"""Common maximum-HP snapshots: independent quantities and shared squad oracle."""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
m=load('max_hp_squad_oracle','scripts/verify-survival-scaling.py')
v=load('max_hp_query_helpers','scripts/verify-detail.py');g=m.g;B=m.B;E=m.E;N=m.N
from calculator.buff_manager import BuffManager
from effect_runtime import pool

def independent_cases():
 # Authored event stimuli; every HP/current maximum below is independent arithmetic.
 start=B('source maximum','max_hp_pct',100)
 gift=B('snapshot','max_hp_from_max_hp_pct',50,'all_allies',event='on_attack',duration=.5)
 late=B('larger source','max_hp_only_pct',100,event='full_burst_start')
 yield 'refresh-and-expiry',[(start,N[0]),(gift,N[0]),(late,N[0])],[(0,0),(.1,7),(.2,7),(.3,1),(.4,7),(1, None)],{
  .1:[(3000,3000),(2000,2000)],.2:[(3000,3000),(2000,2000)],.4:[(3500,4500),(2500,2500)],1:[(3000,3000),(1000,1000)]}
 stacked=B('snapshot','max_hp_from_max_hp_pct',25,'all_allies',event='on_attack',duration=.5,max_stack=2)
 yield 'stack-cap-refresh',[(stacked,N[0])],[(0,0),(.1,7),(.2,7),(.3,7),(1,None)],{
  .1:[(1250,1250)]*2,.2:[(1500,1500)]*2,.3:[(1500,1500)]*2,1:[(1000,1000)]*2}
 gift=B('snapshot','max_hp_from_max_hp_pct',50,N[1],event='on_attack',duration=.5)
 yield 'recipient-and-source-separated',[(B('source maximum','max_hp_only_pct',100),N[0]),(gift,N[0]),(B('source growth','max_hp_pct',100,event='full_burst_start'),N[0])],[(0,0),(.1,7),(.2,1),(.3,7),(1,None)],{
  .1:[(1000,2000),(2000,2000)],.3:[(2000,3000),(2500,2500)],1:[(2000,3000),(1000,1000)]}

def reference_case(effects,events,expected):
 chars=v.characters(N);bs={n:dict(atk=1000,def_=0,hp=1000) for n in N}
 for values in bs.values():values['def']=values.pop('def_')
 class Manager(BuffManager):
  def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
 state=dict(base_stats=bs,hp={n:1000 for n in N},hp_pct={n:100 for n in N},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={},rng_expected=True,camera=set())
 manager=Manager(chars,state=state);rows=[];script=[];label={0:'battle_start',7:'on_attack',1:'full_burst_start'}
 for at,event in events:
  manager.tick(at)
  if event is not None:
   if event==1:manager.state['full_burst']=True
   manager.notify(label[event],at,N[0]);script.append([at,0,event,0,0,-1,0,0])
  if at in expected:
   actual=[(manager.state['hp'][n],manager.effective_max_hp(n)) for n in N[:2]]
   assert actual==expected[at],dict(time=at,actual=actual,expected=expected[at])
   if event==7:assert pool(manager,'max_hp_snapshot'),'Activation must use shared state'
   rows+=actual
   for who in range(2):script.append([at,2,101,who,0,len(rows)-2+who,0,0])
 assert not pool(manager,'max_hp_snapshot'),'Expired carrier must leave shared state'
 return chars,bs,script,rows

def independent(device,backend,reference_only=False):
 rows=[]
 for name,effects,events,expected in independent_cases():
  chars,bs,script,wanted=reference_case(effects,events,expected)
  if reference_only:actual=wanted
  else:
   result=g.run(device,[g.compile_effects(chars,effects)],script,[[0,0]],[bs],module_backend=backend)
   actual=[(row[0],row[2]) for row in result['queries'][0]]
  row=dict(name='independent-'+name,passed=actual==wanted,expected=wanted,actual=actual);rows.append(row);print(json.dumps(row),flush=True)
 return rows

