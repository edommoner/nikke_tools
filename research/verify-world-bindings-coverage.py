"""Bind identities without changing existing effects, weapons or world prefix."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
from detail_coverage import a,body_for,coverage
import detail_gpu as g
old_source=ROOT/'research/ports/v69-mode-inputs-native-stage/app/detail_gpu.py'
old_world_source=ROOT/'research/ports/v52-resource-limits-verified/app/detail_boss.py'
prior_path=ROOT/'research/ports/v69-mode-inputs-verified/research/mode-inputs-coverage.json'
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/detail_coverage.py',ROOT/'data/engine-effect-overrides.json',old_source,old_world_source,prior_path]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('world_binding_old_compiler',old_source);old_world=load('world_binding_old_world',old_world_source);old.compile_world=old_world.compile_world
prior=json.loads(prior_path.read_text(encoding='utf-8'));report=coverage();accepted=lambda r:{row['character'] for row in r['results'] if row['supported']}
assert accepted(report)==accepted(prior)
for name in sorted(accepted(report)):
    names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4];body=body_for(names)
    current=a.evaluate({**body,'_compile_gpu_detail':True});previous=old.compile_full(current['prepared'],lambda c:current['base_stats'][c['name']],body,current['policy'],current['requested_policy'])
    new=dict(current['program']);oldp=dict(previous['program']);nw=new.pop('world');ow=oldp.pop('world')
    assert new==oldp and nw[:len(ow)]==ow,name
    assert old.weapon_rows(oldp['chars'],previous['base_stats'])==g.weapon_rows(new['chars'],current['base_stats']),name
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report.update(passed=True,compile_only=True,existing_programs_identical=len(accepted(report)),old_world_prefix_identical=True,weapon_rows_identical=True,character_admission_changed=False,source_stable=True,source_sha256=before)
(ROOT/'research/world-bindings-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,supported=report['supported'],characters=report['characters'])))
