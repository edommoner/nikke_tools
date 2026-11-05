"""Observe original incoming attacks under the unchanged full battle comparer."""
import copy
from unittest.mock import patch
from calculator import timeline
from portable_coordinate_original_cases import prepare_case as original_case
from portable_add_attack_battle_wire import compile_battle
from world_logical_geometry_full_native import observe as logical_battle


def prepare_case(row):
    case,prepared=original_case(row)
    case.update(logical_geometry=copy.deepcopy(row['logical_geometry']),add_attack_contract=copy.deepcopy(row['contract']),sampled_groups=True)
    words,meta,bindings,scene=compile_battle(prepared,case['logical_geometry'])
    return words,(case,meta,bindings,scene)


def observe(domain):
    records=[];old=timeline.BossScript;bindings=domain[2]
    lookup={b.label:i for i,b in enumerate(bindings)}
    class Boss(old):
        def begin_frame(self,t,enemy):
            previous=getattr(self,'_add_attack_observed_time',None)
            events=super().begin_frame(t,enemy)
            if previous!=t:
                self._add_attack_observed_time=t
                from calculator.boss_pattern import ADD_PREFIX
                for hit in self.attacks:
                    node=self._run_by_id[hit.pattern].p.idx
                    slot=lookup[ADD_PREFIX+hit.source] if hit.source else 0
                    generation=self._runs[node].opens if slot else 1
                    records.append(dict(time=t,node=node,slot=slot,generation=generation,index=hit.index))
            return events
    with patch.object(timeline,'BossScript',Boss):native=logical_battle(domain)
    native['queued_add_attacks']=records
    return native
