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


def project(manager,t,capture):
 program=capture.program;labels={i:label for label,i in program['states'].items()};keys=[-1]+sorted({int(r[3]) for r in program['effects'] if r[1]==0 and r[2] in (81,82)})
 names=[c['name'] for c in program['chars']];resident=[a for a in manager._active if a.effect.get('stat') in STATS];rows=[]
 for key in keys:
  chosen=[a for a in resident if key<0 or a.effect.get('name','')==labels[key]]
  archived=sum(manager._accum_last.values()) if key<0 else manager._accum_last.get(labels[key],0)
  rows.append(dict(time=t,key=key,current={n:sum(a.accum for a in chosen if a.caster==n) for n in names},capacity={n:sum(a.accum_cap for a in chosen if a.caster==n) for n in names},done={n:sum(a.accum_done for a in chosen if a.caster==n) for n in names},carriers=len(chosen),archived=archived))
 return rows


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

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx'],default='native');a=p.parse_args()
 files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'research/upstream/nikke-calc-master/calculator').glob('*.py'))+[ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json']+[ROOT/'app'/n for n in ('detail_effects.cu',*(['detail_effects-sm86.cubin','detail_effects-sm86.json'] if a.backend=='native' else ['detail_effects.ptx','detail_effects-build.json']))]
 hashes={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
 rows=verify(a.backend);stable=all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in hashes.items());planned=12 if a.backend=='native' else 5
 report=dict(passed=stable and len(rows)==planned and all(r['passed'] for r in rows),backend=a.backend,cases=rows,source_stable=stable,source_sha256=hashes,cpu_model_corrected=True,in_game_rules_verified=False,cpu_traces_used_as_gpu_input=False)
 (ROOT/f'research/damage-accum-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
