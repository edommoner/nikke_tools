"""Match CPU invalidation before end callbacks and preserve callback snapshots."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','research/detail-boss-buffs-rng-30.json','research/detail-boss-buffs-rng-30-full-end-damage.json','research/detail-mode-charge-restore-probe.json']
for f in files:
 p=ROOT/'research/ports/v32-mode-cache-only'/f;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f,p)
p=ROOT/'app/detail_effects.cu';s=p.read_text(encoding='utf-8')
old='s->phase=0;*full=0;code|=log_burst(s,t,5,-1);';new='s->phase=0;*full=0;invalidate(s);s->cached_full=0;code|=log_burst(s,t,5,-1);'
assert s.count(old)==1;s=s.replace(old,new)
old='s->gauge=t+regen;s->cycle++;s->cast_mask=0;invalidate(s);';new='s->gauge=t+regen;s->cycle++;s->cast_mask=0;'
assert s.count(old)==1;s=s.replace(old,new)
needle=' if(s->phase==5&&t>=s->fb_end-1e-9){';s=s.replace(needle,' // CPU changes full_burst and invalidates before callbacks. Clearing the cast\n // flags afterwards retains any complete buff dictionaries queried by them.\n'+needle)
p.write_text(s,encoding='utf-8')
