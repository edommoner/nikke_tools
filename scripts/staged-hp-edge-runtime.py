"""Substitute only the staged GPU interpreter in a development test process."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    sys.path.insert(0,str(ROOT/'app'))
    import engine_worker
    path=ROOT/'research/staging/v35/app/detail_gpu.py'
    current=sys.modules.get('detail_gpu')
    if current is not None and Path(current.__file__).resolve()==path.resolve():
        assert current.DETAIL_ABI=='detail_hp_edge_v35'
        return current
    spec=importlib.util.spec_from_file_location('detail_gpu',path)
    module=importlib.util.module_from_spec(spec);previous=sys.modules.get('detail_gpu');sys.modules['detail_gpu']=module
    try:spec.loader.exec_module(module)
    except BaseException:
        if previous is None:sys.modules.pop('detail_gpu',None)
        else:sys.modules['detail_gpu']=previous
        raise
    assert module.DETAIL_ABI=='detail_hp_edge_v35'
    return module
