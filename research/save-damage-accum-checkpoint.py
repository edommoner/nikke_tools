"""Seal current receipts without rerunning identical GPU comparisons."""
import hashlib,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
reports={key:read(path) for key,path in {
 'native':'research/damage-accum-native.json','ptx':'research/damage-accum-ptx.json',
 'fast':'research/detail-common-fast-acceptance.json','wiring':'research/damage-accum-wiring.json',
 'expansion':'research/damage-accum-expansion.json','preview':'research/damage-accum-preview-api.json',
 'owned_api':'research/detail-owned-api-acceptance.json'}.items()}
assert all(r['passed'] for r in reports.values())
for key in ('native','ptx','fast','wiring','preview'):
 for path,digest in reports[key]['source_sha256'].items():
  assert sha(ROOT/path)==digest,(key,path,'source changed after verification')
for key,count in [('native',12),('ptx',5)]:
 assert reports[key]['source_stable'] and len(reports[key]['cases'])==count
 assert all(c['passed'] for c in reports[key]['cases'])
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_damage_accum_v45'
assert native['source_sha256']==portable['source_sha256']==sha(ROOT/'app/detail_effects.cu')
assert native['binary_sha256']==sha(ROOT/'app/detail_effects-sm86.cubin')
assert portable['ptx_sha256']==sha(ROOT/'app/detail_effects.ptx')
size=int(re.search(r'detail_state_bytes_v\d+\s*=\s*(\d+);',(ROOT/'app/detail_effects.ptx').read_text()).group(1))
assert size==1103888
for file,needle in [('damage-accum-existing-full-module.log','Ran 5 tests'),('damage-accum-recovery-regression.log','Ran 3 tests')]:
 log=(ROOT/'research'/file).read_text(encoding='utf-8-sig');assert needle in log and '\nOK' in log
assert 'pass 28' in (ROOT/'research/damage-accum-node.log').read_text(encoding='utf-8-sig')
before=read('research/damage-refresh-before.json');after=read('research/damage-refresh-after.json')
assert before['released_without_new_hits']==700 and after['released_without_new_hits']==0
contract={
 'abi':native['abi'],'workspace_bytes_per_squad':size,'objective_complete':False,
 'operation':'damage_accumulation','carrier_stat_codes':[81,82],'rate_stat_code':83,
 'discharge_kind':34,'full_event_code':50,'interest_bit':4,
 'shared_state':'Active UID pools and per-manager archive are separate; archive survives carrier removal and is cleared on fresh activation.',
 'scopes':'Dealt pool observes its owner boss damage; received pool observes squad boss damage. Current supported body/parts paths only.',
 'capacity':'Final ATK at activation times capacity percent. Subsequent ATK changes do not resize it.',
 'rate':'Sum unreferenced quantities, default to 100 only if no base quantity exists; add matching named quantities. Explicit zero differs from absent quantity.',
 'ordering':['Existing lifesteal and nested heal callbacks finish before accumulation.',
             'Update dealt then received pools in instance order; update all pools before full notifications.',
             'Snapshot full notification identities so removal by an earlier callback does not erase later delivery.',
             'Consume and clear archive before emitting discharge.',
             'Keep existing queued landing continuation and next-frame timing; compare final drain too.'],
 'discharge':'Stored damage times split bonus, truncate; do not reapply ATK, DEF, critical, minimum damage, named hit callback or burst gauge.',
 'storage':'Type-guarded reuse of shield scalar slots; distinct stat codes prevent semantic aliasing. Additional scalar name archive is 2048 bytes.',
 'strict_rejection':['Ambiguous nonempty carrier names across definitions or owners',
                     'Discharge scaling, coefficient and geometry fields not supported by this operation',
                     'Invalid actors, named references, event modes and query keys before CUDA'],
 'cpu_correction':{'before':'research/damage-refresh-before.json','after':'research/damage-refresh-after.json',
                   'rule':'Fresh lifetime resets live and archived amount together. Previous CPU leaked 700 after refresh and expiry without new hits; corrected result is zero.'},
 'verification':'Reuse common whole-squad comparator plus resource_frame_capture.py read-only per-frame/final projection; independent numeric witnesses do not derive expected amounts from CPU.',
 'gpu_input_is_cpu_trace':False,'character_specific_execution_branches_added':False,
 'game_rules_verified':False,
 'limits':['Legacy name-scoped CPU lookup preserved under uniqueness gate.',
           'Rate lookup follows explicit reference membership model; all game interactions are not independently verified.',
           'Current static boss/parts model does not cover every projectile or world geometry.'],
 'extension_guide':'docs/adding-effects.md'}
