from fastapi.testclient import TestClient
import app

def test_health_and_ui():
    with TestClient(app.app) as client:
        assert client.get('/api/health').json()['synthetic'] is True
        assert client.get('/').status_code == 200
        assert client.get('/ui.js').status_code == 200

def test_invalid_inputs():
    with TestClient(app.app) as client:
        assert client.post('/api/run', json={'scenario': 'unknown'}).status_code == 422
        assert client.post('/api/run', json={'scenario': 'charging', 'weight': -1}).status_code == 422
        assert client.post('/api/run', json={'scenario': 'charging', 'surprise': 'x'}).status_code == 422
def test_estimate_and_missing_information():
    result = app.analyze('charging')
    assert result['estimate']['total_cents'] == 10058
    assert sum(line['cents'] for line in result['estimate']['lines']) == 10058
    assert app.analyze('missing_model')['status'] == 'clarify'
    assert 'estimate' not in app.analyze('missing_model')
    for scenario in ('no_stock', 'unsupported', 'tool_failure'):
        assert app.analyze(scenario)['status'] == 'review'
        assert 'estimate' not in app.analyze(scenario)

def test_approval_is_session_bound_and_single_use():
    with TestClient(app.app) as first, TestClient(app.app) as second:
        result = first.post('/api/run', json={'scenario': 'charging'}).json()
        proposal = result['result']
        action = {k: proposal[k] for k in ('proposal_id', 'approval_token')}
        assert second.post('/api/approve', json=action).status_code == 403
        assert second.get('/api/events/'+result['stream_id']).status_code == 403
        bad = dict(action, approval_token='wrong')
        assert first.post('/api/approve', json=bad).status_code == 403
        assert first.post('/api/approve', json=action).status_code == 200
        assert first.post('/api/approve', json=action).status_code == 409

def test_new_workflow_invalidates_old_proposal_and_expired_session():
    with TestClient(app.app) as client:
        old = client.post('/api/run', json={'scenario':'charging'}).json()['result']
        action = {k: old[k] for k in ('proposal_id','approval_token')}
        client.post('/api/run', json={'scenario':'missing_model'})
        assert client.post('/api/approve', json=action).status_code == 403
        app.sessions[client.cookies['repair_session']]['expires'] = 0
        assert client.post('/api/approve', json=action).status_code == 403

def test_stream_events_and_session_limit():
    with TestClient(app.app) as client:
        result = client.post('/api/run', json={'scenario':'charging'}).json()
        stream = client.get('/api/events/'+result['stream_id'])
        assert 'event: step' in stream.text
        assert 'event: result' in stream.text
        app.sessions[client.cookies['repair_session']]['count'] = 30
        assert client.post('/api/run', json={'scenario':'charging'}).status_code == 429
