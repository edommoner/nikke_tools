"""Periodic input/eligibility sampling and registration ownership on both backends."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from periodic_target_cases import prepare,actions,exercise,reentrant_prepare,reentrant_actions,reentrant_exercise,predicate_prepare,predicate_actions,predicate_exercise,sibling_prepare,sibling_actions,sibling_exercise,NAMES,world_patterns
from detail_coverage import a
from detail_boss import compile_world
from impact_specs import ActorHandle,Impact,impact_command
from periodic_target_specs import required_aim_owners
import detail_gpu as g


def compiled(bm,raw):
    chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES];program=g.compile_effects(chars,bm._effects,enemy_fields=True)
    program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program);g.validate_gpu_fields(program['effects'],bool(raw));return program












if __name__=='__main__':main()
