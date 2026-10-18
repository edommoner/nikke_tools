"""Keep the measured 1,438-event long fixture in scope; grow the bounded log."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['app/detail_boss.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json']:
    dst=ROOT/'research/ports/v31-clock-initial'/name;assert not dst.exists()
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
for name,old,new in [('app/detail_boss.py','BP,BL,BW,BH,BLOG,BQ=32,8,80,512,1024,1024','BP,BL,BW,BH,BLOG,BQ=32,8,80,512,4096,1024'),('app/detail_effects.cu','#define BLOG 1024','#define BLOG 4096')]:
    p=ROOT/name;t=p.read_text(encoding='utf-8');assert old in t;p.write_text(t.replace(old,new),encoding='utf-8')
print('Boss log capacity 4096; per-node history remains independently bounded at 512')
