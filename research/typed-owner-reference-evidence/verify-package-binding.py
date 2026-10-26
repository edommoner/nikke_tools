import hashlib,importlib.util,json,sys
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('owner_binding_cli',root/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
a_root=Path('/tmp/nikke-typed-owner-cpu-v4');b_root=Path('/tmp/nikke-typed-owner-cpu-v5');a=cli.verify_package(a_root);b=cli.verify_package(b_root);m=cli.verify_package(root)
def delta(x,y):
 u={r['path']:r for r in x['files']};v={r['path']:r for r in y['files']};assert u.keys()==v.keys();return sorted(k for k in u if u[k]!=v[k])
assert delta(a,b)==['research/portable_coordinate_typed_owner_cases.py','tests/test_coordinate_typed_owner_policy.py']
assert delta(b,m)==['app/portable_readiness_semantics.py','research/portable_coordinate_typed_owner_contracts.py']
for x in (a,b):assert x['golden']==m['golden']
with cli.forbid_gpu():adapter=cli.open_suite(m);entries,data=cli.prepare_entries(adapter,m)
assert len(entries)==67 and cli.sha(data)==m['golden']['input_sha256']
assert not any(d is not None and d[0].get('typed_actor_policy',{}).get('mode')=='body-owned-current-fields-v1' for _,_,d in entries)
source=Path('/tmp/nikke-typed-actor-final-v1');gpu=sorted((root/'gpu').glob('*.slang'))
for p in gpu:assert p.read_bytes()==(source/'gpu'/p.name).read_bytes(),p.name
protected=['app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py','gpu/binary64.slang','gpu/core_probability.slang','research/summarize-portable-cross-gpu.py','app/portable_compile_cache.py','app/portable_backend.py']
for name in protected:assert (root/name).read_bytes()==(source/name).read_bytes(),name
checkout=Path('/private/tmp/nikke-runtime-resident')
for row in m['files']:assert hashlib.sha256((checkout/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
r=dict(schema=1,old67_cpu_package_id=a['package_id'],new_owner_reference_package_id=b['package_id'],final_package_id=m['package_id'],payload_files_verified=len(m['files']),old67_cpu_producer_inputs_tests_exact_except_unused_owner_fixture_and_unit=True,final_diff_scope='readiness reporting and stronger owner-only verifier; saved native SHA and input SHA independently checked before all5 stronger assertions',all67_prepared_input_and_sealed_golden_exact=True,slang_files_exact=len(gpu),protected_and_transport_files_exact=protected,new_native_or_gpu_calls=0,new_owner_gpu_wire_connected=False)
Path('/tmp/nikke-typed-owner-binding-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
