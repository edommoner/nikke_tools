"""Named-effect amplification: independent arithmetic and shared squad oracles."""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('named_squad_oracle','scripts/verify-survival-scaling.py')
v=load('named_query_helpers','scripts/verify-detail.py');g=m.g
N=m.N;B=m.B;E=m.E

def independent(device,backend):
 chars=v.characters(N);bs={n:{'atk':1000+i*100,'def':0,'hp':1000000} for i,n in enumerate(N)}
 query_script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
 rows=[]
 for kind in ('attack','received','damage'):
  es=[]
  def add(e,owner=0):es.append((e,N[owner]))
  if kind=='attack':
   add(B('base','atk_caster_based_pct',20,'all_allies'))
   add(B('first','atk_buff_mag_pct',40,'all_allies',target_effect='base',duration=.5))
   add(B('second','atk_buff_mag_pct',60,'all_allies',target_effect='base',duration=1),1)
   add(B('wrong name','atk_buff_mag_pct',900,'all_allies',target_effect='other'))
   key=1;who=2;expected=[400,320]
  elif kind=='received':
   add(B('base','received_dmg_pct',10,'target'))
   add(B('base','received_dmg_pct',20,'target'),1)
   add(B('unrelated','received_dmg_pct',3,'target'))
   add(B('first','received_dmg_buff_mag_pct',50,'target',target_effect='base',duration=.5))
   add(B('second','received_dmg_buff_mag_pct',25,'target',target_effect='base',duration=1),2)
   add(B('wrong recipient','received_dmg_buff_mag_pct',900,'self',target_effect='base'))
   key=12;who=0;expected=[55.5,40.5]
  else:
   add(B('no critical','crit_rate',-15,'all_allies'))
   add(B('first','dmg_scale_mag_pct',25,target_effect='hit',duration=.5))
   add(B('second','dmg_scale_mag_pct',50,target_effect='hit',duration=1))
   add(B('other owner','dmg_scale_mag_pct',900,target_effect='hit'),1)
   add(B('wrong name','dmg_scale_mag_pct',900,target_effect='other'))
   add(E('hit','damage','damage',100,'target',event='on_attack'))
   expected=[1875,3375];who=0
  p=g.compile_effects(chars,es);script=copy.deepcopy(query_script)
  if kind=='damage':
   for index,t in enumerate((.1,.75)):
    script += [[t,0,7,0,0,-1,0,0],[t,2,0,0,-1,index,0,0]]
  else:script += [[t,2,103,who,key,index,0,0] for index,t in enumerate((.1,.75))]
  result=g.run(device,[p],script,[[0,0]],[bs],module_backend=backend)
  actual=[q[38] if kind=='damage' else q[0] for q in result['queries'][0]]
  passed=all(abs(a-b)<1e-8 for a,b in zip(actual,expected))
  row=dict(name='independent-'+kind,passed=passed,expected=expected,actual=actual);rows.append(row);print(json.dumps(row),flush=True)
 return rows

def fixtures():
 for variant in ('combined','deferred-expiry'):
  b=m.body(8);b['burst_gauge_mode']='fixed';extra={n:[] for n in N}
  if variant=='combined':
   extra[N[0]]=[B('base ATK','atk_caster_based_pct',20,'all_allies'),B('ATK magnitude','atk_buff_mag_pct',50,'all_allies',target_effect='base ATK',duration=4),B('base weakness','received_dmg_pct',10,'target')]
   extra[N[1]]=[B('weakness magnitude','received_dmg_buff_mag_pct',80,'target',target_effect='base weakness',duration=5)]
   extra[N[2]]=[B('damage magnitude','dmg_scale_mag_pct',50,target_effect='periodic hit',duration=5),E('periodic hit','damage','damage',150,'target',event='every:0.4s')]
  else:
   extra[N[2]]=[B('early magnitude','dmg_scale_mag_pct',100,target_effect='delayed bonus',duration=3.4),E('delayed bonus','damage','bonus_damage',200,'target',event='burst_cast'),B('late magnitude','dmg_scale_mag_pct',300,target_effect='delayed bonus',event='burst_cast',duration=2)]
  yield 'named-'+variant,b,extra
 for subject in ('브래디','엠마 : 택티컬 업'):
  for reordered in (False,True):
   names=[subject,'리타','크라운','앨리스','모더니아']
   if reordered:names=[names[1],names[3],subject,names[4],names[2]]
   b=m.body(30,True,names);b['burst_gauge_mode']='fixed'
   yield 'raw-named-'+subject+('-reordered' if reordered else ''),b,{}

def verify(backend):
 from verification_session import VerificationSession
 from gpu_selector import Cuda
 session=VerificationSession();session.device=Cuda();rows=[]
 try:
  rows+=independent(session.device,backend)
  if all(r['passed'] for r in rows):
   for name,b,x in fixtures():
    row=session.compare(m,name,b,x,backend);rows.append(row)
    if not row['passed']:break
 finally:session.close()
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx'],default='native');a=p.parse_args()
 files=list((ROOT/'app').glob('*.py'))+[ROOT/'app'/n for n in ('detail_effects.cu',*(['detail_effects-sm86.cubin','detail_effects-sm86.json'] if a.backend=='native' else ['detail_effects.ptx','detail_effects-build.json']))]
 hashes={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
 rows=verify(a.backend);stable=all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in hashes.items())
 report=dict(passed=stable and len(rows)==9 and all(r['passed'] for r in rows),backend=a.backend,cases=rows,source_stable=stable,source_sha256=hashes,game_rules_verified=False,cpu_traces_used_as_gpu_input=False)
 (ROOT/f'research/named-magnitude-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
