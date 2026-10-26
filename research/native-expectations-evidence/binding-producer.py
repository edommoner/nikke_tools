import ast,hashlib,importlib.util,json,sys
from pathlib import Path
root=Path('/private/tmp/nikke-runtime-resident');sys.path.insert(0,str(root/'app'))
s=importlib.util.spec_from_file_location('expectations_binding_cli',root/'scripts/nikke_gpu.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
old_root=Path('/tmp/nikke-typed-live-aim-final-v1');old=a.load(old_root/'gpu-package.json');assert old['package_id']==a.package_id(old);a.check_records(old_root,old['files'])
baseline=a.verify_package(Path('/tmp/nikke-native-expectations-baseline-v2'));new_root=Path('/tmp/nikke-native-expectations-cli-v2');new=a.verify_package(new_root)
previous={r['path']:r['sha256'] for r in old['files']};current={r['path']:r['sha256'] for r in new['files']}
assert {p for p in previous.keys()&current.keys() if previous[p]!=current[p]}=={'scripts/nikke_gpu.py'}
assert current.keys()-previous.keys()=={'app/portable_development_expectations.py','tests/test_portable_development_expectations.py'}
assert not previous.keys()-current.keys()
for r in new['files']:assert a.sha((root/r['path']).read_bytes())==r['sha256'],r['path']
assert baseline['files']==new['files']
assert old['golden']['input_sha256']==new['golden']['input_sha256']
assert old['golden']['source_sha256']==new['golden']['source_sha256']
for before,after in zip(old['golden']['entries'],new['golden']['entries'],strict=True):
    assert after=={k:before[k] for k in ('name','input_sha256','native_sha256')}
def functions(path):return {n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
before=functions(old_root/'scripts/nikke_gpu.py');after=functions(new_root/'scripts/nikke_gpu.py')
names=['cpu_preflight','native_value','native_hash','run_capture','audit_capture','seal_development','run_job','cache_probe','required_generation_cache_preflight','required_cuda_cache_preflight','generation_capture','publish_transport_input']
for name in names:assert ast.dump(before[name])==ast.dump(after[name]),name
assert [ast.dump(n) for n in before['verify_package'].body[:-1]]==[ast.dump(n) for n in after['verify_package'].body[:-2]]
assert ast.dump(before['verify_package'].body[-1])==ast.dump(after['verify_package'].body[-1])
assert ast.dump(after['verify_package'].body[-2])==ast.dump(ast.parse("if 'native_expectation_baseline' in m:\n from portable_development_expectations import validate\n validate(m)").body[0])
cpu_root=Path('/tmp/nikke-native-expectations-cli-v1');cpu_manifest=a.verify_package(cpu_root)
assert cpu_manifest['golden']==new['golden']
old_helpers=functions(cpu_root/'app/portable_development_expectations.py');new_helpers=functions(new_root/'app/portable_development_expectations.py')
for name in ('reuse','validate','digest'):assert ast.dump(old_helpers[name])==ast.dump(new_helpers[name]),name
assert (cpu_root/'scripts/nikke_gpu.py').read_bytes()==(new_root/'scripts/nikke_gpu.py').read_bytes()
capture=Path('/tmp/nikke-native-expectations-cpu-v1');cpu=a.load(capture/'cpu.json');result=a.load(capture/'result.json')
assert cpu['passed'] and cpu['input_count']==35 and cpu['native_oracles']==22 and cpu['input_sha256']==new['golden']['input_sha256']
assert cpu['gpu_calls']==dict(build=0,execute=0) and result['cpu_verified'] and result['gpu_calls']==0 and result['calculation_verified'] is False
assert not (new_root/'gpu-claimed-metal.json').exists() and not (capture/'readback.bin').exists()
guarded=a.load(Path('/tmp/nikke-native-expectations-package-proof-v2.json'));direct=a.load(Path('/tmp/nikke-native-expectations-cli-v2.json'))
assert guarded['package_id']==direct['package_id']==new['package_id']
r=dict(schema=1,cpu_proof_package_id=cpu_manifest['package_id'],completed_cpu_check_reused_only_for_identical_calculation_producers=True,packaging_helper_reuse_validate_asts_exact=True,utf8_ledger_reading_tested_under_cp932_default=True,scope='Expected-hash package optimization only; unchanged calculation/transport sources remain covered by prior independent Metal35 proof; new CPU-only preflight still recomputes all22 domains',baseline_package_id=baseline['package_id'],candidate_package_id=new['package_id'],prior_metal_package_id=old['package_id'],all_existing_noncontroller_payload_bytes_exact=True,all35_input_native_expectations_exact=True,all_gpu_sources_exact=True,unchanged_native_audit_launch_cache_function_asts=names,verify_package_delta_only_extra_receipt_validation=True,actual_cli_matches_guarded_builder=True,package_seconds=guarded['elapsed_seconds'],package_native_baseline_calls=0,fresh_preflight_domains=22,fresh_preflight_seconds=cpu['elapsed_seconds'],new_gpu_calls=0,windows_requests=0,cuda_cache_hit_verified=False,full_goal_complete=False)
Path('/tmp/nikke-native-expectations-binding-v2.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
