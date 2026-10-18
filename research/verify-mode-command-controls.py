"""Two representative existing mode integrations; reuse the shared comparer."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('mode_command_previous_controls',ROOT/'scripts/verify-modes-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/'app'/name for name in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=v.Cuda();rows=[]
try:
    for label,effects,seconds in v.scenarios():
        if label not in ('charge-expiry','shot-end-removes-ammo'):continue
        with v.p.custom_effects(effects),v.observe_modes() as observed:row=v.p.full.compare(device,label,v.body_for(v.p.NAMES,seconds,True),module_backend='native')
        assert row['passed'] and observed['mode_shots']>0,(row,observed)
        row['mode_observations']=observed;rows.append(row)
finally:device.close()
assert len(rows)==2 and before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,cases=rows,source_stable=True,source_sha256=before,cpu_trace_used_as_gpu_input=False)
(ROOT/'research/mode-commands-mode-controls.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=2)))
