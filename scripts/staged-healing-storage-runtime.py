"""Load v40 and its declared CPU storage extension in an isolated process."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    sys.path.insert(0,str(ROOT/'app'))
    import engine_worker
    stage=ROOT/'research/staging/v40/app'
    spec=importlib.util.spec_from_file_location('healing_storage_compat',stage/'healing_storage_compat.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge);bridge.install()
    spec=importlib.util.spec_from_file_location('detail_gpu',stage/'detail_gpu.py');module=importlib.util.module_from_spec(spec);sys.modules['detail_gpu']=module;spec.loader.exec_module(module)
    assert module.DETAIL_ABI=='detail_healing_storage_v40';return module
