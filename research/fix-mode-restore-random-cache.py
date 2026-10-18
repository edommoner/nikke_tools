"""Retain CPU's already-computed buff dictionary when restoring normal weapons."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_boss.py','scripts/verify-boss-buffs-detail.py','scripts/verify-boss-clock-detail.py','research/detail-normal-acceptance.json','research/detail-boss-buffs-verification.json','research/detail-boss-buffs-rng-30.json','research/detail-boss-buffs-long-verification.log','research/detail-boss-buffs-fb-end-rng-cpu.json']
for f in files:
 dst=ROOT/'research/ports/v32-before-mode-cache-fix'/f;assert not dst.exists(),dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,dst)
p=ROOT/'app/detail_effects.cu';s=p.read_text(encoding='utf-8')
old='s->charge_full[who]=-1;s->hold_release[who]=-1;s->charging[who]=0;invalidate(s);}'
new='s->charge_full[who]=-1;s->hold_release[who]=-1;s->charging[who]=0;}'
assert s.count(old)==1;s=s.replace(old,new)
needle=' if(mode<0&&prior>=0)'
assert needle in s;s=s.replace(needle,' // BuffManager already invalidated when the mode ended. Restoring CharState\n // fields preserves the CPU buff query snapshot, including random recipients.\n'+needle)
p.write_text(s,encoding='utf-8')
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'));r['current_work'].update(status='rebuilding_mode_restore_cache_fix',first_rng_divergence_time=20.53333333333345,diagnosis='GPU invalidated all cached recipient queries a second time when restoring CharState weapon fields; CPU invalidates only at end_weapon_change.',active_verifications={});p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
