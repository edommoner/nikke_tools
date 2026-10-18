"""Load v41 sharing without changing the accepted production interpreter."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    sys.path.insert(0,str(ROOT/'app'))
    import engine_worker
    stage=ROOT/'research/staging/v41/app'
    for name in ['heal_sharing_compat','detail_gpu']:
        spec=importlib.util.spec_from_file_location(name,stage/(name+'.py'));module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        if name=='heal_sharing_compat':module.install()
    assert module.DETAIL_ABI=='detail_heal_sharing_v41';return module
