"""Existing operations: distinct recipients and parent continuation identity.

Reuse the original whole-squad/resource comparators, preserving their assertions.
This adds identity stimuli, not copies of their numerical/formula tests.
"""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=load('carrier_base_helpers','scripts/verify-base-copy.py');m=c.m;g=c.g;N=c.N;B=c.B;E=c.E
from lifecycle_carrier_cases import OPERATIONS

def fixtures():
 files={'decoy':'verify-decoy-healing.py','overheal_storage':'verify-healing-storage.py',
        'healing_charge':'verify-heal-charge.py','damage_accumulation':'verify-damage-accum.py',
        'max_hp_snapshot':'verify-max-hp-snapshot.py'}
 for kind,stat,_ in (*OPERATIONS,('damage_accumulation','dmg_accum_dealt_atk_pct',None)):
  body=m.body(18);body['burst_gauge_mode']='fixed';extra={n:[] for n in N}
  extra[N[0]]=[B('changing recipients',stat,20,'allies_burst_casted_burst3',event='every:0.4s',duration=2),
    B('source HP changes','max_hp_only_pct',50,event='every:0.7s',max_trigger=1),
    B('source ATK changes','atk_pct',50,event='every:0.9s',max_trigger=1)]
  extra[N[1]]=[E('heal recipients','instant','heal_hp_pct',200,'all_allies',event='every:0.3s',scaling='max_hp')]
  if kind=='decoy':
   body['_debug_decoy_frames']=True
   extra[N[1]].append(E('heal decoys','instant','decoy_heal_pct',5,'all_allies',event='every:0.3s'))
  body['enemy']['patterns']=[dict(id='recipient damage',kind='attack',delay=.2,until={'time':18},spec=dict(coeff=100,atk=50000,target='all',hits=50,interval=.35,pierce=True))]
  oracle=m if kind=='shield' else load('carrier_'+kind,'scripts/'+files[kind])
  yield dict(name='carrier-'+stat,kind=kind,stat=stat,body=body,extra=extra,oracle=oracle)

def context(row,observe):
 original=c.BuffManager._activate
 def activate(manager,effect,caster,t,*args,**kwargs):
  result=original(manager,effect,caster,t,*args,**kwargs)
  if effect.get('stat')==row['stat']:
   observe.append(sum(ab.effect is effect and ab.caster==caster for ab in manager._active))
  return result
 return patch.object(c.BuffManager,'_activate',activate)

def compare(device,name,body,extra,backend,row):
 counts=[]
 with context(row,counts):result=row['oracle'].compare(device,name,body,extra,backend)
 result['checks']['distinct_live_recipient_instances']=any(n>1 for n in counts)
 result['passed']=all(result['checks'].values())
 print(json.dumps(dict(name=name,passed=result['passed'],failed=[k for k,v in result['checks'].items() if not v])),flush=True)
 return result

def continuation_case(device,backend,reference_only=False):
 case=dict(name='removed-HP-parent-cannot-grant-through-replacement',axis='hp',effects=[
   E('HP loss','instant','current_hp_reduce',50),
   B('parent','max_hp_from_max_hp_pct',50,event='on_attack',duration=.5),
   E('remove parent','instant','remove_named_buff',0,event='event:parent',target_effect='parent',max_trigger=1),
   E('replacement','instant','buff_stack_init',1,event='event:parent',target_effect='parent',max_trigger=1)],
   steps=[(.1,7,[500,1000],0,0,0),(.2,7,[1000,1500],0,0,0),(1,None,[1000,1000],0,0,0)])
 chars,bs,effects,script,wanted,actual=c.reference_case(case)
 if not reference_only:
  result=g.run(device,[g.compile_effects(chars,effects)],script,[[0,0]],[bs],module_backend=backend);logs=result['queries'][0]
  actual=[[logs[2*i][0],logs[2*i][2],logs[2*i][1],logs[2*i+1][1],logs[2*i+1][6],logs[2*i+1][11]] for i in range(len(wanted))]
 result=dict(name=case['name'],passed=actual==wanted,expected=wanted,actual=actual)
 print(json.dumps(result),flush=True);return result

def verify(backend,reference_only=False):
 from verification_session import VerificationSession
 from gpu_selector import Cuda
 session=VerificationSession();results=[]
 try:
  if not reference_only:session.device=Cuda()
  results.append(continuation_case(session.device,backend,reference_only))
  for row in fixtures():
   if reference_only:
    counts=[]
    with context(row,counts),m.s.v.context(row['name'],row['extra']):m.s.v.v.a.evaluate(row['body'])
    result=dict(name=row['name'],passed=any(n>1 for n in counts),max_instances=max(counts,default=0),scope='CPU activation only')
   else:
    # Bind fixture metadata once; no character-specific execution rules.
    def run(device,name,body,extra,backend,selected=row):return compare(device,name,body,extra,backend,selected)
    result=session.compare(SimpleNamespace(compare=run),row['name'],row['body'],row['extra'],backend)
   results.append(result)
   if not result['passed']:break
 finally:session.close()
 return results

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['native','ptx'],default='native');parser.add_argument('--reference-only',action='store_true');args=parser.parse_args()
 paths=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]+[ROOT/'app/detail_effects.cu']
 if not args.reference_only:paths += [ROOT/'app'/p for p in (['detail_effects-sm86.cubin','detail_effects-sm86.json'] if args.backend=='native' else ['detail_effects.ptx','detail_effects-build.json'])]
 hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 rows=verify(args.backend,args.reference_only);stable=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest for p,digest in hashes.items())
 report=dict(passed=stable and len(rows)==8 and all(r['passed'] for r in rows),source_stable=stable,cases=rows,source_sha256=hashes,backend='CPU reference' if args.reference_only else args.backend,game_rules_verified=False)
 suffix='reference' if args.reference_only else args.backend
 (ROOT/f'research/carrier-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
