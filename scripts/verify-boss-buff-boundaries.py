"""Exercise pattern bit 31 and boss-owned definitions through index 255."""
import hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('buff_boundary',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
files=['scripts/verify-boss-buff-boundaries.py','scripts/verify-boss-buffs-detail.py','scripts/verify-boss-clock-detail.py','app/detail_boss.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
def sha(f):return hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
hashes={f:sha(f) for f in files};rows=[];d=v.v.Cuda()
try:
 for dense in (False,True):
  b=v.v.body_for(v.v.NAMES,4,True);b.update(seed=12345,_debug_boss_frames=True,_debug_random_state=True)
  b['enemy']['parts']=[dict(name='fixed armor',hp=0,reach=1),dict(name='breakable cannon',hp=500000,reach=1)]
  b['enemy']['patterns']=[v.buff('armor-'+str(i),.1,.2,enemy={'def_mult':.99,'def_add':i,'received_dmg_pct':(i+1)/10},after=['start','armor-'+str(i)],repeat=0) for i in range(32)]
  extra={v.v.NAMES[0]:[v.E('cleanse all','instant','enemy_buff_cleanse',1000,'target',event='every:1s')]}
  if dense:
   with v.v.t.raw.injected_effects(extra):initial=v.a.evaluate({**b,'_compile_gpu_detail':True})
   for i in range(256-len(initial['program']['effects'])):extra[v.v.NAMES[0]].append(v.E('inactive padding '+str(i),'buff','crit_dmg',0,event='inactive'))
   with v.v.t.raw.injected_effects(extra):compiled=v.a.evaluate({**b,'_compile_gpu_detail':True})
   assert len(compiled['program']['effects'])==256 and max(compiled['program']['boss_effect_rows'].values())==255
  rows.append(v.v.compare(d,'32-pattern-mask-'+('dense-256' if dense else 'ordinary'),b,extra,'native'))
finally:d.close()
assert hashes=={f:sha(f) for f in files}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
(ROOT/'research/detail-boss-buff-boundaries-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
