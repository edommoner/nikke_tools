import ast,hashlib,importlib.util,json,sys
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('actor_final_cli',root/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
old=Path('/tmp/nikke-typed-actor-gpu-develop-v1');a=cli.verify_package(old);b=cli.verify_package(root)
x={r['path']:r for r in a['files']};y={r['path']:r for r in b['files']};changed=sorted(n for n in x.keys()&y.keys() if x[n]!=y[n]);added=sorted(y.keys()-x.keys());assert not x.keys()-y.keys()
assert changed==['app/portable_readiness_semantics.py','scripts/nikke_gpu.py'],changed
assert added==['research/portable-coordinate-typed-actor-short-expected.json'],added
functions=lambda p:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert functions(root/'scripts/nikke_gpu.py')==functions(old/'scripts/nikke_gpu.py')
for name in x:
 if name not in changed:assert (root/name).read_bytes()==(old/name).read_bytes(),name
with cli.forbid_gpu():adapter=cli.open_suite(b);entries,data=cli.prepare_entries(adapter,b)
assert len(entries)==67 and cli.sha(data)==a['golden']['input_sha256']==b['golden']['input_sha256']
for aa,bb in zip(a['golden']['entries'],b['golden']['entries'],strict=True):assert aa=={k:bb[k] for k in aa}
assert a['golden']['source_sha256']==b['golden']['source_sha256']
capture=Path('/tmp/nikke-typed-actor-metal-v1');cmp=cli.load(capture/'comparison.json');assert cmp['calculation_verified'] and not cmp['mismatches'];assert b['golden']['generated_normalized']==cmp['generated_normalized']
protected=['app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py','gpu/binary64.slang','gpu/core_probability.slang','research/summarize-portable-cross-gpu.py','app/portable_compile_cache.py']
prior=Path('/tmp/nikke-typed-aim-final-v1')
for name in protected:assert (root/name).read_bytes()==(prior/name).read_bytes(),name
checkout=Path('/private/tmp/nikke-runtime-resident')
for row in b['files']:assert hashlib.sha256((checkout/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
r=dict(schema=1,execution_package_id=a['package_id'],final_package_id=b['package_id'],payload_files_verified=len(y),existing_payload_files_exact=len(x)-2,changed_files=changed,added_files=added,all_cli_functions_ast_exact=True,all_cpu_producer_test_and_data_bytes_exact=True,all67_prepared_input_source_native_fingerprints_exact=True,input_bytes=len(data),generated_cuda_metal_exact=True,protected_files_exact=protected,new_native_or_gpu_calls=0,scope='Seal registration and scoped readiness metadata only. Reuses the same fresh67 independent audit because every native producer/input/test/calculation and GPU/transport byte is exact; no new final CPU preflight is claimed.')
Path('/tmp/nikke-typed-actor-final-binding-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
