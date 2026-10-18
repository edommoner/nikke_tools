"""Check whether the CPU's B1 ally predicate counts a down squad member."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('dead_ally_survival',ROOT/'scripts/verify-staged-survival.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
names=[*m.N[:4],'맥스웰'];b=m.v.body(4,False,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[m.lethal(at=.1)]
extra={names[1]:[m.B('other B1 exists','atk_pct',100,'all_allies',event='every:0.3s',condition=['has_burst1_ally'])]}
d=m.v.v.v.Cuda()
try:r=m.compare(d,'dead-b1-ally-predicate',b,extra,'native')
finally:d.close()
(ROOT/'research/detail-dead-b1-ally-probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if r['passed'] else 1)
