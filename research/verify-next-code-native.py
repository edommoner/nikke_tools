"""Inspect native code predicates for the next connection; not GPU certification."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES
class BM(BuffManager):
    def _register_all(self):self._effects=[];self._build_notify_index()
    def char_effects(self,name):return []
chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=1000,**{'def':0}) for n in NAMES},enemy={}))
codes=['작열','수냉','풍압','전격','철갑','','unknown:code',' 전격 ']
rows=[]
for enemy in [None]+codes:
    bm.state['enemy']={} if enemy is None else dict(code=enemy)
    for predicate in codes:
        conditions=['target_code:'+predicate]
        expected=not enemy or enemy==predicate
        for owner in NAMES:
            activation=bm._condition_ok(conditions,owner,0)
            runtime_body=bm._runtime_condition_ok(conditions,owner,owner,'__enemy__',0)
            runtime_add=bm._runtime_condition_ok(conditions,owner,owner,'__enemy__:add:1',0)
            assert activation==runtime_body==runtime_add==expected
            rows.append(dict(enemy_code=enemy,predicate_code=predicate,owner=NAMES.index(owner),activation=activation,runtime_body=runtime_body,runtime_add=runtime_add))
path=R/'research/portable-next-code-native.json'
path.write_text(json.dumps(dict(passed=True,cases=rows,case_count=len(rows),native_methods=['BuffManager._condition_ok','BuffManager._runtime_condition_ok'],gpu_execution_performed=False,portable_host_admission_changed=False,scope='Direct native predicate method probes only; not a battle, code-input implementation or GPU verification.',source_sha256={'research/verify-next-code-native.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'research/upstream/nikke-calc-master/calculator/buff_manager.py':hashlib.sha256((R/'research/upstream/nikke-calc-master/calculator/buff_manager.py').read_bytes()).hexdigest()}),ensure_ascii=False,indent=2)+'\n')
print('Next code native probes',len(rows),'passed; GPU/admission remain unimplemented')
