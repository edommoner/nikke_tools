"""Load isolated v42 and the explicit charge/discharge CPU extension."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    sys.path.insert(0,str(ROOT/'app'))
    import engine_worker
    stage=ROOT/'research/staging/v42/app'
    for name in ['heal_charge_compat','detail_gpu']:
        spec=importlib.util.spec_from_file_location(name,stage/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
        if name=='heal_charge_compat':m.install()
    assert m.DETAIL_ABI=='detail_heal_charge_v42';return m
