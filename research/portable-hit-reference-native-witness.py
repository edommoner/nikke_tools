"""Run the pinned timeline's actual hit-count AST in the independent BM/boss observer.
Only native hit selection is projected; no GPU state or CPU trace is GPU input.
"""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
native=ROOT/'research/upstream/nikke-calc-master/calculator/timeline.py';raw=native.read_text();tree=ast.parse(raw)
function=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_handle_damage_eff')
indices=[i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='gauge_ref' for t in n.targets)]
assert len(indices)==1;i=indices[0]
assert isinstance(function.body[i-1],ast.Assign) and function.body[i-1].targets[0].id=='hit_count'
assert isinstance(function.body[i+1],ast.If) and isinstance(function.body[i+1].test,ast.Name) and function.body[i+1].test.id=='gauge_ref'
selected=copy.deepcopy(function.body[i-1:i+2])
stub=ast.parse('def native_hits(eff,caster,bm):\n stat=eff.get("stat","damage")\n stat_parts=stat.split(":")\n base_stat=stat_parts[0]\n return 0\n')
fn=stub.body[0];ret=ast.Return(value=ast.Name(id='hit_count',ctx=ast.Load()));ast.copy_location(ret,selected[-1]);fn.body=fn.body[:-1]+selected+[ret];fn.end_lineno=selected[-1].end_lineno;fn.end_col_offset=selected[-1].end_col_offset
namespace={};exec(compile(ast.fix_missing_locations(stub),str(native),'exec'),namespace);native_hits=namespace['native_hits']
# Replace just the independently copied selector in the component observer.
# Its BuffManager, effects, notifications, damage math and enemy routing remain
# original native components; the replacement is the exact pinned AST above.
p=ROOT/'scripts/portable_enemy_oracle.py';observer=ast.parse(p.read_text());damage=next(n for n in ast.walk(observer) if isinstance(n,ast.FunctionDef) and n.name=='damage')
selectors=[i for i,n in enumerate(damage.body) if isinstance(n,ast.If) and ast.unparse(n.test)=="effect.get('hit_count_gauge_ref')"]
assert len(selectors)==1
replacement=ast.parse('hits=_pinned_native_hit_count(effect,caster,bm)').body[0];ast.copy_location(replacement,damage.body[selectors[0]]);damage.body[selectors[0]]=replacement
projected=ast.unparse(observer);ns={'__name__':'pinned_hit_component','_pinned_native_hit_count':native_hits};exec(compile(ast.fix_missing_locations(observer),str(p),'exec'),ns)
fixture=ROOT/'tests/fixtures/portable-hit-references.json';cases=json.loads(fixture.read_text())['cases'];rows=[]
for case in cases:
 actual=ns['observe'](case)
 for got,expected in zip(actual['queries'],case['expected_queries']):assert got['damage']==expected['damage'],case['name']
 rows.append(dict(name=case['name'],passed=True,native=actual))
paths=[native,p,fixture,Path(__file__).resolve()]
report=dict(passed=True,cases=rows,native_hit_count_AST=ast.unparse(ast.Module(body=selected,type_ignores=[])),native_hit_count_AST_sha256=hashlib.sha256(ast.dump(ast.Module(body=selected,type_ignores=[]),include_attributes=False).encode()).hexdigest(),projected_observer_sha256=hashlib.sha256(projected.encode()).hexdigest(),source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},cpu_trace_used_as_gpu_input=False,scope='Exact hit-count block from pinned native timeline with original BuffManager.ref_count, damage and boss components; not full battle certification')
(ROOT/'research/portable-hit-reference-native-witness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Pinned native hit-count AST verified',len(rows),'cases')
