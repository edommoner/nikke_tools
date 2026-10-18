"""Existing 187 standard programs stay identical; source admission stays closed."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
from detail_coverage import a,body_for,coverage
import detail_gpu as g
base=ROOT/'research/ports/v70-world-bindings-native-stage'
sources=[base/'app/detail_gpu.py',base/'app/detail_boss.py']
prior_path=ROOT/'research/ports/v70-world-bindings-verified/research/world-bindings-coverage.json'
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/detail_coverage.py',ROOT/'data/engine-effect-overrides.json',prior_path]+sources
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('summon_old_compiler',sources[0]);old_world=load('summon_old_world',sources[1]);old.compile_world=old_world.compile_world
prior=json.loads(prior_path.read_text(encoding='utf-8'));report=coverage();accepted=lambda r:{row['character'] for row in r['results'] if row['supported']}
assert accepted(prior)==accepted(report)
for name in sorted(accepted(report)):
    names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4];body=body_for(names)
    current=a.evaluate({**body,'_compile_gpu_detail':True});previous=old.compile_full(current['prepared'],lambda c:current['base_stats'][c['name']],body,current['policy'],current['requested_policy'])
    assert current['program']==previous['program'],name
    assert g.weapon_rows(current['program']['chars'],current['base_stats'])==old.weapon_rows(previous['program']['chars'],previous['base_stats']),name
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report.update(passed=True,compile_only=True,existing_programs_identical=len(accepted(report)),weapon_rows_identical=True,normal_summon_admission=False,source_stable=True,source_sha256=before)
(ROOT/'research/summon-sources-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,supported=report['supported'])))
