"""Use the immutable packet's selected unit CLI; Job ownership stays in its caller."""
import hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
cfg=json.loads((R/'sdk-paths.json').read_text(encoding='utf-8'));P=Path(cfg['packet']);D=R/'host-tests'
req=json.loads((R/'program.json').read_text(encoding='utf-8'))
sys.path[:0]=[str(P/x) for x in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('product_unit_cli',P/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
with cli.forbid_gpu():
 m=cli.verify_package(P);assert m['package_id']==req['owner'] and m['source_commit']==req['source_commit']
 selection=R/req['unit_selection'];assert hashlib.sha256(selection.read_bytes()).hexdigest()==req['unit_selection_sha256']
 document=json.loads(selection.read_text(encoding='utf-8'))
 assert list(document['patterns'])==req['cpu_patterns']
 assert {k:v for k,v in document['patterns'].items() if v is not None}==req['selected_case_ids']
 assert type(req['windows_targeted_tests']) is int and document['expected_tests']==req['windows_targeted_tests']
 result=cli.unit_capture(D/'unit-tests',selection,req['unit_selection_sha256'])
 assert result['passed'] and result['selected_unit_tests_verified'] and not result['unit_tests_verified']
 assert result['tests']==req['windows_targeted_tests'] and result['gpu_calls']==0
 rows=cli.load(D/'unit-tests/cpu-tests.json')
 assert all(x['exit_code']==0 and x['errors']==x['failures']==x['skipped']==0 for x in rows)
 proof=dict(result,owner=m['package_id'],source_commit=m['source_commit'],groups=rows,
  selected_case_ids=req['selected_case_ids'],extra_native_preflight_battles=0,sdk_calls=0)
 with (D/'verification.json').open('x',encoding='utf-8') as f:json.dump(proof,f,indent=2);f.write('\n')
print(json.dumps(dict(passed=True,tests=result['tests'],gpu_calls=0)),flush=True)
