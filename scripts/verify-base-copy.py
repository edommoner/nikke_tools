"""Base-stat copies: independent selection/quantity witnesses and shared squads."""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
m=load('copy_squad_oracle','scripts/verify-survival-scaling.py');v=load('copy_quantity_helpers','scripts/verify-detail.py')
g=m.g;B=m.B;E=m.E;N=m.N
from calculator.buff_manager import BuffManager
from calculator.timeline import _register_instant_handlers,CharState
from base_copy_runtime import POLICIES
from resource_frame_capture import FrameCapture

def independent_cases():
 def copied(stat,value=20,**kw):return B('copied',stat,value,event='on_attack',duration=.5,copy_from=POLICIES[stat].selector,**kw)
 boost=B('reverse final rank','atk_pct',200,N[2])
 yield dict(name='base-ATK-rank-and-live-stack',axis='atk',effects=[boost,copied('atk_copy',max_stack=5),E('add stacks','instant','buff_stack_add',2,event='full_burst_start',target_effect='copied')],
  steps=[(.1,7,[400],2000,2,0),(.2,1,[1200],2000,2,0),(.3,7,[1600],2000,2,0),(1,None,[0],0,0,0)])
 yield dict(name='self-and-stable-tie',axis='atk',self_tie=True,effects=[B('reverse final rank','atk_pct',1000,N[1]),copied('atk_copy')],
  steps=[(.1,7,[400],2000,1,0),(.2,7,[400],2000,1,0),(1,None,[0],0,0,0)])
 yield dict(name='base-HP-rank-no-refresh-heal',axis='hp',effects=[B('reverse final HP rank','max_hp_only_pct',200,N[2]),B('healing potency must not amplify gift','heal_received_pct',999),copied('hp_copy',50),E('lose HP','instant','current_hp_reduce',50,event='full_burst_start')],
  steps=[(.1,7,[2000,2000],2000,2,1000),(.2,1,[1000,2000],2000,2,1000),(.3,7,[1000,2000],2000,2,1000),(1,None,[1000,1000],0,0,0),(1.1,7,[2000,2000],2000,2,1000),(2,None,[1000,1000],0,0,0)])
 yield dict(name='named-child-observes-prepared-copy',axis='damage',effects=[boost,B('no critical','crit_rate',-15,'all_allies'),copied('atk_copy'),E('child damage','damage','damage',100,'target',event='event:copied')],
  steps=[(.1,7,[1400],2000,2,0)])
 for stat in POLICIES:
  hp=stat=='hp_copy'
  yield dict(name='stack-init-'+stat,axis='hp' if hp else 'atk',effects=[copied(stat,50 if hp else 20,max_stack=5),E('initial stacks','instant','buff_stack_init',2,event='full_burst_start',target_effect='copied')],
   steps=[(.1,1,[1000,3000] if hp else [800],2000,2,0),(.2,7,[4000,4000] if hp else [1200],2000,2,3000 if hp else 0),(1,None,[1000,1000] if hp else [0],0,0,0)])
 gift=copied('hp_copy',50);gift['target']='all_allies'
 yield dict(name='child-removes-one-recipient-before-HP-grant',axis='hp',query_who=2,effects=[E('initial HP loss','instant','current_hp_reduce',50,N[2]),gift,E('remove recipient','instant','remove_named_buff',0,N[2],event='event:copied',target_effect='copied',remove_scope='target')],
  steps=[(.1,7,[750,1500],2000,2,1000),(1,None,[750,1500],0,0,0)])
 yield dict(name='removed-parent-cannot-grant-through-reused-slot',axis='hp',effects=[E('initial HP loss','instant','current_hp_reduce',50),copied('hp_copy',50),E('remove parent','instant','remove_named_buff',0,event='event:copied',target_effect='copied',max_trigger=1),E('create replacement','instant','buff_stack_init',1,event='event:copied',target_effect='copied',max_trigger=1)],
  steps=[(.1,7,[500,2000],2000,2,0),(.2,7,[1500,2000],2000,2,1000),(1,None,[1000,1000],0,0,0)])

