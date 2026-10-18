"""Damage accumulation: independent quantities and one shared resource-frame oracle."""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
shared=load('accum_shared','scripts/verify-named-magnitude.py');m=shared.m;v=shared.v;g=shared.g
from resource_frame_capture import FrameCapture
from calculator.buff_manager import BuffManager
N=m.N;B=m.B;E=m.E;STATS=('dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct')

def independent(device,backend):
 chars=v.characters(N);bs={n:{'atk':1000+i*100,'def':0,'hp':1000000} for i,n in enumerate(N)};rows=[]
 for case in ('scoped-rates-fixed-caps','absent-versus-zero-rate','release-and-fresh-lifetime','all-full-before-callbacks'):
  effects=[]
  def add(effect,owner=0):effects.append((effect,N[owner]));return effect
  start=[[0,0,0,i,0,-1,0,0] for i in range(5)]
  if case=='scoped-rates-fixed-caps':
   add(B('own','dmg_accum_dealt_atk_pct',100,'target'))
   add(B('team','dmg_accum_received_atk_pct',50,'target'),1)
   add(B('base rate','dmg_accum_rate_pct',50,'target'))
   add(B('own rate','dmg_accum_rate_pct',25,target_effect='own'))
   add(B('team rate','dmg_accum_rate_pct',50,target_effect='team'),1)
   add(B('later ATK','atk_pct',100,'all_allies',event='on_attack'))
   program=g.compile_effects(chars,effects);script=start+[[.1,7,2,2,0,-1,200,0],[.1,2,124,0,-1,0,0,0],[.15,0,7,0,0,-1,0,0],[.2,7,2,0,0,-1,400,0],[.2,2,124,0,-1,1,0,0],[.3,7,2,0,0,-1,1000,0],[.3,2,124,0,-1,2,0,0]]
   result=g.run(device,[program],script,[[0,0]],[bs],module_backend=backend)
   actual=[(r[1],r[2],r[6],r[7],r[11],r[12]) for r in result['queries'][0]]
   expected=[(0,300,1000,550,0,0),(300,550,1000,550,0,1),(1000,550,1000,550,1,1)]
  elif case=='absent-versus-zero-rate':
   add(B('own','dmg_accum_dealt_atk_pct',100,'target'));add(B('team','dmg_accum_received_atk_pct',100,'target'),1)
   missing=add(B('missing rate','dmg_accum_rate_pct',1));missing.pop('fixed_value',None);missing.pop('values',None)
   add(B('explicit zero','dmg_accum_rate_pct',0),1)
   program=g.compile_effects(chars,effects);script=start+[[.1,7,2,0,0,-1,200,0],[.1,2,124,0,-1,0,0,0]]
   result=g.run(device,[program],script,[[0,0]],[bs],module_backend=backend);actual=[tuple(result['queries'][0][0][1:3])];expected=[(200,0)]
  elif case=='release-and-fresh-lifetime':
   add(B('pool','dmg_accum_received_atk_pct',200,'target',event='on_attack',duration=.5));add(B('split boost','split_dmg_pct',25))
   add(E('release','damage','accum_split_damage',0,'target',event='event:state_end:pool',target_effect='pool'))
   program=g.compile_effects(chars,effects);actual=[];expected=[(376,0),(0,0)]
   for refresh in (False,True):
    script=start+[[0,0,7,0,0,-1,0,0],[.1,7,2,1,0,-1,301,0]]
    if refresh:script.append([.2,0,7,0,0,-1,0,0])
    script += [[.8,1,0,0,0,-1,0,0],[.8,5,0,0,0,-1,0,0],[.8,2,0,0,-1,0,0,0],[.8,2,124,0,-1,1,0,0]]
    result=g.run(device,[program],script,[[999999,0]],[bs],module_backend=backend);actual.append((result['queries'][0][0][38],result['queries'][0][1][17]))
  else:
   add(B('first','dmg_accum_dealt_atk_pct',100,'target'));add(B('second','dmg_accum_received_atk_pct',100,'target'),1)
   add(E('remove other','instant','remove_named_buff',0,event='event:accum_full:first',target_effect='second'))
   add(E('release first','damage','accum_split_damage',0,'target',event='event:accum_full:first',target_effect='first'))
   add(E('release second','damage','accum_split_damage',0,'target',event='event:accum_full:second',target_effect='second'),1)
   program=g.compile_effects(chars,effects);script=start+[[.1,7,2,0,0,-1,2000,0],[.1,2,0,0,-1,0,0,0]]
   result=g.run(device,[program],script,[[0,0]],[bs],module_backend=backend);actual=[tuple(result['totals'][0][:2])];expected=[(3000,1100)]
  row=dict(name='independent-'+case,passed=actual==expected,expected=expected,actual=actual,workspace_bytes=result['workspace_bytes']);rows.append(row);print(json.dumps(row),flush=True)
 return rows

def project(manager,t,capture):
 program=capture.program;labels={i:label for label,i in program['states'].items()};keys=[-1]+sorted({int(r[3]) for r in program['effects'] if r[1]==0 and r[2] in (81,82)})
 names=[c['name'] for c in program['chars']];resident=[a for a in manager._active if a.effect.get('stat') in STATS];rows=[]
 for key in keys:
  chosen=[a for a in resident if key<0 or a.effect.get('name','')==labels[key]]
  archived=sum(manager._accum_last.values()) if key<0 else manager._accum_last.get(labels[key],0)
  rows.append(dict(time=t,key=key,current={n:sum(a.accum for a in chosen if a.caster==n) for n in names},capacity={n:sum(a.accum_cap for a in chosen if a.caster==n) for n in names},done={n:sum(a.accum_done for a in chosen if a.caster==n) for n in names},carriers=len(chosen),archived=archived))
 return rows

