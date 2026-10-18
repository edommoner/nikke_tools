"""Preserve the source-bound v32 checkpoint before the next port changes it."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checkpoint='research/detail-boss-buffs-checkpoint.json'
c=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'))
assert c['passed'] and not c['objective_complete'] and c['abi']=='detail_boss_buffs_v32'
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert all(sha(p)==h for p,h in c['source_sha256'].items())
assert all(sha(p)==h for p,h in c['report_sha256'].items())
paths=set(c['source_sha256'])|set(c['report_sha256'])|{checkpoint,'research/detail-expansion-next.json','research/detail-boss-buffs-node-tests.log','research/detail-boss-buffs-phase-final-verification.log','research/detail-boss-buffs-phase-final-normal-tests.log','research/detail-incoming-target-transitions-cpu-reference.json','research/detail-incoming-damage-cpu-reference.json','scripts/audit-incoming-target-transitions.py','scripts/audit-incoming-damage.py','research/detail-boss-buffs-ui-session-verification.json','research/detail-boss-buffs-ui-fixture.json','research/detail-boss-buffs-api-fixture.json','scripts/verify-boss-buffs-ui-session.mjs','research/detail-boss-buffs-rng-30.json','research/detail-boss-buffs-rng-30-full-end-damage.json','research/detail-mode-charge-restore-probe.json'}
dest=ROOT/'research/ports/v32'
assert not dest.exists(),'Preserved archives are immutable; inspect existing archive instead.'
for p in sorted(paths):
 target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(abi=c['abi'],objective_complete=False,files={p:sha(p) for p in sorted(paths)}),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(archived=str(dest),files=len(paths),objective_complete=False)))
