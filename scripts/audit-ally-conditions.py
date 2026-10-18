"""Independent pinned-CPU outputs for authored HP/composition stimuli."""
import hashlib, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ally_conditions','scripts/verify-ally-conditions-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
rows=[]
for name,names,effects,commands,expected in v.primitives():
    program=v.oracle.program(v.oracle.characters(names),effects)
    stats={n:{'atk':100000+i*1234,'hp':1000000,'def':1000} for i,n in enumerate(names)}
    script=[];index=0
    for t,event,who in commands:
        script.append([t,2 if event=='query' else 0,0 if event=='query' else event,who,-1,index if event=='query' else -1,0,0])
        if event=='query':index+=1
    cpu,_=v.cpu_oracle(program,script,[31784,50],stats)
    atk=[q[0] for q in cpu]
    if expected is not None:assert atk==expected,(name,atk,expected)
    rows.append(dict(name=name,names=names,effects=effects,stimulus=script,cpu_atk=atk))
assert any(any(value>0 for value in r['cpu_atk']) for r in rows)
assert any(all(value==0 for value in r['cpu_atk']) for r in rows)
case=next(r for r in rows if r['name']=='hp-50-50-order0')
assert case['cpu_atk']==[0,0,23,0,0,0,0,0,0,0],case
files=['scripts/audit-ally-conditions.py','scripts/verify-ally-conditions-detail.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,passed=True,cases=rows,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
(ROOT/'research/detail-ally-conditions-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,cpu_cases=len(rows),recipient_boundary=case['cpu_atk'])))
