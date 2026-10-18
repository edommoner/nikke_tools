"""Standard inventory plus only the newly admitted character's favorite inputs."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
from detail_coverage import a,coverage,body_for
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/detail_coverage.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
report=coverage();stages=[]
for stage in range(4):
    body=body_for(['아인','리타','크라운','앨리스','모더니아'],8,True);body['profile']['chars']['아인']['favorite_stage']=stage
    compiled=a.evaluate({**body,'_compile_gpu_detail':True});assert compiled['program']['periodic_source_estimated'];stages.append(stage)
old=json.loads((ROOT/'research/ports/v54-target-counters-verified/research/target-counters-coverage.json').read_text(encoding='utf-8'))
supported=lambda value:{r['character'] for r in value['results'] if r['supported']}
assert supported(old)<=supported(report) and supported(report)-supported(old)=={'아인'}
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report.update(passed=True,compile_only=True,newly_accepted=['아인'],new_character_favorite_stages=stages,source_stable=True,source_sha256=before)
(ROOT/'research/periodic-sources-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,supported=report['supported'],characters=report['characters'],favorite_contexts=len(stages))))
