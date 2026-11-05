"""Local native carrier subtype with explicitly declared factor5 semantics."""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from destructible_damage_policy import manager_type,resolve
from timer_registry_cases import NAMES

def observe(case):
    class Literal(BuffManager):
        def _register_all(self):
            self._effects=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])];self._build_notify_index()
    cls=manager_type(Literal)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    manager=cls(chars,state=dict(base_stats={n:dict(atk=1000,hp=10000,**{'def':100}) for n in NAMES},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={}))
    for _ in range(case.get('activations',1)):
        for name in NAMES:manager.notify('battle_start',0.,name)
    answer=resolve(manager,NAMES[case['attacker']],kind=case['kind'],base_attack=case['base_attack'],weapon=engine_worker.META[NAMES[case['attacker']]],defense=case['defense'],coefficient=case['coefficient'],when=case['when'])
    return answer,[]
