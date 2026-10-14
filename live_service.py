"""Public synthetic-intake service. SQLite budgets survive process restarts."""
import asyncio, hashlib, json, os, secrets, sqlite3, time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from typesafe_adapter import judge, compose, MODEL, PRICE_PER_MILLION, api_key

DB=Path(os.environ.get('PORTFOLIO_DEMO_DB',str(Path.home()/'.local/state/portfolio-ai/runtime.db')))
ORIGINS=['https://michaelrizzo2.github.io','http://127.0.0.1:8020','http://localhost:8020']+[f'http://127.0.0.1:{port}' for port in range(8011,8015)]
TTL=900; DAY_CALLS=90; DAY_TOKENS=120000; RESERVE=6000
app=FastAPI(title='Repair desk • typed AI evidence',docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_methods=['GET','POST'],allow_headers=['Content-Type'],max_age=600)
semaphore=asyncio.Semaphore(2)

def connect():
 DB.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 db=sqlite3.connect(DB,timeout=5);db.row_factory=sqlite3.Row
 db.executescript('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, expires REAL, count INTEGER, current TEXT, result TEXT, approved INTEGER); CREATE TABLE IF NOT EXISTS daily (day TEXT PRIMARY KEY, calls INTEGER, tokens INTEGER, sessions INTEGER); CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, day TEXT, status TEXT, latency REAL, input_tokens INTEGER, output_tokens INTEGER, request_hash TEXT);')
 os.chmod(DB,0o600)
 return db

def hashed(value):return hashlib.sha256(value.encode()).hexdigest()
def day():return time.strftime('%Y-%m-%d',time.gmtime())
def daily(db):
 db.execute('INSERT OR IGNORE INTO daily VALUES (?,0,0,0)',(day(),))
 return db.execute('SELECT * FROM daily WHERE day=?',(day(),)).fetchone()
def session(db,token):
 s=db.execute('SELECT * FROM sessions WHERE id=?',(hashed(token),)).fetchone()
 if not s or s['expires']<time.time():raise HTTPException(403,'Session expired. Start a new session.')
 return s
@app.middleware('http')
async def boundary(request:Request,call_next):
 origin=request.headers.get('origin')
 if origin and origin not in ORIGINS:
  from fastapi.responses import JSONResponse
  return JSONResponse({'detail':'Origin not allowed'},status_code=403)
 if request.method=='POST':
  # Consume at most 8 KiB even when Content-Length is omitted or inaccurate.
  body=bytearray()
  async for chunk in request.stream():
   body.extend(chunk)
   if len(body)>8192:
    from fastapi.responses import JSONResponse
    return JSONResponse({'detail':'Request too large'},status_code=413)
  request._body=bytes(body)
 response=await call_next(request)
 response.headers['Cache-Control']='no-store'
 return response

@app.get('/api/health')
def health():
 try:api_key();configured=True
 except RuntimeError:configured=False
 return {'status':'ok','configured':configured,'model':MODEL,'mode':'live typed AI on fictional requests','limits':{'session_runs':5,'session_seconds':TTL,'daily_calls':DAY_CALLS,'daily_input_tokens':DAY_TOKENS},'privacy':'Request text sent to TypeSafe; demo stores only its hash. Use fictional text.'}
@app.post('/api/session')
def new_session():
 token=secrets.token_urlsafe(32)
 with connect() as db:
  db.execute('BEGIN IMMEDIATE');d=daily(db)
  if d['sessions']>=500:raise HTTPException(429,'Daily session capacity reached.')
  db.execute('DELETE FROM sessions WHERE expires < ?',(time.time(),))
  db.execute('INSERT INTO sessions VALUES (?,?,0,NULL,NULL,0)',(hashed(token),time.time()+TTL))
  db.execute('UPDATE daily SET sessions=sessions+1 WHERE day=?',(day(),))
 return {'token':token,'expires_in':TTL}
class Run(BaseModel):
 model_config=ConfigDict(extra='forbid')
 token:str=Field(min_length=20,max_length=100)
 text:str=Field(min_length=10,max_length=600)