def reference_case(case):
 chars=v.characters(N);bs={n:dict(atk=value,**{'def':0},hp=value) for n,value in zip(N,(1000,2000,1500,900,800))}
 if case.get('self_tie'):bs[N[0]]['atk']=2000
 effects=[(effect,N[0]) for effect in case['effects']]
 class Manager(BuffManager):
  def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
 state=dict(base_stats=bs,hp={n:values['hp'] for n,values in bs.items()},hp_pct={n:100 for n in N},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={},rng_expected=True,camera=set())
 manager=Manager(chars,state=state);_register_instant_handlers(manager,{n:CharState(c,bs[n]['atk'],None) for n,c in zip(N,chars)},None)
 total=0
 def skill(effect,owner,t):
  nonlocal total
  buffs=manager.get_buffs(owner,'__enemy__',t)
  hit=v.default_hit_type(coeff=effect['fixed_value'],is_normal_atk=False,is_full_burst=state['full_burst'])
  total+=v.calc_damage(bs[owner]['atk'],buffs,chars[N.index(owner)]['_weapon'],hit,enemy_def=0,expected=True)['damage']
 manager.register_damage_handler(skill)
 script=[];wanted=[];actual=[]
 for who,name in enumerate(N):manager.notify('battle_start',0,name);script.append([0,0,0,who,0,-1,0,0])
 for at,event,value,basis,source,gift in case['steps']:
  manager.tick(at)
  if event is not None:
   if event==1:state['full_burst']=True
   manager.notify({7:'on_attack',1:'full_burst_start'}[event],at,N[0]);script.append([at,0,event,0,0,-1,0,0])
  recipient=N[case.get('query_who',0)]
  if case['axis']=='atk':observed=[manager.get_buffs(recipient,'__enemy__',at).get('atk_flat',0)];query=103;arg=1
  elif case['axis']=='hp':observed=[state['hp'][recipient],manager.effective_max_hp(recipient),state['hp_pct'][recipient]];query=101;arg=0
  else:observed=[total];query=0;arg=-1
  carriers=[ab for ab in manager._active if ab.effect.get('stat') in POLICIES and ab.caster==N[0]]
  fields=[sum(ab.copy_basis for ab in carriers),sum(N.index(ab.copy_source)+1 if ab.copy_source is not None else 0 for ab in carriers),sum(getattr(ab,'copy_last_gift',0) for ab in carriers)]
  expected_value=[*value,value[0]/value[1]*100] if case['axis']=='hp' else value
  expected=[*expected_value,basis,source,gift];got=[*observed,*fields]
  assert got==expected,dict(case=case['name'],time=at,expected=expected,actual=got)
  actual.append(got);wanted.append(expected)
  script += [[at,2,query,case.get('query_who',0),arg,len(actual)*2-2,0,0],[at,2,125,0,-1,len(actual)*2-1,0,0]]
 return chars,bs,effects,script,wanted,actual

def independent(device,backend,reference_only=False):
 rows=[]
 for case in independent_cases():
  chars,bs,effects,script,wanted,actual=reference_case(case)
  if not reference_only:
   result=g.run(device,[g.compile_effects(chars,effects)],script,[[0,0]],[bs],module_backend=backend);logs=result['queries'][0];actual=[]
   for i in range(len(wanted)):
    value=logs[2*i];fields=logs[2*i+1]
    observed=[value[0]] if case['axis']=='atk' else [value[0],value[2],value[1]] if case['axis']=='hp' else [value[38]]
    actual.append([*observed,fields[1],fields[6],fields[11]])
  row=dict(name='independent-'+case['name'],passed=actual==wanted,expected=wanted,actual=actual);rows.append(row);print(json.dumps(row),flush=True)
 return rows

def fixtures():
 for variant in ('named-order-and-stack','source-down-and-reselect','HP-snapshot-and-storage','recipient-sets'):
  body=m.body(18 if variant=='recipient-sets' else 4);body['burst_gauge_mode']='fixed';extra={n:[] for n in N}
  for i,stat in enumerate(POLICIES):extra[N[i]].append(B('copy '+stat,stat,20,event='every:0.4s',duration=.6,max_stack=3 if stat=='atk_copy' else 1,copy_from=POLICIES[stat].selector))
  extra[N[0]].append(E('copy child','damage','damage',100,'target',event='event:copy atk_copy'))
  extra[N[0]].append(E('stack increase','instant','buff_stack_add',1,event='every:0.5s',target_effect='copy atk_copy'))
  if variant=='named-order-and-stack':
   for i,stat in enumerate(POLICIES):extra[N[i]].append(E('initial copy '+stat,'instant','buff_stack_init',1,target_effect='copy '+stat))
   extra[N[1]].append(B('initialized HP condition','atk_pct',50,'all_allies',event='passive',condition=['self_hp_below:90']))
  elif variant=='source-down-and-reselect':
   body['enemy']['patterns']=[m.s.lethal('slot:3',1.2)];body['enemy']['patterns'][0]['until']={'time':4}
   extra[N[4]].append(E('revive source','instant','revive',50,'allies_down_top_atk_excl:1',event='every:2s',max_trigger=1))
  elif variant=='HP-snapshot-and-storage':
   extra[N[1]] += [B('final HP gift','max_hp_from_max_hp_pct',10,'all_allies',event='every:0.7s',duration=.8),B('overheal storage','heal_overcharge_store',20,'all_allies',event='every:0.6s',duration=.7)]
   extra[N[4]].append(E('heal','instant','heal_hp_pct',10,'all_allies',event='every:0.3s',scaling='max_hp'))
  elif variant=='recipient-sets':
   for effects in extra.values():
    for effect in effects:
     if effect.get('stat') in POLICIES:effect.update(target='allies_burst_casted_burst3',duration=2)
  yield 'copy-'+variant,body,extra
 for subject in ('길티','신','퀀시'):
  for grown in (False,True):
   names=[subject,'리타','크라운','앨리스','모더니아']
   if grown:names=[names[4],names[1],subject,names[2],names[3]]
   body=m.body(35,True,names);body['burst_gauge_mode']='fixed'
   if grown:
    for entry in body['profile']['chars'].values():entry.update(affinity=35,collection_stage='SR15',skill_levels={'1':7,'2':9,'3':10})
   yield 'raw-copy-'+subject+('-grown-reordered' if grown else ''),body,{}
 yield 'raw-copy-combined',m.body(35,True,['길티','신','퀀시','리타','모더니아']),{}

