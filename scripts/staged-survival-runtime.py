"""Load only the staged GPU interpreter/CPU revival bridge in a test process.

Call install() before importing verifier helpers. The running app and its v33
files are not modified; the pinned CPU and ordinary adapter retain their paths.
"""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def install():
 sys.path.insert(0,str(ROOT/'app'))
 import engine_worker
 path=ROOT/'research/staging/v34/app/detail_gpu.py'
 spec=importlib.util.spec_from_file_location('detail_gpu',path);module=importlib.util.module_from_spec(spec)
 previous=sys.modules.get('detail_gpu');sys.modules['detail_gpu']=module
 try:spec.loader.exec_module(module)
 except BaseException:
  if previous is None:sys.modules.pop('detail_gpu',None)
  else:sys.modules['detail_gpu']=previous
  raise
 spec=importlib.util.spec_from_file_location('staged_survival_compat',ROOT/'research/staging/v34/app/survival_compat.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge);bridge.install()
 assert module.DETAIL_ABI=='detail_survival_v34'
 return module