save('research/damage-accum-contract.json',contract)
coverage=read('research/detail-damage-accum-coverage.json')
remaining=[row for row in coverage['results' if 'results' in coverage else 'rows'] if not row['supported']]
checkpoint={
 'generated_at':datetime.now(timezone.utc).isoformat(),'passed':True,'objective_complete':False,
 'scope':'Common damage accumulation lifecycle extension after existing-character shared-state migration.',
 'abi':native['abi'],'workspace_bytes_per_squad':size,
 'standard_accepted':167,'standard_total':203,'favorite_accepted':661,'favorite_total':812,
 'remaining_standard':remaining,'compilation_is_battle_verification':False,
 'previous_programs_unchanged':872,'new_compile_contexts':10,
 'verification':{'native_cases':12,'ptx_cases':5,'independent_per_backend':4,
                 'native_squads':8,'ptx_squads':1,'fast_tests':97,'node_tests':28,
                 'existing_full_module_tests':5,'recovery_test_methods':3,'recovery_cases':30,
                 'normal_api_routes':3,'preview_squads':2,'full_suite_repeated':False},
 'source_hashes_rechecked':True,'backend_hashes_rechecked':True,
 'intentional_cpu_correction':{'old_stale_release':700,'fresh_lifetime_release':0,'game_rules_verified':False},
 'test_bookkeeping':'An initial PTX run completed all comparisons but source guard detected a concurrent test-selection edit; final native and PTX runs use fixed source and pass guards.',
 'reports':{key:'research/'+name for key,name in {
   'native':'damage-accum-native.json','ptx':'damage-accum-ptx.json',
   'wiring':'damage-accum-wiring.json','expansion':'damage-accum-expansion.json',
   'preview':'damage-accum-preview-api.json','fast':'detail-common-fast-acceptance.json',
   'existing_api':'detail-owned-api-acceptance.json'}.items()},
 'correctness_policy':'CPU parity is regression evidence; independent game evidence takes precedence. All-character/all-effect goal remains incomplete.',
 'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for folder,pattern in [('app','*.py'),('app','detail_effects*'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/folder).glob(pattern) if p.is_file()}}
save('research/damage-accum-checkpoint.json',checkpoint)
destination=ROOT/'research/ports/v45-damage-accum-verified'
assert not destination.exists(),'Do not overwrite a sealed archive'
files=[p for folder in ('app','scripts','tests','docs') for p in (ROOT/folder).iterdir() if p.is_file()]
files += [ROOT/'README.md']
files += [p for p in (ROOT/'research').iterdir() if p.is_file() and
          (p.name.startswith(('damage-accum-','damage-refresh-','detail-damage-accum-','verify-damage-refresh-'))
           or p.name in ('detail-common-fast-acceptance.json','detail-owned-api-acceptance.json','save-damage-accum-checkpoint.py'))]
for p in files:
 target=destination/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
assert all(sha(p)==sha(destination/p.relative_to(ROOT)) for p in files)
save('research/damage-accum-archive.json',{'passed':True,'path':destination.relative_to(ROOT).as_posix(),'files':len(files),'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}})
print(json.dumps({'passed':True,'archive_files':len(files),'remaining':len(remaining)}))
