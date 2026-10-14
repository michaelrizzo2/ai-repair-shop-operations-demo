CONFIG = {'input_label': 'Fictional repair request', 'boundary': 'Preset synthetic requests only. Estimates are provisional. Approval creates a fictional booking in your isolated 15-minute session.', 'options': [{'id': 'charging', 'label': 'Known model · charging issue'}, {'id': 'missing_model', 'label': 'Missing model · clarification needed'}, {'id': 'no_stock', 'label': 'Compatible part unavailable'}, {'id': 'unsupported', 'label': 'Unsupported account request'}, {'id': 'tool_failure', 'label': 'Simulated inventory failure'}], 'title': 'Repair desk', 'subtitle': 'From a repair request to a reviewed next step.'}
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).parent
app = FastAPI(title=CONFIG['title'])

class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scenario: str = Field(min_length=1, max_length=60)
    weight: int = Field(default=50, ge=0, le=100)

@app.get('/')
def index():
    return FileResponse(ROOT / 'ui.html')

@app.get('/styles.css')
def styles():
    return FileResponse(ROOT / 'styles.css', media_type='text/css')

@app.get('/ui.js')
def script():
    return FileResponse(ROOT / 'ui.js', media_type='text/javascript')

@app.get('/api/health')
def health():
    return {'status': 'ok', 'mode': 'deterministic', 'synthetic': True}

@app.get('/api/config')
def config():
    return CONFIG
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
import asyncio
import json
import secrets
import time
from threading import Lock
from typing import Literal
from fastapi import Request, Response
from fastapi.responses import StreamingResponse

SCENARIOS = {
    'charging': {'text': 'My Northstar N14 laptop will not charge. Could you estimate a repair?', 'model': 'Northstar N14', 'symptom': 'charging'},
    'missing_model': {'text': 'My laptop will not charge. Please book a repair.', 'model': None, 'symptom': 'charging'},
    'no_stock': {'text': 'My Meridian M2 laptop will not charge.', 'model': 'Meridian M2', 'symptom': 'charging'},
    'unsupported': {'text': 'Please recover my account password.', 'model': None, 'symptom': 'account'},
    'tool_failure': {'text': 'My Northstar N14 laptop will not charge.', 'model': 'Northstar N14', 'symptom': 'charging', 'tool_failure': True},
}
INVENTORY = {'Northstar N14': {'part': 'Compatible diagnostic charging kit', 'price_cents': 4900, 'stock': 3}, 'Meridian M2': {'part': 'M2 charging kit', 'price_cents': 6900, 'stock': 0}}
SLOTS = ['Fictional Tuesday, 10:00', 'Fictional Wednesday, 14:00']
sessions = {}
lock = Lock()
TTL = 900

def analyze(scenario):
    if scenario not in SCENARIOS:
        raise ValueError('Unknown scenario')
    intake = SCENARIOS[scenario]
    base = {'kind': 'repair', 'mode': 'deterministic', 'synthetic': True, 'intake': intake, 'events': ['Validated preset synthetic request.']}
    if intake['symptom'] != 'charging':
        return dict(base, title='Human review', message='Account recovery is outside this demo. No account tools are connected.', status='review')
    if not intake['model']:
        return dict(base, title='More information needed', message='Please provide the device model before we choose a compatible part or estimate.', status='clarify')
    if intake.get('tool_failure'):
        return dict(base, title='Inventory unavailable', message='The simulated inventory tool failed. No estimate or booking was created.', status='review')
    part = INVENTORY.get(intake['model'])
    base['events'].append('Looked up compatible inventory using the device model.')
    if not part or part['stock'] <= 0:
        return dict(base, title='Part unavailable', message='No compatible part is available in synthetic stock. Send to a technician for review.', status='review')
    lines = [{'label': part['part'], 'cents': part['price_cents']}, {'label': 'Diagnostic labor', 'cents': 4500}]
    subtotal = sum(line['cents'] for line in lines)
    tax = (subtotal * 7 + 50) // 100
    lines.append({'label': 'Illustrative tax (7%, demo assumption)', 'cents': tax})
    base['events'].extend(['Calculated a provisional estimate in integer cents.', 'Retrieved fictional appointment slots.', 'Prepared a response; approval is required before a simulated booking.'])
    return dict(base, title='Provisional estimate ready', status='approval_required', estimate={'lines': lines, 'total_cents': subtotal + tax, 'currency': 'USD'}, slots=SLOTS, message='We can inspect your Northstar N14. This is a provisional estimate, not a confirmed diagnosis. Approve a fictional booking for the first displayed slot.')