def fixtures():
 for variant in ('refresh-and-healing','simultaneous-expiry','source-down-revive'):
  body=m.body(4);body['burst_gauge_mode']='fixed';extra={n:[] for n in N}
  extra[N[0]]=[B('source maximum','max_hp_pct',50),B('snapshot','max_hp_from_max_hp_pct',25,'all_allies',event='every:0.4s',duration=.6,max_stack=2)]
  extra[N[1]]=[B('HP-derived power','atk_from_hp_pct',2,'all_allies'),B('protection','shield_from_max_hp_pct',10,'all_allies',event='every:0.7s',duration=.5),E('heal','instant','heal_hp_pct',10,'all_allies',event='every:0.3s',scaling='max_hp')]
  if variant=='simultaneous-expiry':
   extra[N[0]][0]['duration']=1
   extra[N[0]][1]['trigger']['timing']=['battle_start'];extra[N[0]][1]['duration']=1
   extra[N[1]].append(B('second snapshot','max_hp_from_max_hp_pct',10,'all_allies',duration=1))
  elif variant=='source-down-revive':
   body['enemy']['patterns']=[m.s.lethal('slot:1',1.2,hits=2,interval=.05)]
   body['enemy']['patterns'][0]['until']={'time':4}
   extra[N[2]]=[E('revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:2s',max_trigger=1)]
  yield 'max-hp-'+variant,body,extra
 for grown in (False,True):
  names=['메어리 : 베이 갓데스','크라운','앨리스','모더니아','루주']
  if grown:names=[names[3],names[1],names[0],names[4],names[2]]
  body=m.body(35,True,names);body['burst_gauge_mode']='fixed'
  if grown:
   for entry in body['profile']['chars'].values():entry.update(affinity=35,collection_stage='SR15',skill_levels={'1':7,'2':9,'3':10})
  yield 'raw-max-hp-'+('grown-reordered' if grown else 'baseline'),body,{}

def compare(device,name,body,extra,backend):
 observed=[];original=BuffManager._activate
 def activate(manager,effect,caster,t,*args,**kwargs):
  result=original(manager,effect,caster,t,*args,**kwargs)
  if effect.get('stat')=='max_hp_from_max_hp_pct':
   observed.extend(ab.hp_bonus_flat for ab in pool(manager,'max_hp_snapshot').values() if ab.effect is effect and ab.caster==caster)
  return result
 with patch.object(BuffManager,'_activate',activate):row=m.compare(device,name,body,extra,backend)
 row['checks']['positive_snapshot_activation']=any(amount>0 for amount in observed)
 if any(effect.get('stat')=='revive' for effects in extra.values() for effect in effects):row['checks']['revival_exercised']=bool(row['cpu_revives'])
 row['passed']=all(row['checks'].values());row['snapshot_activations']=len(observed)
 print(json.dumps(dict(name=name,passed=row['passed'],failed=[key for key,value in row['checks'].items() if not value])),flush=True)
 return row

def verify(backend):
 from gpu_selector import Cuda
 from verification_session import VerificationSession
 from types import SimpleNamespace
 session=VerificationSession();session.device=Cuda();rows=[]
 try:
  rows+=independent(session.device,backend)
  chosen=list(fixtures());chosen=[row for row in chosen if row[0]=='raw-max-hp-baseline'] if backend=='ptx' else chosen
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
 count=3 if args.reference_only else 8 if args.backend=='native' else 4
 report=dict(passed=stable and len(rows)==count and all(row['passed'] for row in rows),backend='CPU-reference' if args.reference_only else args.backend,cases=rows,source_stable=stable,source_sha256=hashes,game_rules_verified=False,cpu_traces_used_as_gpu_input=False)
 (ROOT/f'research/max-hp-snapshot-{ "reference" if args.reference_only else args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
