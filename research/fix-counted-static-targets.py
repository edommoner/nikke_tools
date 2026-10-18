"""Preserve CPU prefix-before-down-filter for class and innate-charge targets."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'research/staging/v34';dest=ROOT/'research/ports/v34-before-counted-target-fix';assert not dest.exists()
for p in base.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:
        out=dest/'stage'/p.relative_to(base);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
for name in ('native','ptx'):
    src=ROOT/f'research/detail-survival-b1-{name}-full.json';r=json.loads(src.read_text(encoding='utf-8'));assert not r['passed'] and r['cases'][-1]['name']=='count-limited-living-class'
    shutil.copy2(src,dest/src.name)
path=base/'app/detail_gpu.py';s=path.read_text(encoding='utf-8')
old="   if prefix=='allies_class':selected=[i for i,ch in enumerate(chars) if ch['_weapon'].get('class')==parts[1]];live_limit=int(parts[2]) if len(parts)>2 else None"
assert old in s;s=s.replace(old,"   if prefix=='allies_class':\n    selected=[i for i,ch in enumerate(chars) if ch['_weapon'].get('class')==parts[1]]\n    if len(parts)>2:selected=selected[:int(parts[2])]")
old="selected.sort(key=lambda i:-chars[i]['_weapon']['charge_time']);live_limit=int(parts[1]);q[141]=1;"
assert old in s;s=s.replace(old,"selected.sort(key=lambda i:-chars[i]['_weapon']['charge_time']);selected=selected[:int(parts[1])];q[141]=1;")
path.write_text(s,encoding='utf-8')
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,files={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()}),indent=2)+'\n',encoding='utf-8')
print('Fixed only the staged compiler. Class/innate-charge prefixes filter down after truncation; code+weapon leftmost retains living-first behavior. CUDA rebuild is unnecessary.')
