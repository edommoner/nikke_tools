"""Independent ordered boss buffs, real enemy cleanse and per-frame defense parity."""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('boss_buffs_clock',ROOT/'scripts/verify-boss-clock-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
g=v.g;a=v.a;E=v.E
def buff(id,at=0,duration=None,**kw):
 return v.pattern(id,'buff',at,duration,**kw)
def fixtures(long=False):
 cases=[
 ('startup-multiply-add',[buff('armor',enemy={'def_mult':2,'def_add':-3500})],[]),
 ('negative-defense-before-final-damage-clamp',[buff('negative',enemy={'def_mult':0,'def_add':-70000})],[]),
 ('start-order-not-declaration',[buff('later',3,5,enemy={'def_mult':2,'def_add':1300}),buff('earlier',1,9,enemy={'def_mult':.5,'def_add':-6000})],[]),
 ('same-start-declaration-order',[buff('first',1,9,enemy={'def_mult':2,'def_add':1300}),buff('second',1,5,enemy={'def_mult':.5,'def_add':-6000})],[]),
 ('received-damage-stacks-and-lifetime',[buff('resist',0,3,enemy={'received_dmg_pct':-33.33}),buff('vulnerable',1,8,enemy={'received_dmg_pct':45.67})],[]),
 ('received-damage-final-minimum',[buff('block',0,4,enemy={'received_dmg_pct':-150})],[]),
 ('random-caster-ranking-and-world-transitions',[buff('cycle',.2,.7,enemy={'def_mult':1.7,'received_dmg_pct':-35},after=['start','cycle'],repeat=0)],[E('random capture','buff','atk_caster_based_pct',17,'allies_random:2',event='every:0.5s',duration=.6)]),
 ('fullburst-end-damage-keeps-query-snapshot',[buff('cycle',.2,.7,enemy={'def_mult':1.7,'received_dmg_pct':-35},after=['start','cycle'],repeat=0)],[E('random capture','buff','atk_caster_based_pct',17,'allies_random:2',event='every:0.5s',duration=.6),E('full end damage','damage','damage',100,'target',event='full_burst_end')]),
 ('enemy-caster-is-not-first-nikke',[buff('collision',0,6,enemy={'received_dmg_pct':-30})],[E('enemy is visible','buff','atk_pct',10,event='on_attack',condition=['target_state:collision·received_dmg_pct'],duration=.2),E('enemy stack is not mine','buff','atk_pct',1000,event='on_attack',condition=['self_stack_above:collision·received_dmg_pct:1'],duration=2)]),
 ('repeating-buff-releases-before-reapply',[buff('cycle',.1,.4,enemy={'def_mult':1.3,'received_dmg_pct':-20},after=['start','cycle'],repeat=0)],[]),
 ('epsilon-close-reopen',[buff('tiny',0,1e-12,enemy={'received_dmg_pct':-50},after=['start','tiny'],repeat=3)],[]),
 ('cleanse-latest-skips-irremovable',[buff('old',0,None,enemy={'def_mult':1.7,'received_dmg_pct':-30}),buff('recent',1,None,enemy={'def_add':7000,'received_dmg_pct':20}),buff('protected',2,None,enemy={'def_mult':1.2,'received_dmg_pct':-15},irremovable=True)],[E('cleanse every two seconds','instant','enemy_buff_cleanse',1,'target',event='every:2s')]),
 ('startup-cleanse-deferred-to-next-begin',[buff('opening',enemy={'def_mult':2,'received_dmg_pct':-60})],[E('startup cleanse','instant','enemy_buff_cleanse',1,'target')]),
 ('shot-cleanse-retains-current-frame-overlay',[buff('armor',enemy={'def_mult':3,'received_dmg_pct':-70})],[E('on shot cleanse','instant','enemy_buff_cleanse',1,'target',event='on_attack',max_trigger=1),E('same shot skill','damage','damage',333,'target',event='on_attack')]),
 ('zero-value-defaults-to-one',[buff('a',enemy={'def_mult':2}),buff('b',enemy={'received_dmg_pct':-50})],[E('zero default','instant','enemy_buff_cleanse',0,'target',event='every:1s')]),
 ('fraction-truncates-to-zero',[buff('a',enemy={'def_mult':2,'received_dmg_pct':-40})],[E('fraction','instant','enemy_buff_cleanse',.5,'target',event='every:1s')]),
 ('negative-limit-removes-nothing',[buff('a',enemy={'def_mult':2})],[E('negative','instant','enemy_buff_cleanse',-1,'target',event='every:1s')]),
 ('self-target-removes-nothing',[buff('a',enemy={'def_mult':2})],[E('self target','instant','enemy_buff_cleanse',3,'self',event='every:1s')]),
 ('cleanse-does-not-close-lifecycle-reopen-restores',[buff('a',.2,.7,enemy={'def_mult':1.7,'received_dmg_pct':-50},after=['start','a'],repeat=0)],[E('periodic cleanse','instant','enemy_buff_cleanse',2,'target',event='every:1s')]),
 ('large-limit-cleanses-every-eligible',[buff('a',enemy={'def_mult':2}),buff('b',enemy={'def_add':7000}),buff('protected',enemy={'received_dmg_pct':-10},irremovable=True)],[E('all cleanse','instant','enemy_buff_cleanse',1000,'target',event='every:1s')]),
 ]
 if long:cases=[c for c in cases if c[0] in ('random-caster-ranking-and-world-transitions','fullburst-end-damage-keeps-query-snapshot','repeating-buff-releases-before-reapply','cleanse-latest-skips-irremovable','shot-cleanse-retains-current-frame-overlay','cleanse-does-not-close-lifecycle-reopen-restores')]
 for name,patterns,extra in cases:
  b=v.body_for(v.NAMES,180 if long else 30 if name=='fullburst-end-damage-keeps-query-snapshot' else 12,True)
  b.update(seed=12345,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True,_debug_boss_frames=True)
  b['enemy'].update(patterns=patterns,core_px=6,distance=30)
  yield name,b,{v.NAMES[0]:extra}
 # Retain real source definitions for newly accepted enemy-cleanse characters.
 raw=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
 for name,effects in raw.items():
  if not isinstance(effects,list) or not any(e.get('stat')=='enemy_buff_cleanse' for e in effects if isinstance(e,dict)):continue
  names=[name]+[n for n in v.NAMES if n!=name][:4];b=v.body_for(names,180 if long else 30,True)
  b.update(seed=12345,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True,_debug_boss_frames=True)
  b['enemy']['patterns']=[buff('cycle',.2,4,enemy={'def_mult':2,'received_dmg_pct':-30},after=['start','cycle'],repeat=0)]
  try:a.evaluate({**b,'_compile_gpu_detail':True})
  except g.UnsupportedDetail:continue
  yield 'raw-'+name,b,{}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx','both'],default='both');ap.add_argument('--long',action='store_true');ap.add_argument('--fail-fast',action='store_true');ap.add_argument('--output',default='research/detail-boss-buffs-verification.json');args=ap.parse_args()
 files=['scripts/verify-boss-buffs-detail.py','scripts/verify-boss-clock-detail.py','app/detail_boss.py','app/detail_gpu.py','app/detail_world.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
 def sha(f):return hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
 hashes={f:sha(f) for f in files};d=v.Cuda();rows=[]
 planned=[(backend,n,b,e) for backend in (('native','ptx') if args.backend=='both' else (args.backend,)) for n,b,e in fixtures(args.long)]
 try:
  for backend,n,b,e in planned:
   rows.append(v.compare(d,n,b,e,backend))
   if args.fail_fast and not rows[-1]['passed']:break
 finally:d.close()
 assert hashes=={f:sha(f) for f in files}
 raw_status=json.loads((ROOT/'research/detail-enemy-cleanse-characters.json').read_text(encoding='utf-8'))
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(r['passed'] for r in rows),objective_complete=False,cases=rows,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),source_sha256=hashes,cpu_trace_used_as_gpu_input=False,raw_enemy_cleanse_character_audit=raw_status,raw_character_audit_note='Compilation acceptance is reported separately from actual raw-character battle parity. Authored effects retain all original skills of the five-member squads.')
 (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
