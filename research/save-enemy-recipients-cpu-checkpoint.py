"""Preserve CPU recipient rules; GPU storage and delayed routing remain pending."""
import hashlib,json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/enemy-recipients-reference.json','research/enemy-recipients-unit.json','research/enemy-recipients-coverage.json','research/enemy-recipients-owned-api.json','research/enemy-recipient-queries-after.json','research/runtime-wiring.json']
r=checked_receipts(reports)
before=read('research/enemy-recipients-reference-before.json');benchmark_before=read('research/enemy-recipient-queries-before.json');benchmark_after=r[reports[4]]
assert before['passed'] and before['cases']==r[reports[0]]['cases'] and len(before['cases'][0]['observations'])==18
assert r[reports[1]]['tests_run']==98 and r[reports[2]]['supported']==r[reports[2]]['existing_programs_identical']==187
assert r[reports[3]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[3]]['mode_policy_roundtrip']['passed'] and r[reports[3]]['original_total']!=r[reports[3]]['total']
assert benchmark_before['passed'] and benchmark_before['stimulus_sha256']==benchmark_after['stimulus_sha256'] and benchmark_before['checksum']==benchmark_after['checksum']
assert benchmark_after['query_count']==4096 and benchmark_after['active_fields']==32 and benchmark_after['repetitions']==3
prior=read('research/target-context-checkpoint.json')
gpu_files=['app/detail_effects'+suffix for suffix in ('.cu','.ptx','-build.json','-sm86.cubin','-sm86.json')]
assert all(sha(name)==prior['source_sha256'][name] for name in gpu_files)
assert read('app/detail_effects-build.json')['abi']=='detail_target_context_v74'
stage='research/ports/v75-enemy-recipients-cpu-stage'
for name,digest in benchmark_before['source_sha256'].items():
    assert any(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest for p in (ROOT/name,ROOT/stage/name)),('baseline source',name)
files=reports+['research/save-enemy-recipients-cpu-checkpoint.py','research/checkpoint_receipts.py','research/enemy-recipients-cpu-stage.json','research/enemy-recipients-reference-before.json','research/enemy-recipient-queries-before.json','research/benchmark-enemy-recipient-queries.py','research/world-bindings-api-fixture.json','research/attack-group-progress.json',
    'app/enemy_recipient_specs.py','app/enemy_recipient_runtime.py','app/effect_spec.py','app/lifecycle_specs.py','app/impact_specs.py',
    'scripts/enemy_recipient_cases.py','scripts/verify-enemy-recipients-reference.py','scripts/verify-common-runtime-unit.py','scripts/verify-compile-stability.py','tests/test_enemy_recipient_runtime.py','tests/test_target_context_runtime.py','tests/test_effect_runtime.py',
    'docs/enemy-recipient-bindings.md','docs/adding-effects.md','README.md']
c=dict(passed=True,objective_complete=False,cpu_only=True,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=stage,
    cpu_recipient_generation_keys_verified=True,canonical_names_unchanged=True,exact_carrier_binding=True,direct_and_named_refresh_generation_checked=True,target_state_query_scoped=True,
    actual_hit_count_target_inheritance_fixed=True,gpu_abi='detail_target_context_v74',gpu_binaries_changed=False,gpu_storage_connected=False,normal_summon_admission=False,character_admission_changed=False,game_rules_verified=False,
    checks=dict(independent_observations=18,lightweight_methods=98,compile_only_supported=187,catalog=203,existing_programs_identical=187,normal_owned_api=True,mode_policy_roundtrip=True),
    efficiency=dict(scope='CPU reference query cache only; not GPU or whole-game speedup',approach='Watch actor generation/liveness per canonical target name; reuse existing per-target query plans while unchanged',query_count=4096,active_fields=32,recipients=3,repetitions=3,before_ms=benchmark_before['median_ms'],after_ms=benchmark_after['median_ms'],cpu_query_speedup=benchmark_after['comparison']['cpu_query_speedup'],overall_speedup_claim=False),
    unchanged_gpu_files={name:sha(name) for name in gpu_files},reused_gpu_evidence='research/target-context-checkpoint.json',
    remaining='GPU per-actor storage/queries/refresh, overlapping multi-recipient independent refresh, periodic and delayed target handles, removal/cleanse lifecycle paths, autonomous aim/outgoing routing and real shot/reach producers.16 standard compile-unaccepted characters and broader world/effect/favorite/equipment/model coverage; final whole-system efficiency remains.')
print(json.dumps(save_checkpoint('research/enemy-recipients-cpu-checkpoint.json','research/ports/v75-enemy-recipients-cpu-verified',c,files)))
