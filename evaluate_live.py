"""Frozen synthetic benchmark; not customer outcomes or a hiring prediction."""
import asyncio,json,time,hashlib,statistics
from pathlib import Path
from typesafe_adapter import judge,compose,MODEL,PRICE_PER_MILLION
ROOT=Path(__file__).parent

def baseline(text):
 t=text.lower()
 if any(x in t for x in ['swollen','smoke','burning','liquid','sparks','overheat']):return 'review'
 if not any(x in t for x in ['charg','battery','power']):return 'review'
 if 'northstar n14' in t:return 'approval_required'
 if 'meridian m2' in t:return 'review'
 return 'clarify'
async def main():
 cases=json.loads((ROOT/'evaluation-cases.json').read_text())['cases']
 rows=[]
 for case in cases:
  started=time.perf_counter()
  try:
   j=await judge(case['text']);r=compose(j)
   row={**case,'actual':r['status'],'latency_ms':round((time.perf_counter()-started)*1000,2),'usage':j.usage.model_dump(),'judgments':j.answers.model_dump()}
  except Exception as exc:row={**case,'actual':'provider_error','latency_ms':round((time.perf_counter()-started)*1000,2),'error_type':type(exc).__name__}
  row['baseline']=baseline(case['text']);row['correct']=row['actual']==case['expected'];rows.append(row)
  print(case['id'],row['actual'],row['correct'],flush=True)
 evaluated=[r for r in rows if r['split']=='holdout'];lat=sorted(r['latency_ms'] for r in evaluated)
 tokens=sum(r.get('usage',{}).get('input_tokens',0) for r in rows)
 report={'model':MODEL,'dataset_sha256':hashlib.sha256((ROOT/'evaluation-cases.json').read_bytes()).hexdigest(),'method':'Hand-labeled synthetic cases frozen before inference. No tuning after holdout. Single run; small sample, not production/customer evidence. Latency includes HTTPS and model, excludes public gateway. Keyword baseline shares no model calls.','holdout_cases':len(evaluated),'holdout_correct':sum(r['correct'] for r in evaluated),'baseline_correct':sum(r['baseline']==r['expected'] for r in evaluated),'unsafe_approval_cases':sum(r['actual']=='approval_required' and r['expected']!='approval_required' for r in evaluated),'provider_errors':sum(r['actual']=='provider_error' for r in rows),'p50_ms':statistics.median(lat),'p95_ms':lat[min(len(lat)-1,int(len(lat)*.95))],'input_tokens':tokens,'estimated_api_cost_usd':tokens*PRICE_PER_MILLION/1e6,'price_source':'https://docs.typesafe.ai/models','rows':rows}
 (ROOT/'evaluation-results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
if __name__=='__main__':asyncio.run(main())
