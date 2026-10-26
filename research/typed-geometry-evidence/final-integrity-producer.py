import importlib.util,sys,json,hashlib,array
from pathlib import Path
root=Path('/tmp/nikke-typed-geometry-final-v3');old=Path('/tmp/nikke-typed-geometry-develop-v1');checkout=Path('/private/tmp/nikke-runtime-resident')
sys.path[:0]=[str(root/'app'),str(root/'research')]
s=importlib.util.spec_from_file_location('geometry_final_integrity',root/'scripts/nikke_gpu.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.verify_package(root);before=a.load(old/'gpu-package.json');gold=a.load(Path('/tmp/nikke-typed-geometry-sealed28-v1.json'));e=a.load(Path('/tmp/nikke-typed-geometry-metal-v1/evidence.json'))
assert m['golden']==gold
for r in m['files']:
    assert a.sha((checkout/r['path']).read_bytes())==r['sha256'],r['path']
old_files={r['path']:r['sha256'] for r in before['files']};new_files={r['path']:r['sha256'] for r in m['files']}
changed={p for p in old_files.keys()&new_files.keys() if old_files[p]!=new_files[p]}
assert changed=={'scripts/nikke_gpu.py','app/portable_readiness_semantics.py','tests/test_portable_readiness_semantics.py'},changed
assert new_files.keys()-old_files.keys()=={'research/portable-coordinate-typed-geometry-short-expected.json'}
assert not old_files.keys()-new_files.keys()
old_cli=(old/'scripts/nikke_gpu.py').read_text();new_cli=(root/'scripts/nikke_gpu.py').read_text()
line=next(r for r in old_cli.splitlines() if r.startswith("SUITES['coordinate-typed-geometry']="))
assert new_cli==old_cli.replace(line,line.replace('development_only=True','development_only=False'))
adapter=a.open_suite(m);entries,data=a.prepare_entries(adapter,m)
assert a.sha(data)==gold['input_sha256']==e['input_sha256']
assert gold['source_sha256']==e['source_sha256']
for x,y in zip(before['golden']['entries'],gold['entries'],strict=True):
    assert set(y)==set(x)|{'output_sha256'} and {k:y[k] for k in x}==x
from portable_coordinate_typed_specs import audit_reserved
h=hashlib.sha256()
with Path('/tmp/nikke-typed-geometry-metal-v1/readback.bin').open('rb') as f:
    for i,(name,words,domain) in enumerate(entries):
        raw=f.read(2032000*4);h.update(raw);assert a.sha(raw)==gold['entries'][i]['output_sha256']
        block=array.array('I');block.frombytes(raw)
        if domain is None:adapter.validate_rejection(block,name)
        else:assert audit_reserved(block)
    assert f.read(1)==b''
assert h.hexdigest()==gold['output_sha256']==e['output_sha256']
for ext in ('cu','metal','cu.reflection.json','metal.reflection.json'):
    assert (Path('/tmp/nikke-typed-geometry-final-generated-v1')/('generated.'+ext)).read_bytes()==(Path('/tmp/nikke-typed-geometry-metal-v1')/('generated.'+ext)).read_bytes(),ext
g=a.load(Path('/tmp/nikke-typed-geometry-final-generated-v1/generation.json'));assert g['verified'] and g['cache_hit'] and g['compiler_invocations']==0
r=dict(schema=1,scope='Final package binds the already completed independent audit: identical native/calculation producers, inputs, sources and saved readbacks; only registry sealing and readiness metadata/assertions changed',package_id=m['package_id'],execution_package_id=before['package_id'],files=len(m['files']),all_payload_checkout_hashes_exact=True,all_native_and_calculation_producer_files_exact=True,all28_input_native_and_source_fingerprints_exact=True,all28_output_hashes_verified=True,positive_reserved_and_rejection_checks_pass=True,paired_generated_cuda_metal_reflections_raw_exact=True,generation_required_hit=True,additional_compiler_calls=0,additional_gpu_calls=0,independent_audit_receipt_sha256=a.sha(Path('/tmp/nikke-typed-geometry-fresh28-v1.json').read_bytes()),output_sha256=h.hexdigest(),cuda_execution_verified=False)
Path('/tmp/nikke-typed-geometry-final-integrity-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
