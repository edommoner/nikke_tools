"""Close autonomous mode input only after numerical and normal-path evidence."""
import hashlib,json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint

reports=['research/mode-inputs-'+name+'.json' for name in ('native','ptx','unit','coverage','mode-controls','related-native','batch-native','owned-api','after-api','ui')]+['research/runtime-wiring.json']
r=checked_receipts(reports)
for path in reports[:2]:
    assert len(r[path]['cases'])==8
    for row in r[path]['cases']:
        assert row['cpu_mode_shots']==row['gpu_mode_shots']
        assert (row['gpu_mode_shots']>0)==row['mode_expected']
        assert row['workspace_bytes']==1216840
assert r[reports[2]]['tests_run']==83
assert r[reports[3]]['supported']==187 and r[reports[3]]['existing_programs_identical']==186
assert r[reports[3]]['old_weapon_words_identical']
assert len(r[reports[4]]['cases'])==2 and len(r[reports[5]]['cases'])==25
assert r[reports[6]]['batch_squads']==10 and r[reports[6]]['previous_squads_preserved']==8
assert r[reports[7]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[7]]['mode_policy_roundtrip']['passed']
native=read('app/detail_effects-sm86.json');portable=read('app/detail_effects-build.json')
assert native['abi']==portable['abi']=='detail_mode_inputs_v69'
assert native['source_sha256']==portable['source_sha256']==sha('app/detail_effects.cu')
assert native['binary_sha256']==sha('app/detail_effects-sm86.cubin') and portable['ptx_sha256']==sha('app/detail_effects.ptx')
base='research/ports/v69-mode-inputs-native-stage'
before=read('research/mode-inputs-before-api.json');after=r[reports[8]]
assert before['passed'] and before['candidates']==after['candidates']==8 and before['cache_hits']==after['cache_hits']==0
assert [{k:v for k,v in row.items() if k!='compute'} for row in before['results']]==[{k:v for k,v in row.items() if k!='compute'} for row in after['results']]
for name,digest in before['source_sha256'].items():
    origin=ROOT/base/name if name in ('app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json') else ROOT/name
    assert hashlib.sha256(origin.read_bytes()).hexdigest()==digest,('before provenance',name)
ancestors=[base]+['research/ports/'+name for name in ('v68-mode-commands-verified','v68-mode-commands-native-stage','v67-named-allies-verified','v67-target-scopes-verified','v67-target-scopes-native-stage','v66-attack-groups-foundation-verified','v65-attack-groups-native-stage','v64-attack-groups-cpu-plans','v63-attack-groups-cpu-stage','v62-resource-marker-verified','v60-quantity-sources-verified','v60-quantity-sources-native-stage','v59-staged-queue-verified','v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        source=ROOT/ancestor/path
        if source.is_file():return source.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md'),('web','*.js'),('web','*.html')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_effects.ptx','app/detail_effects-build.json'})
changed={name for name in inventory if previous(name)!=(ROOT/name).read_bytes()}
changed.update(reports+['research/save-mode-inputs-checkpoint.py','research/checkpoint_receipts.py','research/verify-mode-command-controls.py','research/verify-mode-inputs-coverage.py','research/verify-event-index-batch.py','research/mode-inputs-before-api.json','research/mode-inputs-native-stage.json','research/attack-group-progress.json','research/mode-inputs-api-fixture.json','research/mode-inputs-ui-fixture.json','research/benchmark-normal-search.mjs'])
c=dict(passed=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base=base,reports=reports,abi=native['abi'],instruction_width=344,character_width=169,workspace_bytes=1216840,
    autonomous_manual_reload_input_connected=True,cpu_reload_entry_initialization_fixed=True,character_admission_changed=True,game_rules_verified=False,
    checks=dict(mode_input_cases_per_backend=8,lightweight_methods=83,existing_mode_integrations=2,existing_ordering_cases=25,heterogeneous_squads=10,normal_owned_api=True,normal_ui=True,compile_only_supported=187,catalog=203,existing_programs_identical=186),
    efficiency=dict(approach='Use existing event19 CSR for conditional reload definitions, preserving condition and registration order',normal_api8_before_ms=before['wall_ms'],normal_api8_after_ms=after['wall_ms'],single_comparison_speedup=before['wall_ms']/after['wall_ms'],repeated_median=False,overall_speedup_claim=False),
    remaining='16 standard compile-unaccepted characters and broader world/effect/favorite/equipment/model coverage. Connect actual weapon landing batch boundaries, GPU actor world and per-target selectors. Require nonzero raw multi_hit activation. After all-character support, profile primary calculation and review overall efficiency.')
print(json.dumps(save_checkpoint('research/mode-inputs-checkpoint.json','research/ports/v69-mode-inputs-verified',c,changed)))
