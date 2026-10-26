import sys,json,hashlib,importlib.util
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('aim_binding_cli',root/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
old=Path('/tmp/nikke-typed-aim-cpu-v2');a=cli.verify_package(old);b=cli.verify_package(root)
x={r['path']:r for r in a['files']};y={r['path']:r for r in b['files']}
assert x.keys()==y.keys();changed=sorted(n for n in x if x[n]!=y[n])
assert changed==sorted(['app/portable_readiness_semantics.py','app/portable_reference.py','research/world_coordinate_typed_aim_native.py','tests/test_coordinate_typed_aim.py']),changed
checkout=Path('/private/tmp/nikke-runtime-resident')
for row in b['files']:
 assert hashlib.sha256((checkout/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
previous=Path('/tmp/nikke-typed-weapon-final-v1')
protected=['app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py','gpu/binary64.slang','gpu/core_probability.slang','research/summarize-portable-cross-gpu.py','app/portable_compile_cache.py']
for name in protected:assert (root/name).read_bytes()==(previous/name).read_bytes(),name
slang=sorted((root/'gpu').rglob('*.slang'))
for p in slang:assert p.read_bytes()==(previous/p.relative_to(root)).read_bytes(),str(p)
with cli.forbid_gpu():
 adapter=cli.open_suite(b);entries,data=cli.prepare_entries(adapter,b)
assert len(entries)==46 and cli.sha(data)==b['golden']['input_sha256']
assert a['golden']==b['golden']
reg=Path('/tmp/nikke-typed-aim-previous46-cpu-v1');cpu=json.loads((reg/'cpu.json').read_text());tests=json.loads((reg/'cpu-tests.json').read_text())
assert cpu['passed'] and cpu['input_count']==46 and cpu['native_oracles']==29 and cpu['input_sha256']==b['golden']['input_sha256']
assert all(r['exit_code']==0 for r in tests)
r=dict(schema=1,previous_cpu_package_id=a['package_id'],final_cpu_package_id=b['package_id'],verified_payload_files=len(y),exact_unchanged_payload_files=len(y)-len(changed),changed_files=changed,changed_scope='new reference-only observer wording and reporting, readiness metadata and its unit assertion; existing 46 producer/compiler/comparator unchanged',all46_prepared_input_bytes_exact=True,all46_input_bytes=len(data),all46_sealed_golden_exact=True,previous_cpu_preflight=cpu,related_tests=sum(t['tests'] for t in tests),protected_files_exact=protected,slang_files_exact=len(slang),new_native_or_gpu_calls=0)
Path('/tmp/nikke-typed-aim-binding-v3.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
