"""Named skill-hit and forced-slot activation; semantic witnesses, not per-character tests."""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
shared=load('named_hits_shared','scripts/verify-named-magnitude.py');m=shared.m;v=shared.v;g=shared.g
N=m.N;B=m.B;E=m.E

def independent(device,backend):
 chars=v.characters(N);bs={n:{'atk':1000+i*100,'def':0,'hp':1000000} for i,n in enumerate(N)};rows=[]
 for case in ('nested-frozen-parent','critical-name-isolation','forced-slot-grid'):
  effects=[]
  def add(effect,owner=0):effects.append((effect,N[owner]));return effect
  script=[[0,0,0,i,0,-1,0,0] for i in range(5)];expected=[];queries=[]
  if case=='nested-frozen-parent':
   add(B('no critical','crit_rate',-15,'all_allies'))
   add(E('parent','damage','sequential_damage:3',100,'target',event='on_attack'))
   add(B('hit power','atk_pct',100,event='hit_count:parent:1'))
   add(E('child','damage','damage',10,'target',event='hit_count:parent:1'))
   add(B('parent count','',event='hit_count:parent:1',max_stack=100))
   add(B('second count','',event='hit_count:parent:2',max_stack=100))
   add(B('wrong name','',event='hit_count:other:1',max_stack=100))
   add(E('parent','damage','damage',100,'target',event='on_attack'),1)
   queries=[(.1,7,0,'parent count',3600,3),(.2,7,0,'parent count',10200,6),(.3,7,1,'parent count',10200,6)]
  elif case=='critical-name-isolation':
   add(B('quarter critical','crit_rate',10,'all_allies'))
   add(B('normal-only critical','normal_atk_crit_rate',100,'all_allies'))
   for name,event in [('first','on_attack'),('second','last_bullet')]:
    add(E(name,'damage','sequential_damage:3',100,'target',event=event))
    add(E(name+' critical child','damage','damage',80,'target',event='hit_count:'+name+':1',condition=['trigger_hit_crit']))
    add(B(name+' critical count','',event='hit_count:'+name+':1',condition=['trigger_hit_crit'],max_stack=100))
   queries=[(.1,7,0,'first critical count',3375,0),(.2,14,0,'second critical count',6750,0),(.3,7,0,'first critical count',11025,1),(.4,14,0,'second critical count',15300,1)]
  else:
   e=add(B('slot marker','',event='every:1.0s',max_stack=100));e['source']='스킬1'
   e=add(B('slot power','atk_pct',10,event='every:1.0s',duration=.25));e['source']='스킬1'
   e=add(B('condition marker','',event='every:1.0s',condition=['self_state:gate'],max_stack=100));e['source']='스킬1'
   add(E('force first','instant','force_skill_use',0,event='battle_start',target_skill='스킬1'))['source']='스킬2'
   add(B('gate','',event='battle_start'))['source']='스킬2'
   add(E('force again','instant','force_skill_use',0,event='every:0.6s',max_trigger=1,target_skill='스킬1'))['source']='스킬3'
  program=g.compile_effects(chars,effects)
  if case=='forced-slot-grid':
   for frame in range(64):
    t=frame/60;script.append([t,4,0,0,0,-1,0,0])
    if frame in (6,24,42,63):
     index=(6,24,42,63).index(frame)
     script.append([t,2,103 if index==1 else 0,0,0 if index==1 else program['states']['slot marker'],index,0,0])
   expected=[1,0,2,3]
  else:
   for index,(t,event,who,ref,total,count) in enumerate(queries):
    script += [[t,0,event,who,0,-1,0,0],[t,2,0,0,program['states'][ref],index,0,0]]
   expected=[(total,count) for _,_,_,_,total,count in queries]
  result=g.run(device,[program],script,[[0,0]],[bs],module_backend=backend)
  if case=='forced-slot-grid':actual=[q[37] if i!=1 else q[0] for i,q in enumerate(result['queries'][0])]
  else:actual=[(q[38],q[37]) for q in result['queries'][0]]
  passed=actual==expected;row=dict(name='independent-'+case,passed=passed,expected=expected,actual=actual,workspace_bytes=result['workspace_bytes']);rows.append(row);print(json.dumps(row),flush=True)
 return rows

