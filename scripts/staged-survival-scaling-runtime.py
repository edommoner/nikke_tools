"""Install only the staged v36 interpreter in an isolated development process."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def install():
    sys.path.insert(0,str(ROOT/'app'))
    import engine_worker
    compat_spec=importlib.util.spec_from_file_location('staged_survival_scaling_compat',ROOT/'research/staging/v36/app/survival_scaling_compat.py');compat=importlib.util.module_from_spec(compat_spec);compat_spec.loader.exec_module(compat);compat.install()
    path=ROOT/'research/staging/v36/app/detail_gpu.py';current=sys.modules.get('detail_gpu')
    if current is not None and Path(current.__file__).resolve()==path.resolve():
        assert current.DETAIL_ABI=='detail_survival_scaling_v36';return current
    spec=importlib.util.spec_from_file_location('detail_gpu',path);m=importlib.util.module_from_spec(spec);sys.modules['detail_gpu']=m
    try:spec.loader.exec_module(m)
    except BaseException:
        if current is None:sys.modules.pop('detail_gpu',None)
        else:sys.modules['detail_gpu']=current
        raise
    assert m.DETAIL_ABI=='detail_survival_scaling_v36';return m
