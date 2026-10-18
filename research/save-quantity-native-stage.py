"""Freeze a working quantity interpreter before the efficiency experiment."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/quantity-sources-'+n+'.json' for n in ('native','unit-native-stage','coverage','api-before','control-before')]
r=checked_receipts(reports);assert len(r[reports[0]]['cases'])==9 and r[reports[1]]['tests_run']==56
assert r[reports[2]]['supported']==184 and r[reports[2]]['existing_programs_identical']==183
native=read('app/detail_effects-sm86.json');assert native['abi']=='detail_quantity_sources_v60'
assert native['source_sha256']==sha('app/detail_effects.cu') and native['binary_sha256']==sha('app/detail_effects-sm86.cubin')
base='research/ports/v59-staged-queue-verified'
ancestors=[base]+['research/ports/'+p for p in ('v58-staged-dot-native-stage','v57-source-index-verified','v56-periodic-sources-verified','v55-event-index-verified','v54-target-counters-verified','v53-typed-impacts-verified','v52-resource-limits-verified')]
def previous(path):
    for ancestor in ancestors:
        p=ROOT/ancestor/path
        if p.is_file():return p.read_bytes()
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
inventory.update({'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'})
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()}
changed.update(reports+['research/save-quantity-native-stage.py','research/checkpoint_receipts.py','research/benchmark-normal-search.mjs','research/quantity-sources-api-fixture.json','research/staged-dot-api-fixture.json','research/quantity-sources-contract.json','research/verify-quantity-sources-coverage.py','research/damage-context-dependency-audit.json'])
checkpoint=dict(passed=True,native_stage_only=True,portable_final_pending=True,objective_complete=False,abi=native['abi'],instruction_width=344,archive_base=base,generated_at=datetime.now(timezone.utc).isoformat(),reports=reports,
    checks=dict(shared_primary_cases=9,raw_squads=2,lightweight_methods=56,compile_only_supported=184,existing_programs_identical=183,catalog=203),
    baseline=dict(new_operation_api8_ms=r[reports[3]]['wall_ms'],existing_control_api8_ms=r[reports[4]]['wall_ms']),
    game_rules_verified=False,remaining='Optimize the shared quantity lookup after native semantic proof, then finalize both backends and normal owned API.19 standard compile-unaccepted characters, other effect/world/equipment/favorite/model checks and final whole-system efficiency review remain.')
print(json.dumps(save_checkpoint('research/quantity-sources-native-stage.json','research/ports/v60-quantity-sources-native-stage',checkpoint,changed)))
