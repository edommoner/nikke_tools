"""CPU B1 ally composition checks include down members; preserve that rule."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'research/staging/v34';dest=ROOT/'research/ports/v34-before-b1-ally-fix';assert not dest.exists()
for p in base.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:
        out=dest/'stage'/p.relative_to(base);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
for name in ('research/probe-dead-burst-ally-condition.py','research/detail-dead-b1-ally-probe.json','research/detail-dead-b1-ally-probe.log'):
    out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,out)
path=base/'app/detail_effects.cu';s=path.read_text(encoding='utf-8')
old='if(k!=owner&&!(s->down_mask&(1<<k))&&s->burst_stage[k]==1)has=1;'
assert s.count(old)==1;s=s.replace(old,'if(k!=owner&&s->burst_stage[k]==1)has=1;')
path.write_text(s,encoding='utf-8')
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,files={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()}),indent=2)+'\n',encoding='utf-8')
print('Archived the B1 predicate mismatch and patched only the staged composition predicate.')
