"""Preserve independent receiver CPU semantics for the next GPU fanout port."""
from checkpoint_receipts import ROOT,sha,read,checked_receipts,save_checkpoint
base='research/ports/v77-enemy-fanout-cpu-stage'
reports=['research/enemy-fanout-'+n+'.json' for n in ('reference','unit','after','coverage','existing-fields','batch-native','order-native','owned-api')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
case=r[reports[0]]['cases'][0]
assert len(case['observations'])==14 and case['original_activations']==6 and case['recipient_applications']==9
assert r[reports[1]]['tests_run']==102 and r[reports[3]]['existing_programs_identical']==187
assert len(r[reports[4]]['cases'])==3 and r[reports[5]]['batch_squads']==10 and len(r[reports[6]]['cases'])==25
assert r[reports[7]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[7]]['mode_policy_roundtrip']['passed']
before=read('research/enemy-fanout-before.json');after=r[reports[2]]
assert before['passed'] and before['values']==after['values']
for name,digest in before['source_sha256'].items():
    assert any((ROOT/a/name).is_file() and sha(a+'/'+name if a else name)==digest for a in ('',base)),('baseline provenance',name)
gpu=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json']
for name in gpu:assert sha(name)==sha('research/ports/v76-enemy-fields-verified/'+name),('GPU unchanged',name)
files=reports+gpu+['research/enemy-fanout-before.json','research/enemy-fanout-cpu-stage.json','research/benchmark-enemy-fanout.py','research/checkpoint_receipts.py','research/save-enemy-fanout-cpu-checkpoint.py','README.md','docs/enemy-recipient-bindings.md','app/enemy_recipient_runtime.py','app/reference_rewrite.py','scripts/audit-effect-runtime.py','scripts/verify-common-runtime-unit.py','scripts/verify-enemy-fanout-reference.py','scripts/enemy_fanout_cases.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/enemy-fanout-cpu-checkpoint.json','research/ports/v77-enemy-fanout-cpu-verified',dict(passed=True,objective_complete=False,cpu_only=True,abi='detail_enemy_fields_v76',gpu_fanout_connected=False,normal_summon_admission=False,checks=dict(observations=14,original_activations=6,recipient_applications=9,lightweight_methods=102,existing_programs_identical=187,mixed_squads=10,existing_ordering_cases=25,normal_owned_api=True),efficiency=dict(scope='CPU receiver updates only',before_ms=before['median_ms'],after_ms=after['median_ms'],speedup=after['speedup']),remaining=['GPU recipient snapshot and fanout executor','Recipient-aware removal/periodic/delayed lifecycle','Normal outgoing routing and shot producers','Remaining characters and broad equipment/effect coverage','Whole-system efficiency after full coverage']),files))
