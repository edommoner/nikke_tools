"""Verify phase receipts against current files and seal an explicit archive."""
import hashlib,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths={name:'research/max-hp-snapshot-'+name+'.json' for name in ('native','ptx','reference','reference-squads','regression','fast','wiring','preview-api','existing-api')}
reports={name:read(path) for name,path in paths.items()}
assert all(report['passed'] for report in reports.values())
for name in ('native','ptx','reference','reference-squads','regression','fast','wiring','preview-api'):
 for path,digest in reports[name]['source_sha256'].items():assert sha(ROOT/path)==digest,(name,path,'receipt differs from current source')
for name,count in [('native',8),('ptx',4),('regression',5)]:
 report=reports[name];assert report['source_stable'] and len(report['cases'])==count and all(row['passed'] for row in report['cases'])
assert next(row for row in reports['native']['cases'] if row['name']=='max-hp-source-down-revive')['checks']['revival_exercised']
assert reports['fast']['tests_run']==100 and reports['fast']['skipped']==0
assert len(reports['wiring']['operations'])==7
legacy=(ROOT/'research/max-hp-snapshot-existing-full-module.log').read_text(encoding='utf-8-sig');assert 'Ran 5 tests' in legacy and '\nOK' in legacy
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_max_hp_snapshot_v46'
assert native['source_sha256']==portable['source_sha256']==sha(ROOT/'app/detail_effects.cu')
assert native['binary_sha256']==sha(ROOT/'app/detail_effects-sm86.cubin')
assert portable['ptx_sha256']==sha(ROOT/'app/detail_effects.ptx')
size=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text()).group(1));assert size==1103888
old=read('research/damage-accum-compile-snapshot.json');new=read('research/max-hp-snapshot-compile-snapshot.json')
assert len(old['compiler_calls'])==len(new['compiler_calls'])==1069
unchanged=added=0
for previous,current in zip(old['compiler_calls'],new['compiler_calls']):
 assert previous['characters']==current['characters']
 if 'program_sha256' in previous:
  assert current.get('program_sha256')==previous['program_sha256'];unchanged+=1
 elif 'program_sha256' in current:added+=1
assert unchanged==882 and added==5
assert new['standard']['supported']==168 and new['favorite_accepted']==665
expansion=dict(passed=True,previously_accepted_programs_unchanged=unchanged,newly_accepted_compile_contexts=added,compiler_calls=1069,
 standard_before=167,standard_after=168,favorite_before=661,favorite_after=665,favorite_total=812,
 scope='Compilation acceptance only; not all-character battle verification.')
save('research/max-hp-snapshot-expansion.json',expansion)
contract=read('research/max-hp-snapshot-contract.json');contract['verification_status']='Native 8, PTX 4, selected related regression 5, fast 100, legacy full module 5, normal API 3 routes and two raw preview squads passed; current source and binary hashes verified.'
save('research/max-hp-snapshot-contract.json',contract)
remaining=[row for row in new['standard']['results'] if not row['supported']]
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
 scope='Common maximum-HP snapshot state activation, current-HP continuation and expiry; existing lifecycle registry reused.',
 abi=native['abi'],workspace_bytes_per_squad=size,workspace_changed=False,
 standard_accepted=168,standard_total=203,favorite_accepted=665,favorite_total=812,remaining_standard=remaining,
 compilation_is_battle_verification=False,previous_programs_unchanged=unchanged,new_compile_contexts=added,
 verification=dict(native_cases=8,ptx_cases=4,independent_per_backend=3,native_squads=5,ptx_squads=1,
                   related_existing_cases=5,existing_full_module_tests=5,fast_tests=100,normal_api_routes=3,preview_squads=2,
                   repeated_full_suite=False,node_repeated=False),
 source_hashes_rechecked=True,backend_hashes_rechecked=True,revival_exercised=True,
 test_fixture_corrections=['Initial down/revival case used all_allies, which excludes down characters; equality passed but positive revival witness failed. Replaced with explicit down-target selector and confirmed revival on both reference and GPU.',
                           'Attack fixture extended beyond original helper stop time and uses two close hits. Positive activation witness remains mandatory.'],
 early_receipts=['research/max-hp-snapshot-native-before-revival-fixture-fix.json','research/max-hp-snapshot-ptx-before-boundary-hardening.json'],
 regression_scope='Selected existing HP denominator, stacked HP gain, revival and damage-accumulation squads. No unchanged web code or complete historical suite rerun.',
 existing_full_module_scope='Five established tests passed. Its log has no source-freeze guard; final native/PTX and selected regression receipts independently guard current sources.',
 correctness_policy='CPU parity is regression evidence. External data supports caster final maximum HP and current-HP gain; refresh/stack/expiry interactions remain explicit reference rules rather than blanket in-game verification.',
 next_mechanism_evidence='research/copy-stat-evidence.json',reports=paths,
 source_sha256={p.relative_to(ROOT).as_posix():sha(p) for folder,pattern in [('app','*.py'),('app','detail_effects*'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/folder).glob(pattern) if p.is_file()})
save('research/max-hp-snapshot-checkpoint.json',checkpoint)
save('research/max-hp-snapshot-progress.json',dict(objective_complete=False,phase='v46 verified; all-character goal remains active',abi=native['abi'],checkpoint='research/max-hp-snapshot-checkpoint.json',remaining_standard=len(remaining),next_mechanism_evidence='research/copy-stat-evidence.json'))
destination=ROOT/'research/ports/v46-max-hp-snapshot-verified';assert not destination.exists(),'Do not overwrite a sealed archive'
files=[p for folder in ('app','scripts','tests','docs') for p in (ROOT/folder).iterdir() if p.is_file()]+[ROOT/'README.md']
files += [p for p in (ROOT/'research').iterdir() if p.is_file() and (p.name.startswith(('max-hp-snapshot-','detail-max-hp-snapshot-','verify-max-hp-snapshot-')) or p.name in ('save-max-hp-snapshot-checkpoint.py','copy-stat-evidence.json'))]
for path in files:
 target=destination/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
assert all(sha(path)==sha(destination/path.relative_to(ROOT)) for path in files)
save('research/max-hp-snapshot-archive.json',dict(passed=True,path=destination.relative_to(ROOT).as_posix(),files=len(files),sha256={path.relative_to(ROOT).as_posix():sha(path) for path in files}))
print(json.dumps(dict(passed=True,archive_files=len(files),remaining=len(remaining))))
