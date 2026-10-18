import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'research/ports/v33-before-cover-ranking-fix'
assert not dest.exists()
paths=['app/detail_gpu.py','app/detail_boss.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-incoming-detail.py','research/detail-incoming-initial-quick.json','research/detail-incoming-initial-quick.log','research/detail-incoming-initial-full.json','research/detail-incoming-initial-full.log']
for p in paths:
 target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
(dest/'archive-manifest.json').write_text(json.dumps(dict(verified_step=False,objective_complete=False,reason='Real Anis squad diverged at frame900 (15s): lowest-cover-HP recipients were still statically selected. Totals and incoming hits happened to match; per-frame/final cover witnesses caught the error.',files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}),indent=2)+'\n',encoding='utf-8')
print('Preserved initial v33 build and failed whole-squad evidence.')
