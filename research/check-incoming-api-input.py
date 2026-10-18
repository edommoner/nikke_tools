import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('api_input_check',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
b=json.loads((ROOT/'research/detail-incoming-api-fixture.json').read_text(encoding='utf-8'))
c=v.v.a.evaluate(b);compiled=v.v.a.evaluate({**b,'_compile_gpu_detail':True})
assert c['incoming_hits'] and any(h['damage']>1 for h in c['incoming_hits'])
assert not any(h['down'] for h in c['incoming_hits'])
print(json.dumps(dict(cpu_total=c['total_damage'],incoming_hits=len(c['incoming_hits']),down=False,nontrivial_damage=True,compiled_effects=len(compiled['program']['effects']),gpu_execution_verified=False)))
