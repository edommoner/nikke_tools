"""CPU reference for incoming targeting across live buff/death transitions.

Read-only call/return observation records the separate boss PRNG. These traces
are an oracle for the next port, never authored input to the GPU simulation.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('target_transitions',ROOT/'scripts/verify-boss-buffs-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator import timeline
NAMES=v.v.NAMES

def buff(name,stat,target='self',**kw):return v.E(name,'buff',stat,1,target,**kw)

fixtures=[
 ('hidden-expires','random:2',{NAMES[0]:[buff('short cloak','stealth',duration=.6)]},False),
 ('all-hidden-fallback-then-single-hidden','random:2',{NAMES[0]:[buff('team cloak','stealth','all_allies',duration=.6),buff('long cloak','stealth',duration=1.2)]},False),
 ('periodic-hidden-taunt','random:2',{NAMES[0]:[buff('cloak','stealth'),buff('periodic taunt','taunt',event='every:0.4s',duration=.2)]},False),
 ('enemy-target-taunt','top_atk:2',{NAMES[0]:[buff('cloak','stealth'),buff('enemy taunt','taunt','target',duration=.6)]},False),
 ('all-allies-taunt-first-live-recipient','slot:2,4',{NAMES[0]:[buff('team taunt','taunt','all_allies',duration=.6)]},False),
 ('fallen-member-excluded','random:2',{},True),
]
rows=[]
for name,rule,extra,lethal in fixtures:
 body=v.v.body_for(NAMES,2,False);body['seed']=12345
 shots=dict(id='selection',kind='attack',delay=.2,until={'time':1.6},spec=dict(coeff=1,atk=1,target=rule,hits=7,interval=.2))
 body['enemy']['patterns']=[shots]
 if lethal:body['enemy']['patterns'].insert(0,dict(id='kill',kind='attack',delay=.1,until={'time':.05},spec=dict(coeff=100,atk=100000000,target='slot:1')))
 calls=[];pending={}
 def trace(frame,event,arg):
  if frame.f_code.co_name!='_attack_targets' or frame.f_globals.get('__name__')!=timeline.__name__:return None
  if event=='call':pending[id(frame)]=list(frame.f_locals['boss_rng'].getstate()[1])
  elif event=='return':
   d=frame.f_locals
   calls.append(dict(time=d['t'],rule=d['spec'].rule,selected=list(arg),alive=list(d['alive']),pool=list(d.get('pool',[])),taunt=list(d.get('taunt',[])),boss_rng_before=pending.pop(id(frame)),boss_rng_after=list(d['boss_rng'].getstate()[1])))
  return trace
 previous=sys.gettrace()
 with v.v.t.p.custom_effects(extra):
  try:sys.settrace(trace);cpu=v.a.evaluate(body)
  finally:sys.settrace(previous)
  try:v.a.evaluate({**body,'_compile_gpu_detail':True});accepted=True;issues=[]
  except v.g.UnsupportedDetail as e:accepted=False;issues=e.issues
 assert not accepted,name
 chosen=[c for c in calls if c['rule'] in ('random','top_atk')] if lethal else calls
 assert len(chosen)==7,(name,len(chosen))
 if name=='hidden-expires':
  assert NAMES[0] not in chosen[0]['pool'] and NAMES[0] in chosen[-1]['pool']
 if name=='all-hidden-fallback-then-single-hidden':assert len(chosen[0]['pool'])==5 and any(len(c['pool'])==4 for c in chosen) and len(chosen[-1]['pool'])==5
 if name=='periodic-hidden-taunt':assert any(c['taunt'] for c in chosen) and any(not c['taunt'] for c in chosen)
 if name=='enemy-target-taunt':assert chosen[0]['taunt']==[NAMES[0]] and chosen[-1]['taunt']==[]
 if name=='all-allies-taunt-first-live-recipient':assert chosen[0]['taunt']==[NAMES[0]] and chosen[-1]['taunt']==[]
 if lethal:assert all(NAMES[0] not in c['alive'] and NAMES[0] not in c['selected'] for c in chosen)
 assert all((c['boss_rng_before']!=c['boss_rng_after'])==(c['rule']=='random') for c in chosen)
 rows.append(dict(name=name,total=cpu['total_damage'],calls=calls,gpu_accepted=False,gpu_issues=issues))
 print(json.dumps(dict(name=name,calls=len(calls),cpu_reference_verified=True,gpu_implemented=False)),flush=True)
files=['scripts/audit-incoming-target-transitions.py','scripts/verify-boss-buffs-detail.py','scripts/verify-boss-clock-detail.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
(ROOT/'research/detail-incoming-target-transitions-cpu-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
