"""Freeze native functional proof before the required efficiency experiment."""
import json,re
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/staged-dot-native.json','research/staged-dot-unit-stage.json','research/staged-dot-coverage.json','research/runtime-wiring.json','research/staged-dot-pool-before.json','research/staged-dot-api-before.json']
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==9 and all(c['passed'] for c in r[reports[0]]['cases'])
assert r[reports[1]]['tests_run']==53 and r[reports[2]]['supported']==183
assert len(r[reports[4]]['samples'])==3 and r[reports[5]]['cache_hits']==0 and r[reports[5]]['candidates']==8
native=read('app/detail_effects-sm86.json');assert native['abi']=='detail_staged_dot_v58' and native['source_sha256']==sha('app/detail_effects.cu') and native['binary_sha256']==sha('app/detail_effects-sm86.cubin')
base='research/ports/v57-source-index-verified'
inventory={p.relative_to(ROOT).as_posix() for directory,pattern in [('app','*.py'),('scripts','*.py'),('tests','*.py'),('docs','*.md')] for p in (ROOT/directory).glob(pattern) if p.is_file()}|{'README.md','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'}
def previous(path):
    for root in (base,'research/ports/v56-periodic-sources-verified','research/ports/v55-event-index-verified','research/ports/v54-target-counters-verified','research/ports/v53-typed-impacts-verified','research/ports/v52-resource-limits-verified'):
        p=ROOT/root/path
        if p.is_file():return p.read_bytes()
changed={p for p in inventory if previous(p)!=(ROOT/p).read_bytes()};changed.update(reports)
changed.update({'research/save-staged-dot-native-stage.py','research/checkpoint_receipts.py','research/verify-staged-dot-unit.py','research/verify-staged-dot-coverage.py','research/benchmark-staged-dot.py','research/benchmark-normal-search.mjs','research/staged-dot-api-fixture.json','research/ramped-dot-dependency-audit.json','research/staged-dot-cpu-prior.json','research/staged-dot-cpu-current.json'})
checkpoint=dict(passed=True,native_stage_only=True,portable_final_pending=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),abi=native['abi'],instruction_width=344,
    archive_base=base,checks=dict(shared_quantities=6,autonomous_squads=3,lightweight_methods=53,compile_only_supported=183,catalog=203),reports=reports,
    baseline=dict(pool64_median_kernel_ms=r[reports[4]]['median_kernel_ms'],normal_owned8_ms=r[reports[5]]['wall_ms']),
    scope='Generation-bound staged applications, latched count and scoped damage-stack override, followed by periodic damage. Native functional stage before efficiency experiment; not final portable acceptance.',
    game_rules_verified=False,remaining='Attempt shared queue efficiency, then final native/PTX bundle, related controls and normal API.20 standard compile-unaccepted characters remain, plus effect/world/model review and the final whole-system efficiency review after all-character support.')
print(json.dumps(save_checkpoint('research/staged-dot-native-stage.json','research/ports/v58-staged-dot-native-stage',checkpoint,changed)))
