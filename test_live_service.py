import pytest
from fastapi.testclient import TestClient
import live_service as service
from typesafe_adapter import Judgment,compose

def judgment(route='charging',model='northstar',hazard=0,missing=0):
 from typesafe_adapter import QUESTIONS
 def choice(key,value):return {'type':'choice','choice':value,'probabilities':{k:float(k==value) for k in QUESTIONS[key]['criteria']},'confidence':1}
 return Judgment.model_validate({'model':'jev-1.13.0','answers':{'route':choice('route',route),'model':choice('model',model),'hazard':{'type':'noul','noul':hazard},'missing_model':{'type':'noul','noul':missing}},'usage':{'input_tokens':600,'output_tokens':60}})
@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(service,'DB',tmp_path/'runtime.db')
 async def fake(text):return judgment()
 monkeypatch.setattr(service,'judge',fake)
 with TestClient(service.app) as c:yield c

def execute(c,token=None):
 token=token or c.post('/api/session').json()['token']
 r=c.post('/api/live/run',json={'token':token,'text':'My fictional Northstar N14 will not charge.'})
 return token,r

def approve(c,t,r):return c.post('/api/live/approve',json={'token':t,'proposal_id':r['proposal_id'],'approval_token':r['approval_token']})
def test_single_use_session_and_stale_proposal(client):
 t,response=execute(client);assert response.status_code==200;r=response.json()
 other=client.post('/api/session').json()['token']
 assert approve(client,other,r).status_code==403
 assert approve(client,t,r).status_code==200
 assert approve(client,t,r).status_code==409
 _,new=execute(client,t);assert new.status_code==200
 assert approve(client,t,r).status_code==403
 assert approve(client,t,new.json()).status_code==200

def test_quota_survives_client_restart_and_no_raw_text(client):
 t,_=execute(client)
 for _ in range(4):assert execute(client,t)[1].status_code==200
 assert execute(client,t)[1].status_code==429
 with service.connect() as db:
  assert db.execute('SELECT tokens FROM daily').fetchone()[0]==3000
 assert b'will not charge' not in service.DB.read_bytes()

def test_provider_failure_never_estimates(client,monkeypatch):
 async def fail(text):raise RuntimeError('secret must never escape')
 monkeypatch.setattr(service,'judge',fail)
 _,r=execute(client);assert r.status_code==503 and 'secret' not in r.text
 assert client.get('/api/metrics').json()['provider_errors']==1

def test_origin_body_and_expiry(client):
 assert client.post('/api/session',headers={'Origin':'https://evil.example'}).status_code==403
 assert client.post('/api/live/run',content='x'*8193).status_code==413
 t,r=execute(client)
 with service.connect() as db:db.execute('UPDATE sessions SET expires=0')
 assert approve(client,t,r.json()).status_code==403

def test_hazards_uncertainty_and_stock():
 assert compose(judgment(hazard=.7))['status']=='review'
 assert compose(judgment(model='other_or_missing',missing=1))['status']=='clarify'
 assert compose(judgment(model='meridian'))['status']=='review'
 assert compose(judgment(route='account'))['status']=='review'
 assert compose(judgment())['status']=='approval_required'

def test_invalid_provider_contract():
 d=judgment().model_dump();d['answers']['route']['probabilities']['charging']=.5
 with pytest.raises(ValueError):Judgment.model_validate(d)
 d=judgment().model_dump();d['usage']['input_tokens']=100000
 with pytest.raises(ValueError):Judgment.model_validate(d)

def test_global_limits_and_failed_reservation(client,monkeypatch):
 monkeypatch.setattr(service,'DAY_TOKENS',6000)
 async def fail(text):raise RuntimeError('provider down')
 monkeypatch.setattr(service,'judge',fail)
 assert execute(client)[1].status_code==503
 # A fresh anonymous session cannot evade the global token budget.
 assert execute(client)[1].status_code==429
 with service.connect() as db:assert db.execute('SELECT tokens FROM daily').fetchone()[0]==6000

def test_daily_call_limit_applies_across_sessions(client,monkeypatch):
 monkeypatch.setattr(service,'DAY_CALLS',1)
 assert execute(client)[1].status_code==200
 assert execute(client)[1].status_code==429