def fixtures():
 for variant in ('nested-parent','critical-forces-slot','reduced-threshold','down-revive-fractions'):
  b=m.body(2);extra={n:[] for n in N}
  extra[N[0]]=[B('quarter critical','crit_rate',10),E('parent','damage','sequential_damage:3',100,'target',event='every:0.2s')]
  if variant=='nested-parent':
   extra[N[0]] += [B('listener power','atk_pct',7,event='hit_count:parent:1',max_stack=100),E('child','damage','sequential_damage:2',40,'target',event='hit_count:parent:2'),B('critical child','atk_dmg_pct',3,event='hit_count:child:1',condition=['trigger_hit_crit'],max_stack=100)]
  elif variant=='critical-forces-slot':
   extra[N[0]][0]['source']='스킬3';extra[N[0]][1]['source']='스킬3'
   extra[N[0]] += [E('force on critical','instant','force_skill_use',0,event='hit_count:parent:1',condition=['trigger_hit_crit'],target_skill='스킬1'),B('forced critical witness','atk_pct',11,event='every:1.1s',condition=['trigger_hit_crit'],max_stack=100)]
   extra[N[0]][-2]['source']='스킬2';extra[N[0]][-1]['source']='스킬1'
  elif variant=='reduced-threshold':
   extra[N[0]] += [B('third-hit listener','atk_pct',3,event='hit_count:parent:3',max_stack=100),B('reduce named threshold','trigger_count_reduce',2,event='every:0.3s',max_trigger=1,target_effect='third-hit listener')]
  else:
   b['enemy']['patterns']=[m.s.lethal('slot:1',at=.3)]
   extra[N[0]] += [B('critical witness','atk_pct',5,event='hit_count:parent:1',condition=['trigger_hit_crit'],max_stack=100)]
   extra[N[1]] += [E('revive source','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.5s',max_trigger=1)]
  yield 'named-hits-'+variant,b,extra
 for subject,favorite,reordered in [('이브',0,False),('이브',0,True),('율리아',1,False),('율리아',2,True)]:
  names=[subject,'리타','크라운','앨리스','모더니아']
  if reordered:names=[names[2],subject,names[1],names[4],names[3]]
  b=m.body(35,True,names);b['burst_gauge_mode']='fixed';b['profile']['chars'][subject]['favorite_stage']=favorite
  if subject=='이브':b['enemy']['code']='전격'
  yield 'raw-named-hits-'+subject+'-fav'+str(favorite)+('-reordered' if reordered else ''),b,{}

def compare(device,name,body,extra,backend):
 from unittest.mock import patch
 from calculator.buff_manager import BuffManager
 notices=set();active_seen=set();watched=set();damage_followups=set();buff_followups=set()
 original_notify=BuffManager.notify;original_gpu=g.evaluate_full
 def inspect_program(device,compiled,*args,**kwargs):
  program=compiled['program'];labels={index:label for label,index in program['states'].items()}
  for row in program['effects']:
   descriptors=[row[g.TD+i*g.TS:g.TD+(i+1)*g.TS] for i in range(int(row[144]))]
   named=[d for d in descriptors if d[0]==49]
   if not named:continue
   owner=program['chars'][int(row[0])]['name'];effect_name=labels[int(row[3])]
   watched.update((owner,'hit_count:'+labels[int(d[3])]) for d in named)
   if row[1]==3:damage_followups.add((owner,'hit_count:'+effect_name))
   elif row[258]==0:buff_followups.add((owner,effect_name))
  return original_gpu(device,compiled,*args,**kwargs)
 def observe(self,event,t,caster,*args,**kwargs):
  result=original_notify(self,event,t,caster,*args,**kwargs)
  if event.startswith('hit_count:'):
   notices.add((caster,event));active_seen.update((ab.caster,ab.effect.get('name')) for ab in self._active)
  return result
 with patch.object(g,'evaluate_full',inspect_program),patch.object(BuffManager,'notify',observe):row=m.compare(device,name,body,extra,backend)
 row['checks']['named_listener_exercised']=bool(watched&notices)
 if damage_followups or buff_followups:
  row['checks']['named_followup_exercised']=bool(damage_followups&notices or buff_followups&active_seen)
 row['passed']=all(row['checks'].values());row['CPU_named_event_identities']=len(notices)
 print(json.dumps(dict(name=name,passed=row['passed'],failed=[k for k,v in row['checks'].items() if not v])),flush=True)
 return row

def verify(backend):
 from gpu_selector import Cuda
 from verification_session import VerificationSession
 session=VerificationSession();session.device=Cuda();rows=[]
 try:
  rows+=independent(session.device,backend)
  planned=list(fixtures())
  if backend=='ptx':planned=[c for c in planned if c[0] in ('named-hits-critical-forces-slot','raw-named-hits-율리아-fav2-reordered')]
  if all(r['passed'] for r in rows):
   for name,b,x in planned:
    from types import SimpleNamespace
    row=session.compare(SimpleNamespace(compare=compare),name,b,x,backend);rows.append(row)
    if not row['passed']:break
 finally:session.close()
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx'],default='native');a=p.parse_args()
 files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'research/upstream/nikke-calc-master/calculator').glob('*.py'))+[ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json']+[ROOT/'app'/n for n in ('detail_effects.cu',*(['detail_effects-sm86.cubin','detail_effects-sm86.json'] if a.backend=='native' else ['detail_effects.ptx','detail_effects-build.json']))]
 hashes={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
 rows=verify(a.backend);stable=all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in hashes.items());planned=11 if a.backend=='native' else 5
 report=dict(passed=stable and len(rows)==planned and all(r['passed'] for r in rows),backend=a.backend,cases=rows,source_stable=stable,source_sha256=hashes,game_rules_verified=False,cpu_traces_used_as_gpu_input=False)
 (ROOT/f'research/named-hits-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
