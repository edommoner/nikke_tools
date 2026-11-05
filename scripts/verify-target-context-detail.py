"""Actual add-pool completions and nested target predicates, one shared fixture."""
import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from test_target_counter_runtime import NAMES
from target_counter_cases import marker
from effect_runtime import state,publish_impact
from impact_runtime import land_add
from impact_specs import ActorHandle,Impact,impact_command
from calculator.sim_result import HitEvent
from detail_world import packed_enemy
import detail_gpu as g
spec=importlib.util.spec_from_file_location('context_source_setup',ROOT/'scripts/verify-summon-sources-detail.py');source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)


def buff(name,stat,value,event,conditions=()):
    return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target='self',duration=10,max_stack=1,trigger=dict(timing=[event],condition=list(conditions)))






if __name__=='__main__':main()
