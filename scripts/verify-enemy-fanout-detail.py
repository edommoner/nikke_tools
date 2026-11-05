"""GPU fanout with common authored selector, nesting and spawn-order witnesses."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_fanout_cases import selector_prepare,selector_actions,selector_exercise,order_prepare,order_exercise,NAMES,world_patterns
from detail_coverage import a
from detail_boss import compile_world
from detail_world import packed_enemy,patterns_for
from impact_specs import ActorHandle,Impact,impact_command
import detail_gpu as g


def compiled(bm,raw,parts=None):
    chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
    program=g.compile_effects(chars,bm._effects,enemy_fields=True)
    program['world'],_=compile_world({'patterns':patterns_for(parts or [])+raw},parts or [],{'enemy':{'patterns':raw}},program)
    return program












if __name__=='__main__':main()
