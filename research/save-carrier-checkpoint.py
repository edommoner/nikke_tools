"""Save a verified joint copy/carrier checkpoint, only after all gates pass.

No build, battle or API runs here. Check current receipts and content hashes;
copy an explicit flat file selection, never a recursive workspace snapshot.
"""
import hashlib,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ABI='detail_lifecycle_carriers_v48'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def receipt(name):
 p=ROOT/'research'/name;r=json.loads(p.read_text(encoding='utf-8'))
 assert r['passed'],f'Unpassed receipt: {name}'
 return r
def current_hashes(report):
 for path,digest in report.get('source_sha256',{}).items():
  assert sha(ROOT/path)==digest,f'Receipt no longer matches: {path}'

full=receipt('detail-normal-acceptance.json')
assert full['selection']=='full' and full['source_stable'] and full['skipped']==0
assert {'test_detail_lifecycle_carriers','test_detail_base_copy'}<=set(full['modules'])
current_hashes(full)
order=json.loads((ROOT/'research/carrier-full-order.json').read_text(encoding='utf-8'))
assert order['same_modules'] and sorted(order['execution_order'])==sorted(full['modules'])
assert order['execution_order'][:2]==['test_detail_lifecycle_carriers','test_detail_base_copy']
assert order['runner_sha256']==sha(ROOT/'research/run-prioritized-acceptance.py')
for name,count in (('carrier-native.json',8),('carrier-ptx.json',8),
                   ('base-copy-native.json',19),('base-copy-ptx.json',9)):
 r=receipt(name);assert r['source_stable'] and len(r['cases'])==count
 assert all(row['passed'] for row in r['cases']);current_hashes(r)
cpu=receipt('carrier-reference-migration.json');assert len(cpu['cases'])==13
compiler=receipt('carrier-compile-migration.json');assert compiler['all_existing_compiled_programs_unchanged']
assert (compiler['standard_accepted'],compiler['favorite_accepted'],compiler['compiler_calls'])==(171,677,1069)
build=receipt('carrier-build-bindings.json');assert build['abi']==ABI
assert build['source_sha256']==sha(ROOT/'app/detail_effects.cu')
native=json.loads((ROOT/'app/detail_effects-sm86.json').read_text())
portable=json.loads((ROOT/'app/detail_effects-build.json').read_text())
assert native['abi']==portable['abi']==ABI
assert native['source_sha256']==portable['source_sha256']==build['source_sha256']
assert native['binary_sha256']==build['native_binary_sha256']==sha(ROOT/'app/detail_effects-sm86.cubin')
assert portable['ptx_sha256']==build['ptx_sha256']==sha(ROOT/'app/detail_effects.ptx')
workspace=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text())[1])
assert workspace==build['workspace_bytes_per_squad']==1103888
api=receipt('carrier-owned-api.json');assert api['pure_gpu_and_verified_and_cpu_equal'] and api['fictional_owned_data'];current_hashes(api)
preview=receipt('carrier-preview-api.json');assert preview['abi']==ABI and len(preview['cases'])==3
assert all(r['passed'] and r['workspace_bytes']==workspace for r in preview['cases']);current_hashes(preview)
probe=json.loads((ROOT/'research/legacy-carrier-audit.json').read_text(encoding='utf-8'))
assert probe['source_stable'] and probe['all_operations_use_current_carrier'] and len(probe['operations'])==6
current_hashes(probe)
snapshot=json.loads((ROOT/'research/base-copy-compile-snapshot.json').read_text(encoding='utf-8'))
checkpoint=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,objective_complete=False,
 scope='Joint base-stat copies and exact carrier migration for existing lifecycle operations. Generic battle interpreter remains.',
 remaining_characters_added_in_carrier_migration=0,abi=ABI,workspace_bytes_per_squad=workspace,
 standard_accepted=171,standard_total=203,favorite_accepted=677,favorite_total=812,
 remaining_standard=[r for r in snapshot['standard']['results'] if not r['supported']],
 native_copy_cases=19,native_carrier_cases=8,portable_copy_cases=9,portable_carrier_cases=8,
 full_regression={k:full[k] for k in ('tests_run','skipped','seconds','source_stable')},
 recovery_execution_reuse={k:v for k,v in full['execution_reuse'].items() if k!='cases'},
 execution_reuse_scope='The recovery comparator subset only, not a count of all GPU battles in the full suite.',
 pre_full_fast_tests=110,fast_is_subset_of_full=True,old_new_CPU_squads=13,
 compiler_migration=compiler,normal_api='GPU only, GPU with CPU verification and CPU; original and edited owned growth agree. Three raw copy squads also use the normal preview API.',
 correctness='CPU agreement is regression evidence. Original CPU copy omissions are corrected with independent expectations. Explicit model assumptions remain, with no blanket in-game verification claim.',
 source_sha256=full['source_sha256'],archive='research/ports/v48-copy-carriers-verified')
checkpoint_path=ROOT/'research/carrier-checkpoint.json'
checkpoint_path.write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files={ROOT/'README.md'}
for folder in ('app','scripts','tests','docs'):
 files.update(p for p in (ROOT/folder).iterdir() if p.is_file())
names=('carrier-checkpoint.json','carrier-contract.json','carrier-progress.json',
 'carrier-build-bindings.json','carrier-native.json','carrier-ptx.json',
 'carrier-reference.json','carrier-reference-migration.json','carrier-compile-migration.json',
 'carrier-owned-api.json','carrier-preview-api.json','carrier-full-order.json',
 'detail-normal-acceptance.json','legacy-carrier-audit.json','legacy-carrier-migration-plan.json',
 'base-copy-native.json','base-copy-ptx.json','base-copy-reference.json','base-copy-reference-squads.json',
 'base-copy-contract.json','base-copy-expansion.json','base-copy-compile-snapshot.json',
 'base-copy-before.json','base-copy-after.json','base-copy-instance-before.json',
 'base-copy-init-percent-before.json','copy-stat-evidence.json','activation-path-audit.json',
 'save-carrier-checkpoint.py')
files.update(ROOT/'research'/name for name in names)
files={p for p in files if p.is_file()}
destination=ROOT/checkpoint['archive'];assert not destination.exists(),'Do not overwrite a verified archive'
manifest={}
for path in sorted(files):
 rel=path.relative_to(ROOT);target=destination/rel
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
 assert sha(target)==sha(path);manifest[rel.as_posix()]=sha(path)
(destination/'archive-manifest.json').write_text(json.dumps(dict(passed=True,abi=ABI,files=manifest),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,archive=checkpoint['archive'],files=len(manifest),full_tests=full['tests_run'])))
