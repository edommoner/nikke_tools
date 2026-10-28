"""Passive canonical retirement receipts alongside the existing full observer."""
import copy
from unittest.mock import patch
from calculator import timeline
from portable_coordinate_original_cases import prepare_case as original_case
from portable_add_self_destruct_wire import compile_battle
from world_add_attack_battle_native import observe as common_observe
from world_original_resource_native import capture as resource_capture


def prepare_case(row):
    case,prepared=original_case(row)
    case.update(logical_geometry=copy.deepcopy(row['logical_geometry']),self_destruct_contract=copy.deepcopy(row['contract']),sampled_groups=True)
    words,meta,bindings,scene=compile_battle(prepared,case['logical_geometry'])
    return words,(case,meta,bindings,scene)


def observe(domain):
    rows=[];old=timeline.BossScript;lookup={b.label:i for i,b in enumerate(domain[2])};cursors=[[0,0] for _ in domain[2]]
    class Boss(old):
        def _retire(self,run,add,why,t,events,log=True):
            if why=='자폭':rows.append(dict(time=t,node=run.p.idx,slot=lookup[add.id],generation=run.opens,fired=add.fired))
            return super()._retire(run,add,why,t,events,log)
        def finish(self,t):
            result=super().finish(t)
            for slot,b in enumerate(domain[2]):
                if int(b.kind)!=5:continue
                run=self._runs[b.run]
                if run.opens and run.p.summon.attack is not None:cursors[slot]=[run.opens,run.adds[b.slot].fired]
            return result
    with patch.object(timeline,'BossScript',Boss),resource_capture(domain[0]) as resources:n=common_observe(domain)
    n['self_destruct']=rows;n['original_resources']=resources;n['firing_cursors']=cursors
    return n
