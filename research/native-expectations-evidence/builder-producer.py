import importlib.util,json,sys,time
from pathlib import Path
from unittest.mock import patch
root=Path('/private/tmp/nikke-runtime-resident');sys.path.insert(0,str(root/'app'))
s=importlib.util.spec_from_file_location('expectations_actual_builder',root/'scripts/nikke_gpu.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
baseline=Path('/tmp/nikke-native-expectations-baseline-v2');before=a.verify_package(baseline)
start=time.perf_counter()
with a.forbid_gpu(),patch.object(a,'development_baseline',side_effect=AssertionError('Full baseline must not run')) as full,patch.object(a,'native_value',side_effect=AssertionError('Native calculation must not run')) as native,patch.object(a,'native_hash',side_effect=AssertionError('Native hashing must not run')) as hashing:
    result=a.make_package('coordinate-typed-live-aim',Path('/tmp/nikke-native-expectations-reused-v2.zip'),develop=True,compact=True,native_baseline_package=baseline)
    assert full.call_count==native.call_count==hashing.call_count==0
assert a.verify_package(baseline)==before
result.update(scope='Real 35-input package construction with all native baseline entry points forbidden; not GPU proof',elapsed_seconds=time.perf_counter()-start,baseline_package_id=before['package_id'],native_baseline_calls=0,native_value_calls=0,native_hash_calls=0,gpu_calls=0)
Path('/tmp/nikke-native-expectations-package-proof-v2.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
