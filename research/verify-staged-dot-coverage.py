"""Standard compiler inventory and new staged operation data inputs."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
from detail_coverage import a,coverage,body_for
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/detail_coverage.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};report=coverage();stages=[]
for stage in range(4):
    body=body_for(['사쿠라 : 블룸 인 서머','리타','크라운','앨리스','모더니아'],8,True);body['profile']['chars']['사쿠라 : 블룸 인 서머']['favorite_stage']=stage
    compiled=a.evaluate({**body,'_compile_gpu_detail':True});assert sum(row[340]>0 for row in compiled['program']['effects'])==1;stages.append(stage)
prior=json.loads((ROOT/'research/ports/v57-source-index-verified/research/source-index-coverage.json').read_text(encoding='utf-8'))
supported=lambda r:{row['character'] for row in r['results'] if row['supported']}
assert supported(prior)<=supported(report) and supported(report)-supported(prior)=={'사쿠라 : 블룸 인 서머'}
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report.update(passed=True,compile_only=True,new_character_inputs=stages,source_stable=True,source_sha256=before)
(ROOT/'research/staged-dot-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,supported=report['supported'],characters=report['characters'])))
