import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('incoming_compile',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
rows=[]
for name,b,extra in v.fixtures():
 with v.context(name,extra):
  try:
   p=v.v.a.evaluate({**b,'_compile_gpu_detail':True});r=dict(name=name,compiled=True,effects=len(p['program']['effects']))
  except Exception as e:r=dict(name=name,compiled=False,error=repr(e))
 rows.append(r)
(ROOT/'research/detail-incoming-compile.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(cases=len(rows),accepted=sum(r['compiled'] for r in rows),failures=[r for r in rows if not r['compiled']]),ensure_ascii=True))
