"""Autonomous GPU source lifecycles and actual pool-clipped landing receipts."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from detail_boss import compile_world
from detail_world import patterns_for,packed_enemy
from calculator.boss_pattern import BossScript,validate,ADD_PREFIX
from calculator.sim_result import HitEvent
from effect_runtime import state
from impact_runtime import land_add
from impact_specs import ActorHandle,Impact,ImpactTrace,impact_command
from world_actor_runtime import registry_for
from world_actor_specs import bindings
from test_target_counter_runtime import manager,NAMES
from summon_source_cases import cases
import detail_gpu as g

def counter(name,event):return dict(name=name,source='스킬1',type='buff',stat='',fixed_value=0,target='self',duration=-1,max_stack=10000,trigger=dict(timing=[event],condition=[]))

def prepare(raw,parts=None,effects=None):
    bm=manager([counter('source-spawns','event:enemy_spawn'),counter('source-deaths','enemy_death')] if effects is None else effects);enemy={'def':0,'core_px':0}
    expected=patterns_for(parts or [])+copy.deepcopy(raw)
    boss=BossScript(validate(expected),enemy,lambda *_:True)
    state(bm).impact_trace=ImpactTrace();bm.state['enemy']=enemy
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in NAMES]
    program=g.compile_effects(chars,bm._effects)
    program['world'],metadata=compile_world({'def':0,'core_px':0,'patterns':expected},parts or [],{'enemy':{'patterns':raw}},program)
    return bm,boss,enemy,program


def script_query(script,index):return next(row for row in script if row[1]==2 and row[5]==index)




if __name__=='__main__':main()
