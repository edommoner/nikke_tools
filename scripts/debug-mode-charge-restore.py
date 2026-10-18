"""Check reset ordering against the original per-frame CPU weapon oracle."""
import argparse,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('restore_probe',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
ap=argparse.ArgumentParser();ap.add_argument('--cpu-only',action='store_true');args=ap.parse_args()
oracle=v.v.t.oracle;names=['앨리스']+[n for n in v.v.NAMES if n!='앨리스'][:4];chars=oracle.characters(names)
mode=dict(source='스킬3',name='long charging mode',type='weapon_change',target='self',weapon_type='SR',damage_coeff={'10':100},max_ammo=5,charge=True,charge_time=10,full_charge_mult=200,duration=1,trigger={'timing':['battle_start'],'condition':[]})
ammo=v.E('charge ammo','buff','max_ammo_pct',100,event='passive',condition=['during_charge'])
p=oracle.program(chars,[(mode,names[0]),(ammo,names[0])]);stats={n:{'atk':100000,'def':1000,'hp':1000000} for n in names}
script=[[0,0,0,0,0,-1,0,0]]
for i in range(90):script.extend([[i/60,3,0,0,0,-1,0,0],[i/60,2,0,0,-1,i,0,0]])
cpu,totals=oracle.oracle(p,script,[31784,6],stats,startup_full=True)
if args.cpu_only:print(json.dumps({'cpu_ammo_near_restore':[r[44] for r in cpu[58:65]],'cpu_max_ammo_pct':[r[18] for r in cpu[58:65]]}));raise SystemExit()
d=v.v.Cuda()
try:g=v.g.run(d,[p],script,[[31784,6]],[stats],module_backend='native')
finally:d.close()
errors=[dict(frame=i,field=k,cpu=x[k],gpu=y[k]) for i,(x,y) in enumerate(zip(cpu,g['queries'][0])) for k in (18,44) if x[k]!=y[k]]
r=dict(passed=not errors,errors=errors,cpu_ammo_near_restore=[r[44] for r in cpu[58:65]],gpu_ammo_near_restore=[r[44] for r in g['queries'][0][58:65]])
(ROOT/'research/detail-mode-charge-restore-probe.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))
