import ast,hashlib,importlib.util,json,sys
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('aim_final_binding',root/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
old=Path('/tmp/nikke-typed-aim-gpu-develop-v3');a=cli.verify_package(old);b=cli.verify_package(root)
x={r['path']:r for r in a['files']};y={r['path']:r for r in b['files']};changed=sorted(n for n in x.keys()&y.keys() if x[n]!=y[n]);added=sorted(y.keys()-x.keys());assert not x.keys()-y.keys()
assert changed==sorted(['app/coordinate_typed_aim_runtime.py','app/portable_coordinate_aim_specs.py','app/portable_coordinate_typed_input.py','app/portable_readiness_semantics.py','scripts/nikke_gpu.py','tests/test_coordinate_typed_aim_gpu.py']),changed
assert added==['research/portable-coordinate-typed-aim-short-expected.json'],added
rejects={
 'app/coordinate_typed_aim_runtime.py':"            if binding.label in ('__enemy__','__enemy__:*'):raise ValueError('Typed aim label cannot alias logical enemy')\n",
 'app/portable_coordinate_aim_specs.py':"        if isinstance(typed_targets,dict) and set(typed_targets)&{'__enemy__','__enemy__:*'}:raise ValueError('Typed aim label cannot alias logical enemy')\n",
 'app/portable_coordinate_typed_input.py':"        if any(label in ('__enemy__','__enemy__:*') for label in labels):raise ValueError('Typed aim label cannot alias logical enemy')\n"}
for name,line in rejects.items():
 current=(root/name).read_text();assert current.count(line)==1 and current.replace(line,'')==(old/name).read_text(),name
functions=lambda p:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert functions(root/'scripts/nikke_gpu.py')==functions(old/'scripts/nikke_gpu.py')
for name,row in x.items():
 if name not in changed:assert (root/name).read_bytes()==(old/name).read_bytes(),name
with cli.forbid_gpu():adapter=cli.open_suite(b);entries,data=cli.prepare_entries(adapter,b)
assert len(entries)==59 and cli.sha(data)==b['golden']['input_sha256']==a['golden']['input_sha256']
for _,_,d in entries:
 if d is not None and d[0].get('typed_aim_policy'):assert not {'__enemy__','__enemy__:*'}&{v['label'] for v in d[0]['typed_bindings']}
assert a['golden']['source_sha256']==b['golden']['source_sha256']
for aa,bb in zip(a['golden']['entries'],b['golden']['entries'],strict=True):assert aa=={k:bb[k] for k in aa}
base=Path('/tmp/nikke-typed-weapon-final-v1');protected=['app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py','gpu/binary64.slang','gpu/core_probability.slang','research/summarize-portable-cross-gpu.py','app/portable_compile_cache.py']
for name in protected:assert (root/name).read_bytes()==(base/name).read_bytes(),name
checkout=Path('/private/tmp/nikke-runtime-resident')
for row in b['files']:assert hashlib.sha256((checkout/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
r=dict(schema=1,execution_package_id=a['package_id'],final_package_id=b['package_id'],payload_files_verified=len(y),existing_payload_files_exact=len(x)-len(changed),changed_files=changed,added_files=added,reject_only_guards_exact=list(rejects),valid_domains_disjoint_from_reserved_names=True,all_cli_functions_ast_exact=True,all59_input_source_native_fingerprints_exact=True,input_bytes=len(data),protected_files_exact=protected,new_gpu_calls=0,scope='Final namespace rejection, seal registration, readiness metadata and tests; GPU source/transport/numeric code exact. Final CPU-only preflight recorded separately.')
Path('/tmp/nikke-typed-aim-final-binding-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