def compare(device,name,body,extra,backend):
 body={**body,'_debug_damage_accum_frames':True};full_events=[];original=BuffManager.notify
 def observe(self,event,t,caster,*args,**kwargs):
  if event.startswith('event:accum_full:'):full_events.append((t,event,caster))
  return original(self,event,t,caster,*args,**kwargs)
 with FrameCapture(g,project) as capture,patch.object(BuffManager,'notify',observe):row=m.compare(device,name,body,extra,backend)
 expected=capture.samples+capture.final_samples;actual=capture.gpu.get('_damage_accum_frames')
 row['checks']['damage_accumulation_frames']=m.s.v.close(expected,actual)
 row['checks']['positive_accumulation_control']=bool(full_events) or any(any(value>0 for value in f['current'].values()) for f in expected)
 row['passed']=all(row['checks'].values());row['accum_frame_rows']=len(expected);row['CPU_full_events']=len(full_events)
 if not row['checks']['damage_accumulation_frames']:row['difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(expected,actual or [])) if not m.s.v.close(c,x)),dict(cpu_rows=len(expected),gpu_rows=len(actual or [])))
 print(json.dumps(dict(name=name,passed=row['passed'],failed=[k for k,v in row['checks'].items() if not v])),flush=True);return row

def fixtures():
 for case in ('scoped-caps','live-rate-fixed-cap','all-full-removal','lifesteal-before-rate'):
  b=m.body(3);x={n:[] for n in N}
  if case=='scoped-caps':
   x[N[0]]=[B('dealt','dmg_accum_dealt_atk_pct',1000,'target',duration=1.3),B('base rate','dmg_accum_rate_pct',50,'target'),B('dealt rate','dmg_accum_rate_pct',30,target_effect='dealt'),E('dealt release','damage','accum_split_damage',0,'target',event='event:state_end:dealt',target_effect='dealt')]
   x[N[1]]=[B('received','dmg_accum_received_atk_pct',1000,'target',duration=1.5),E('received release','damage','accum_split_damage',0,'target',event='event:state_end:received',target_effect='received')]
  elif case=='live-rate-fixed-cap':
   x[N[0]]=[B('pool','dmg_accum_dealt_atk_pct',500,'target',duration=2.2),B('base rate','dmg_accum_rate_pct',50,'target'),B('late rate','dmg_accum_rate_pct',60,event='every:0.4s',max_trigger=1,duration=.4,target_effect='pool'),B('late power','atk_pct',100,event='every:0.3s',max_trigger=1,duration=1),E('release','damage','accum_split_damage',0,'target',event='event:state_end:pool',target_effect='pool')]
  elif case=='all-full-removal':
   x[N[0]]=[B('first','dmg_accum_dealt_atk_pct',1,'target'),E('remove second','instant','remove_named_buff',0,event='event:accum_full:first',target_effect='second'),E('first release','damage','accum_split_damage',0,'target',event='event:accum_full:first',target_effect='first')]
   x[N[1]]=[B('second','dmg_accum_received_atk_pct',1,'target'),E('second release','damage','accum_split_damage',0,'target',event='event:accum_full:second',target_effect='second')]
  else:
   x[N[0]]=[E('HP space','instant','current_hp_reduce',50),B('body lifesteal','lifesteal_pct',1000),B('pool','dmg_accum_dealt_atk_pct',1000,'target',duration=2),B('HP dependent rate','dmg_accum_rate_pct',100,scaling='lost_hp_pct'),E('release','damage','accum_split_damage',0,'target',event='event:state_end:pool',target_effect='pool')]
  yield 'damage-accum-'+case,b,x
 for variant,names in [('received',['도로시','크라운','앨리스','모더니아','루주']),('dealt',['트로니','리타','크라운','앨리스','모더니아']),('combined',['트로니','도로시','크라운','앨리스','모더니아']),('owned-reordered',['모더니아','크라운','도로시','트로니','앨리스'])]:
  b=m.body(35,True,names);b['burst_gauge_mode']='fixed'
  if variant=='owned-reordered':
   for n in names:b['profile']['chars'][n].update(affinity=35,collection_stage='SR15',skill_levels={'1':7,'2':9,'3':10})
   b['profile']['chars']['트로니']['equip_skills']['atk_pct']=[11.11,11.11,12.34]
  yield 'raw-damage-accum-'+variant,b,{}

def verify(backend):
 from gpu_selector import Cuda
 from verification_session import VerificationSession
 from types import SimpleNamespace
 session=VerificationSession();session.device=Cuda();rows=[]
 try:
  rows+=independent(session.device,backend)
  planned=list(fixtures());planned=[c for c in planned if c[0]=='raw-damage-accum-combined'] if backend=='ptx' else planned
  if all(r['passed'] for r in rows):
   for name,b,x in planned:
    row=session.compare(SimpleNamespace(compare=compare),name,b,x,backend);rows.append(row)
    if not row['passed']:break
 finally:session.close()
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx'],default='native');a=p.parse_args()
 files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'research/upstream/nikke-calc-master/calculator').glob('*.py'))+[ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json']+[ROOT/'app'/n for n in ('detail_effects.cu',*(['detail_effects-sm86.cubin','detail_effects-sm86.json'] if a.backend=='native' else ['detail_effects.ptx','detail_effects-build.json']))]
 hashes={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
 rows=verify(a.backend);stable=all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in hashes.items());planned=12 if a.backend=='native' else 5
 report=dict(passed=stable and len(rows)==planned and all(r['passed'] for r in rows),backend=a.backend,cases=rows,source_stable=stable,source_sha256=hashes,cpu_model_corrected=True,in_game_rules_verified=False,cpu_traces_used_as_gpu_input=False)
 (ROOT/f'research/damage-accum-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
