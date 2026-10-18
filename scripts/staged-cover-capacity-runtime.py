"""Install only v37 GPU interpreter; accepted CPU engine/bridges stay shared."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    sys.path.insert(0,str(ROOT/'app'))
    import engine_worker
    path=ROOT/'research/staging/v37/app/detail_gpu.py';current=sys.modules.get('detail_gpu')
    if current is not None and Path(current.__file__).resolve()==path.resolve():return current
    spec=importlib.util.spec_from_file_location('detail_gpu',path);m=importlib.util.module_from_spec(spec);sys.modules['detail_gpu']=m
    try:spec.loader.exec_module(m)
    except BaseException:
        if current is None:sys.modules.pop('detail_gpu',None)
        else:sys.modules['detail_gpu']=current
        raise
    assert m.DETAIL_ABI=='detail_cover_capacity_v37';return m
