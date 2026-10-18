"""Compile inventory; deliberately separate from raw-squad numerical proof."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,coverage,body_for
old_source=ROOT/'research/ports/v62-resource-marker-verified/app/detail_gpu.py'
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/detail_coverage.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json',old_source]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};report=coverage()
previous=json.loads((ROOT/'research/ports/v62-resource-marker-verified/research/resource-marker-coverage.json').read_text(encoding='utf-8'))
accepted=lambda r:{x['character'] for x in r['results'] if x['supported']}
assert accepted(previous)==accepted(report)
# Verify all previously accepted programs remain identical despite the new gated diagnostic group forms.
loader=importlib.util.spec_from_file_location('marker_previous_compiler',old_source);old=importlib.util.module_from_spec(loader);loader.loader.exec_module(old)
unchanged=[]
for name in sorted(accepted(previous)):
    names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
    body=body_for(names);current=a.evaluate({**body,'_compile_gpu_detail':True})
    prior=old.compile_full(current['prepared'],lambda char:current['base_stats'][char['name']],body,current['policy'],current['requested_policy'])
    assert current['program']==prior['program'],name
    unchanged.append(name)
stages=[]
for stage in range(4):
    body=body_for(['네온 : 비전 아이','리타','크라운','앨리스','모더니아'],8,True);body['profile']['chars']['네온 : 비전 아이']['favorite_stage']=stage
    p=a.evaluate({**body,'_compile_gpu_detail':True})['program'];assert sum(r[1]==4 and r[64]>=0 for r in p['effects'])==1;stages.append(stage)
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report.update(passed=True,compile_only=True,new_character_inputs=stages,existing_programs_identical=len(unchanged),source_stable=True,source_sha256=before)
(ROOT/'research/attack-groups-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,supported=report['supported'],characters=report['characters'])))
