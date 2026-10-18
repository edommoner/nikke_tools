"""GPU shield quantities from profiles/effects/authored operations, not CPU states."""
import copy,hashlib,importlib.util,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('shield_lifecycle',ROOT/'scripts/audit-shield-lifecycle.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import run
from gpu_selector import Cuda

def execute(device,ref,backend):
 body=copy.deepcopy(ref['input']);effects=copy.deepcopy(ref['authored_effects']);names=body['squad'];ops=ref['authored_operations'];aux={}
 # Only authored named-removal and stack operations become inactive definitions.
 for i,(op,who,value,pierce) in enumerate(ops):
  if op=='remove':eff=v.E('authored operation '+str(i),'instant','remove_named_buff',0,names[who],event='inactive',target_effect='strip shield',remove_scope=value)
  elif op=='addstack':eff=v.E('authored operation '+str(i),'instant','buff_stack_add',value,'self',event='inactive',target_effect='stack shield')
  else:continue
  effects.setdefault(names[who],[]).append(eff);aux[i]=eff['name']
 with v.v.c.p.custom_effects(effects):compiled=v.v.c.a.evaluate({**body,'_compile_gpu_detail':True})
 program=compiled['program'];states=program['states'];script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[0,0,5,i,0,-1,0,0] for i in range(5)]
 t=0.0
 while t<=body['duration']:script.append([t,4,0,0,0,-1,0,0]);t+=1/60
 script.append([body['duration'],5,0,0,0,-1,0,0]);queries=[]
 shield_names=list(dict.fromkeys(e['name'] for es in ref['authored_effects'].values() for e in es if e.get('stat') in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct','next_shield_hp_pct')))
 def query(t,ev,arg,tag):
  index=len(queries);script.append([t,2,ev,0,arg,index,0,0]);queries.append(tag)
 def snapshot(t,step):
  query(t,111,-1,(step,'summary'))
  for name in shield_names:query(t,111,states[name],(step,name))
  if 'ended probe' in states:query(t,0,states['ended probe'],(step,'probe'))
 snapshot(body['duration'],-1);t=body['duration']+.1
 for i,(op,who,value,pierce) in enumerate(ops):
  if op=='tick':t=float(value);script.append([t,6,2,0,0,-1,0,0])
  elif op in ('absorb','heal'):script.append([t,6,0 if op=='absorb' else 1,who,0,-1,float(value),int(pierce)])
  else:
   stateid=states[aux[i]];row=next(j for j,e in enumerate(program['effects']) if e[3]==stateid and e[1]!=-1)
   script.append([t,0,28,who,row,-1,0,0])
  snapshot(t,i);t+=.1
 for page in range(14):query(t-.1,110,page,('rng',page))
 result=run(device,[program],script,[compiled['enemy']],[compiled['base_stats']],module_backend=backend,seeds=[body.get('seed',0)])
 outputs=result['queries'][0];errors=[];final_rng=[]
 for tag,gpu in zip(queries,outputs):
  step,name=tag
  if step=='rng':final_rng.extend(int(x) for x in gpu);continue
  expected=ref['initial'] if step==-1 else ref['steps'][step]['after']
  if name=='probe':
   if gpu[37]!=(expected['ended_probe'][0] if expected['ended_probe'] else 0):errors.append([step,'end callback stack',gpu[37],expected['ended_probe']])
   continue
  entries=expected['entries'] if name=='summary' else [e for e in expected['entries'] if e['name']==name]
  if name=='summary' and step>=0:
   returned=ref['steps'][step]['returned']
   if isinstance(returned,(float,int)) and not math.isclose(gpu[0],returned,rel_tol=1e-12,abs_tol=1e-6):errors.append([step,'returned',gpu[0],returned])
  for who,n in enumerate(names):
   amount=sum(e['shield'].get(n,0) for e in entries);capacity=sum(e['capacity'].get(n,0) for e in entries);has=any(e['shield'].get(n,0)>0 for e in entries)
   for field,x,y in [('amount',gpu[1+who],amount),('capacity',gpu[6+who],capacity),('has_shield',gpu[11+who],int(has))]:
    if not math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-6):errors.append([step,name,n,field,x,y])
  mask=0;present=0
  for e in entries:
   if e['targets'] is None:mask=-1
   elif mask>=0:
    for n in e['targets']:mask|=1<<names.index(n)
   for n in e['capacity']:present|=1<<names.index(n)
  for field,x,y in [('entries',gpu[16],len(entries)),('targets',gpu[17],mask),('stacks',gpu[18],sum(e['stack'] for e in entries)),('present',gpu[19],present)]:
   if x!=y:errors.append([step,name,field,x,y])
 checks=dict(shield_snapshots=not errors,final_random_state=final_rng[:625]==ref['final_random_state'],initial_battle_damage=sum(result['totals'][0])==ref['cpu_total'])
 return dict(name=ref['name'],backend=backend,passed=all(checks.values()),checks=checks,errors=errors[:12],cpu_total=ref['cpu_total'],gpu_total=sum(result['totals'][0]),workspace_bytes=result['workspace_bytes'])

def verify(device,backend):
 refs=json.loads((ROOT/'research/detail-shield-lifecycle-cpu-references.json').read_text(encoding='utf-8'));rows=[]
 for ref in refs['cases']:
  try:row=execute(device,ref,backend)
  except Exception as e:row=dict(name=ref['name'],backend=backend,passed=False,error=str(e))
  rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
 return rows

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx','both'],default='both');p.add_argument('--output',default='research/detail-shield-lifecycle-verification.json');args=p.parse_args();device=Cuda()
 try:rows=sum((verify(device,b) for b in (('native','ptx') if args.backend=='both' else (args.backend,))),[])
 finally:device.close()
 files=['scripts/verify-shield-lifecycle-detail.py','scripts/audit-shield-lifecycle.py','research/detail-shield-lifecycle-cpu-references.json','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(x['passed'] for x in rows),scope='Authored shield subsystem operations following a complete initial five-member battle. Incoming boss combat integration is not covered.',cpu_trace_used_as_gpu_input=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
