from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'scripts/verify-boss-clock-detail.py';archive=ROOT/'research/ports/v31/scripts/verify-boss-clock-detail.py';shutil.copy2(p,archive)
s=p.read_text(encoding='utf-8').replace("e.event in ('start','end')", "e.event in ('start','end','dispel')").replace('opens=[r.opens for r in runs])','opens=[r.opens for r in runs],defense=enemy["def"],dispelled_mask=sum(1<<i for i,r in enumerate(runs) if r.dispelled))');p.write_text(s,encoding='utf-8')
p=ROOT/'app/detail_effects.cu';s=p.read_text(encoding='utf-8').replace('dst[39]=stat(c,e,ne,s,0,12,full);','');p.write_text(s,encoding='utf-8')
p=ROOT/'app/detail_gpu.py';s=p.read_text(encoding='utf-8');needle="  if len(p['chars'])!=5 or len(p['effects'])>NE:raise ValueError('Invalid detailed program size')"
assert needle in s;s=s.replace(needle,needle+'''
  w=p.get('world',[0]*WP)
  for i in range(int(w[0])):
   row=int(w[WB+i*BW+78])
   if row>=0:
    if row>=len(p['effects']):raise ValueError('Boss effect row exceeds definitions')
    q=p['effects'][row]
    if w[WB+i*BW]!=5 or q[1]!=0 or q[2]!=12 or q[4]!=4:raise ValueError('Boss effect row has incompatible semantics')''');p.write_text(s,encoding='utf-8')
