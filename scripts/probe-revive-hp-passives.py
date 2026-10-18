"""Probe the pinned CPU's HP-conditioned passive restoration before the GPU port."""
import hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('revive_hp_probe',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
rows=[]
for character in ('앨리스','솔린','크라운'):
 names=[character]+[n for n in v.NAMES if n!=character][:4];b=v.body(1,True,names);b['burst_gauge_mode']='fixed'
 b['enemy']['patterns']=[dict(id='lethal',kind='attack',delay=.35,until={'time':.1},spec=dict(coeff=100,atk=100000000,target='slot:1',pierce=True))]
 extra={names[-1]:[v.E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]}
 with v.context('raw-probe',extra):
  try:
   r=v.v.a.evaluate(b);row=dict(character=character,cpu_valid=True,total=r['total_damage'],down_hit=any(h['down'] for h in r['incoming_hits']))
  except Exception as error:row=dict(character=character,cpu_valid=False,error=repr(error))
 rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
files=['scripts/probe-revive-hp-passives.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),probe_completed=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-revive-hp-passive-cpu-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
