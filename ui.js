
let config, current;
const byId = id => document.getElementById(id);
function node(tag, text, cls){const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;}
function money(cents){return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(cents/100);}
function metric(parent, label, value){const n=node('div','','metric');n.append(node('strong',value),node('span',label));parent.append(n);}
function render(result){
 current=result; const out=byId('result');out.replaceChildren();
 out.append(node('span',result.mode||'deterministic demo','badge'));
 if(result.kind==='repair'){
   out.append(node('h2',result.title),node('p',result.message));
   if(result.estimate){const m=node('div','','metrics');metric(m,'Provisional total',money(result.estimate.total_cents));metric(m,'Approval','Required');out.append(m);for(const line of result.estimate.lines)out.append(node('div',line.label+' — '+money(line.cents),'row'));}
   if(result.proposal_id){const b=node('button','Approve fictional booking');b.onclick=async()=>{b.disabled=true;try{const r=await fetch('/api/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proposal_id:result.proposal_id,approval_token:result.approval_token})});const data=await r.json();if(!r.ok)throw Error(data.detail);out.append(node('p',data.message,'success'));b.remove();}catch(e){out.append(node('p',e.message,'error'));b.disabled=false;}};out.append(b);}
 } else if(result.kind==='gate'){
   out.append(node('h2',result.allowed?'Eligible for review':'Gate blocked'),node('p',result.message));const m=node('div','','metrics');metric(m,'Net return',result.metrics.net_return_pct.toFixed(2)+'%');metric(m,'Maximum drawdown',result.metrics.max_drawdown_pct.toFixed(2)+'%');metric(m,'Completed trades',String(result.metrics.trades));out.append(m);for(const c of result.checks)out.append(node('div',(c.passed?'PASS · ':'BLOCK · ')+c.label,'row'));out.append(node('p','Synthetic series · '+result.bars+' hourly closes · '+result.fee_bps+' bps fee per side. Synthetic results cannot authorize a trading experiment.','muted'));
 } else {
   out.append(node('h2','Ranked results'),node('p',result.message));for(const row of result.items){const card=node('div','','row');card.append(node('h3',row.title),node('p','Score '+row.score.toFixed(1)+'/100 · '+row.reason));if(row.landed_cents!=null)card.append(node('p','Landed cost '+money(row.landed_cents)+' · potential net '+money(row.profit_cents)));if(row.flags.length)card.append(node('p','Review: '+row.flags.join('; '),'error'));out.append(card);}
 }
 const detail=node('details');detail.append(node('summary','Inspect structured output'));detail.append(node('pre',JSON.stringify(result,null,2)));out.append(detail);
}
async function init(){const r=await fetch('/api/config');config=await r.json();byId('title').textContent=config.title;byId('subtitle').textContent=config.subtitle;byId('boundary').textContent=config.boundary;byId('input-label').textContent=config.input_label;for(const option of config.options){const o=node('option',option.label);o.value=option.id;byId('scenario').append(o);}if(config.weight_label){byId('weight-controls').hidden=false;byId('weight-label').textContent=config.weight_label;byId('weight').value=config.default_weight;byId('weight-value').textContent=config.default_weight;byId('weight').oninput=()=>byId('weight-value').textContent=byId('weight').value;}}
byId('run').onclick=async()=>{const b=byId('run');b.disabled=true;byId('events').replaceChildren();byId('result').replaceChildren(node('p','Working…'));try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:byId('scenario').value,weight:Number(byId('weight').value)})});const data=await r.json();if(!r.ok)throw Error(data.detail||'Request failed');if(data.stream_id){await new Promise((resolve,reject)=>{const es=new EventSource('/api/events/'+data.stream_id);es.addEventListener('step',e=>byId('events').append(node('li',JSON.parse(e.data).message)));es.addEventListener('result',e=>{render(JSON.parse(e.data));es.close();resolve();});es.onerror=()=>{es.close();reject(Error('Workflow stream interrupted. Run a new workflow.'));};});}else render(data);}catch(e){byId('result').replaceChildren(node('p',e.message,'error'));}finally{b.disabled=false;}};
init().catch(()=>byId('result').replaceChildren(node('p','Could not load the demo. Check the server.','error')));
