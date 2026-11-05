"""Actual world count + effect lifetimes; no character-specific result matrix."""
import argparse,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from test_target_counter_runtime import NAMES
from detail_world import packed_enemy
from impact_specs import ActorHandle,Impact,impact_command
from impact_runtime import land_add
from calculator.sim_result import HitEvent
import detail_gpu as g
spec=importlib.util.spec_from_file_location('world_source_verifier',ROOT/'scripts/verify-summon-sources-detail.py');sources=importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)


def effect(name,stat,value,condition,timing='passive',duration=-1,max_stack=1):
    return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target='self',duration=duration,max_stack=max_stack,trigger=dict(timing=[timing],condition=condition))






if __name__=='__main__':main()
