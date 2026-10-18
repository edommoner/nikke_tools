"""Keep all186 existing programs identical while manual mode input is pending."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for,coverage
old_source=ROOT/'research/ports/v67-named-allies-verified/app/detail_gpu.py'
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/detail_coverage.py',ROOT/'data/engine-effect-overrides.json',old_source]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
prior=json.loads((ROOT/'research/ports/v67-named-allies-verified/research/named-allies-coverage.json').read_text(encoding='utf-8'))
report=coverage();accepted=lambda r:{x['character'] for x in r['results'] if x['supported']}
assert accepted(report)==accepted(prior)
loader=importlib.util.spec_from_file_location('before_mode_compiler',old_source);old=importlib.util.module_from_spec(loader);loader.loader.exec_module(old)
for name in sorted(accepted(prior)):
    names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4];body=body_for(names)
    current=a.evaluate({**body,'_compile_gpu_detail':True});previous=old.compile_full(current['prepared'],lambda char:current['base_stats'][char['name']],body,current['policy'],current['requested_policy'])
    assert current['program']==previous['program'],name
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report.update(passed=True,compile_only=True,existing_programs_identical=len(accepted(prior)),source_stable=True,source_sha256=before)
(ROOT/'research/mode-commands-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,supported=report['supported'],characters=report['characters'])))