def project(manager,t,capture):
 program=capture.program;labels={value:key for key,value in program['states'].items()};names=[c['name'] for c in program['chars']]
 keys=[-1]+sorted({int(row[3]) for row in program['effects'] if row[1]==0 and row[2] in (85,86)})
 carriers=[ab for ab in manager._active if ab.effect.get('stat') in POLICIES];rows=[]
 for key in keys:
  chosen=[ab for ab in carriers if key<0 or ab.effect.get('name','')==labels[key]]
  rows.append(dict(time=t,key=key,basis={n:sum(ab.copy_basis for ab in chosen if ab.caster==n) for n in names},source={n:sum(names.index(ab.copy_source)+1 if ab.copy_source is not None else 0 for ab in chosen if ab.caster==n) for n in names},gift={n:sum(getattr(ab,'copy_last_gift',0) for ab in chosen if ab.caster==n) for n in names},carriers=len(chosen)))
 return rows

def compare(device,name,body,extra,backend):
 body={**body,'_debug_base_copy_frames':True}
 with FrameCapture(g,project) as capture:row=m.compare(device,name,body,extra,backend)
 expected=capture.samples+capture.final_samples;actual=capture.gpu.get('_base_copy_frames')
 row['checks']['copy_frames']=m.s.v.close(expected,actual)
 row['checks']['positive_copy_control']=any(any(value>0 for value in frame['basis'].values()) for frame in expected)
 if any(effect.get('target')=='allies_burst_casted_burst3' for effects in extra.values() for effect in effects):
  definitions=sum(row[1]==0 and row[2] in (85,86) for row in capture.program['effects'])
  row['checks']['distinct_recipient_instances_exercised']=any(frame['key']==-1 and frame['carriers']>definitions for frame in expected)
 if any(effect.get('stat')=='revive' for effects in extra.values() for effect in effects):row['checks']['revival_exercised']=bool(row['cpu_revives'])
 row['passed']=all(row['checks'].values());row['copy_frame_rows']=len(expected)
 if not row['checks']['copy_frames']:row['difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(expected,actual or [])) if not m.s.v.close(c,x)),dict(cpu_rows=len(expected),gpu_rows=len(actual or [])))
 print(json.dumps(dict(name=name,passed=row['passed'],failed=[key for key,value in row['checks'].items() if not value])),flush=True);return row

def verify(backend):
 from gpu_selector import Cuda
 from verification_session import VerificationSession
 session=VerificationSession();session.device=Cuda();rows=[]
 try:
  rows+=independent(session.device,backend)
  chosen=list(fixtures());chosen=[row for row in chosen if row[0]=='raw-copy-combined'] if backend=='ptx' else chosen
  if all(row['passed'] for row in rows):
   for name,body,extra in chosen:
    row=session.compare(SimpleNamespace(compare=compare),name,body,extra,backend);rows.append(row)
    if not row['passed']:break
 finally:session.close()
 return rows

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['native','ptx'],default='native');parser.add_argument('--reference-only',action='store_true');args=parser.parse_args()
 files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'research/upstream/nikke-calc-master/calculator').glob('*.py'))+[ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json']
 if not args.reference_only:files += [ROOT/'app'/name for name in ('detail_effects.cu',*(['detail_effects-sm86.cubin','detail_effects-sm86.json'] if args.backend=='native' else ['detail_effects.ptx','detail_effects-build.json']))]
 hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 rows=independent(None,args.backend,True) if args.reference_only else verify(args.backend)
 stable=all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
 count=8 if args.reference_only else 19 if args.backend=='native' else 9
 report=dict(passed=stable and len(rows)==count and all(row['passed'] for row in rows),backend='CPU-reference' if args.reference_only else args.backend,cases=rows,source_stable=stable,source_sha256=hashes,game_rules_verified=False,cpu_traces_used_as_gpu_input=False)
 (ROOT/f'research/base-copy-{ "reference" if args.reference_only else args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