@app.post('/api/live/run')
async def run(body:Run):
 if not body.text.strip():raise HTTPException(422,'Enter a fictional repair request.')
 if semaphore.locked():raise HTTPException(429,'Two workflows are already running. Try again shortly.')
 run_id=secrets.token_urlsafe(20);current_day=day()
 async with semaphore:
  with connect() as db:
   db.execute('BEGIN IMMEDIATE');s=session(db,body.token);d=daily(db)
   if s['count']>=5 or d['calls']>=DAY_CALLS or d['tokens']+RESERVE>DAY_TOKENS:raise HTTPException(429,'Demo inference budget reached. Use the offline examples.')
   db.execute('UPDATE daily SET calls=calls+1,tokens=tokens+? WHERE day=?',(RESERVE,current_day))
   db.execute('UPDATE sessions SET count=count+1,current=?,result=NULL,approved=0 WHERE id=?',(run_id,s['id']))
   db.execute('INSERT INTO runs VALUES (?,?,?,0,?,0,?)',(run_id,current_day,'pending',RESERVE,hashed(body.text)))
  started=time.perf_counter()
  try:
   judgment=await judge(body.text);result=compose(judgment)
  except Exception:
   with connect() as db:db.execute('UPDATE runs SET status=?,latency=? WHERE id=?',('provider_error',(time.perf_counter()-started)*1000,run_id))
   raise HTTPException(503,'Live inference failed. No estimate or booking was created. You can select an offline example.')
  latency=(time.perf_counter()-started)*1000
  result['telemetry']={'run_id':run_id,'latency_ms':round(latency,1),'input_tokens':judgment.usage.input_tokens,'output_tokens':judgment.usage.output_tokens,'estimated_api_cost_usd':judgment.usage.input_tokens*PRICE_PER_MILLION/1e6,'price_source':'https://docs.typesafe.ai/models','cost_excludes_hosting':True}
  if result['status']=='approval_required':result.update(proposal_id=run_id,approval_token=secrets.token_urlsafe(24))
  with connect() as db:
   db.execute('BEGIN IMMEDIATE');s=session(db,body.token)
   db.execute('UPDATE daily SET tokens=tokens-?+? WHERE day=?',(RESERVE,judgment.usage.input_tokens,current_day))
   db.execute('UPDATE runs SET status=?,latency=?,input_tokens=?,output_tokens=? WHERE id=?',(result['status'],latency,judgment.usage.input_tokens,judgment.usage.output_tokens,run_id))
   if s['current']!=run_id:raise HTTPException(409,'A newer workflow replaced this result.')
   db.execute('UPDATE sessions SET result=? WHERE id=?',(json.dumps(result),s['id']))
  return result
class Approval(BaseModel):
 model_config=ConfigDict(extra='forbid')
 token:str=Field(min_length=20,max_length=100)
 proposal_id:str=Field(min_length=1,max_length=100)
 approval_token:str=Field(min_length=1,max_length=100)
@app.post('/api/live/approve')
def approve(body:Approval):
 with connect() as db:
  db.execute('BEGIN IMMEDIATE');s=session(db,body.token);r=json.loads(s['result'] or '{}')
  if r.get('status')!='approval_required' or body.proposal_id!=s['current'] or not secrets.compare_digest(body.approval_token,r.get('approval_token','')):raise HTTPException(403,'Approval does not match the current proposal.')
  if s['approved']:raise HTTPException(409,'Proposal already approved.')
  db.execute('UPDATE sessions SET approved=1 WHERE id=?',(s['id'],))
 return {'booking_id':'fictional-'+secrets.token_hex(6),'slot':'Fictional Tuesday, 10:00','message':'Fictional booking approved. No real appointment, payment or message was created.'}
@app.get('/api/metrics')
def metrics():
 with connect() as db:
  rows=db.execute('SELECT status,latency,input_tokens FROM runs WHERE day=?',(day(),)).fetchall();d=daily(db)
 success=[r for r in rows if r['status'] not in ['pending','provider_error']]
 latencies=sorted(r['latency'] for r in success)
 return {'day_utc':day(),'attempts':len(rows),'successful':len(success),'provider_errors':sum(r['status']=='provider_error' for r in rows),'p50_latency_ms':round(latencies[len(latencies)//2],1) if latencies else None,'p95_latency_ms':round(latencies[min(len(latencies)-1,int(len(latencies)*.95))],1) if latencies else None,'reserved_or_used_input_tokens':d['tokens'],'scope':'Public demo only; daily aggregate, includes failed-call reservations.'}
