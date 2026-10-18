"""CPU-only target selection groundwork. This is explicitly not a GPU success."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('incoming_world',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from calculator import timeline
rows=[]
for rule in ('all','slot:2,4','random:2','top_atk:2'):
 for scenario in ('visible','one_hidden','all_hidden','hidden_taunter','ignore_taunt'):
  if rule=='all' and scenario=='ignore_taunt':continue
  b=v.v.body_for(v.v.NAMES,4,True);b['seed']=12345
  spec=dict(coeff=1,atk=1,target=rule,hits=8,interval=.5)
  if scenario=='ignore_taunt':spec['ignore_taunt']=True
  b['enemy']['patterns']=[dict(id='incoming',kind='attack',until={'time':4},spec=spec)]
  extra={}
  if scenario in ('one_hidden','hidden_taunter','ignore_taunt'):extra[v.v.NAMES[0]]=[v.E('hidden','buff','stealth',1)]
  if scenario=='all_hidden':extra[v.v.NAMES[0]]=[v.E('all hidden','buff','stealth',1,'all_allies')]
  if scenario in ('hidden_taunter','ignore_taunt'):extra[v.v.NAMES[0]]+=[v.E('taunt','buff','taunt',1)]
  chosen=[]
  def trace(frame,event,arg):
   if frame.f_code.co_name!='_attack_targets' or frame.f_globals.get('__name__')!=timeline.__name__:return None
   if event=='return':
    d=frame.f_locals;chosen.append(dict(time=d['t'],selected=list(arg),pool=list(d.get('pool',[])),taunt=list(d.get('taunt',[])),rest=list(d.get('rest',[]))))
   return trace
  previous=sys.gettrace()
  with v.v.t.p.custom_effects(extra):
   try:sys.settrace(trace);cpu=v.a.evaluate(b)
   finally:sys.settrace(previous)
   try:v.a.evaluate({**b,'_compile_gpu_detail':True});gpu_accepted=True;issues=[]
   except v.g.UnsupportedDetail as e:gpu_accepted=False;issues=e.issues
  assert len(chosen)==8 and not gpu_accepted
  if rule=='all':assert all(len(r['selected'])==5 for r in chosen)
  if scenario=='all_hidden' and rule.startswith(('random','top_atk')):assert all(len(r['pool'])==5 for r in chosen)
  if scenario in ('one_hidden','ignore_taunt') and rule.startswith(('random','top_atk')):assert all(v.v.NAMES[0] not in r['pool'] for r in chosen)
  if scenario=='hidden_taunter' and rule!='all':assert all(r['selected'][0]==v.v.NAMES[0] for r in chosen)
  if rule.startswith('slot:') and scenario=='ignore_taunt':assert all(r['selected']==[v.v.NAMES[1],v.v.NAMES[3]] for r in chosen)
  row=dict(rule=rule,scenario=scenario,cpu_total=cpu['total_damage'],targets=chosen,gpu_accepted=False,gpu_issues=issues)
  rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
files=['scripts/audit-incoming-targets.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
(ROOT/'research/detail-incoming-targets-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
