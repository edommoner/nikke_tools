"""Preserve the failing candidate and restore CPU dead-candidate wait semantics."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];stage=ROOT/'research/staging/v34'
dest=ROOT/'research/ports/v34-before-burst-wait-fix';assert not dest.exists()
for p in stage.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:
        target=dest/'stage'/p.relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
raw=(ROOT/'research/detail-survival-normal-tests.log').read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig',errors='replace')
rows=[]
for line in text.splitlines():
    if line.startswith('{'):
        try:r=json.loads(line)
        except ValueError:continue
        if r.get('passed') is False:rows.append(r)
assert len(rows)==4,rows
(dest/'normal-partial.log').write_bytes(raw)
(dest/'failure.json').write_text(json.dumps(dict(passed=False,objective_complete=False,normal_suite_complete=False,cases=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path=stage/'app/detail_effects.cu';s=path.read_text(encoding='utf-8')
old='candidate_stage[i]=(s->down_mask&(1<<i))?0:s->burst_stage[i];'
assert old in s;s=s.replace(old,'candidate_stage[i]=s->burst_stage[i];')
old=' if(s->phase>=1&&s->phase<=3&&s->action>=1e29){for(int who=0;who<5;who++)if(candidate_stage[who]==s->phase||candidate_stage[who]==4){s->action=t;break;}}\n'
assert old in s;s=s.replace(old,' // A stage with no candidates stays permanently blocked. Dead candidates\n // remain in the wait set, but cannot cast; revival needs no special restart.\n')
old='earliest=mn(earliest,s->ready[i]);if(stat(c,e,ne,s,i,28,0)>0)continue;'
assert old in s;s=s.replace(old,'earliest=mn(earliest,s->ready[i]);if(stat(c,e,ne,s,i,28,0)>0||(s->down_mask&(1<<i)))continue;')
path.write_text(s,encoding='utf-8')
(dest/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,files={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()}),indent=2)+'\n',encoding='utf-8')
print('Preserved the four failures and patched staged candidate/wait semantics; production code unchanged.')
