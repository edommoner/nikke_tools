"""CPU-side compile preflight for named-duration masks above the old bound."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('named_capacity_before',ROOT/'scripts/verify-named-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
rows=[]
for first in (31,32,63,64,95,96,127,128,191,192,223,224,253):
    effects=[v.effect('padding '+str(i),'buff','crit_dmg',0,event='inactive') for i in range(first)]
    effects+=[v.effect('mode','buff','atk_pct',10,duration=1),v.effect('extend','instant','named_buff_duration_extend',1,event='burst_cast',target_effect='mode')]
    try:
        p=v.oracle.program(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in effects])
        rows.append(dict(index=first,accepted=True,state_index=p['states']['mode'],effects=len(p['effects'])))
    except Exception as e:rows.append(dict(index=first,accepted=False,error_type=type(e).__name__,error=str(e)))
report=dict(cpu_preparation_only=True,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/detail_gpu.py','app/detail_effects.cu','scripts/audit-named-capacity.py']})
(ROOT/'research/detail-named-capacity-before.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows))