def cleanup():
    now = time.monotonic()
    for session_id in list(sessions):
        if sessions[session_id]['expires'] <= now:
            del sessions[session_id]

def get_session(request):
    cleanup()
    sid = request.cookies.get('repair_session')
    if not sid or sid not in sessions:
        raise HTTPException(403, 'Session missing or expired. Run a new workflow.')
    return sessions[sid]

@app.post('/api/run')
def run(body: RunRequest, request: Request, response: Response):
    try:
        result = analyze(body.scenario)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    with lock:
        cleanup()
        sid = request.cookies.get('repair_session')
        if sid not in sessions:
            if len(sessions) >= 500:
                raise HTTPException(429, 'Demo session capacity reached.')
            sid = secrets.token_urlsafe(32)
            sessions[sid] = {'expires': time.monotonic() + TTL, 'count': 0}
        session = sessions[sid]
        if session['count'] >= 30:
            raise HTTPException(429, 'Session workflow limit reached.')
        session['count'] += 1
        stream_id = secrets.token_urlsafe(24)
        session['stream_id'] = stream_id
        session['approved'] = False
        if result['status'] == 'approval_required':
            result.update(proposal_id=secrets.token_urlsafe(24), approval_token=secrets.token_urlsafe(32))
        session['result'] = result
        response.set_cookie('repair_session', sid, httponly=True, samesite='strict', secure=request.url.scheme == 'https', max_age=TTL)
    return {'stream_id': stream_id, 'result': result}

@app.get('/api/events/{stream_id}')
def events(stream_id: str, request: Request):
    with lock:
        session = get_session(request)
        if session['stream_id'] != stream_id:
            raise HTTPException(404, 'Workflow not found in this session.')
        result = dict(session['result'])
    async def stream():
        # Replay completed, truthful workflow events for inspectable UI presentation.
        # The deterministic computation occurs in /api/run, not during this replay.
        for message in result['events']:
            yield 'event: step\ndata: ' + json.dumps({'message': message}) + '\n\n'
            await asyncio.sleep(0.08)
        yield 'event: result\ndata: ' + json.dumps(result) + '\n\n'
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})

class Approval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    proposal_id: str = Field(min_length=1, max_length=100)
    approval_token: str = Field(min_length=1, max_length=100)

@app.post('/api/approve')
def approve(body: Approval, request: Request):
    with lock:
        session = get_session(request)
        result = session['result']
        if result['status'] != 'approval_required' or body.proposal_id != result.get('proposal_id') or not secrets.compare_digest(body.approval_token, result.get('approval_token', '')):
            raise HTTPException(403, 'Approval does not match the current proposal.')
        if session['approved']:
            raise HTTPException(409, 'This proposal was already approved.')
        session['approved'] = True
        return {'booking_id': 'fictional-' + secrets.token_hex(6), 'slot': result['slots'][0], 'message': 'Fictional booking approved. No real appointment, message or payment was created.'}

# Explicit public evidence assets; never expose arbitrary project paths.
@app.get('/{asset}')
def evidence_asset(asset: str):
    if asset not in ('demo-engine.js','jobs-data.json','eth-history.json','evaluation-results.json'):
        raise HTTPException(404,'Asset not found')
    return FileResponse(ROOT / asset)
