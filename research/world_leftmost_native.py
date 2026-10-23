"""Capture existing target-resolution returns without adding any state query."""
import engine_worker  # Install canonical compatibility layers before calculator imports.
from contextlib import contextmanager
from unittest.mock import patch
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    original=BuffManager._resolve_target;selections=[]
    def resolve(bm,target,caster):
        result=original(bm,target,caster)
        if isinstance(target,str) and target.startswith('allies_code_weapon_leftmost:'):
            selections.append(dict(target=target,owner=names.index(caster),picked=[names.index(n) for n in result]))
        return result
    with patch.object(BuffManager,'_resolve_target',resolve):yield selections

def observe(case):
    with capture(roster_names(case)) as selections:native,trace=plain(case)
    native['leftmost_selections']=selections
    return native,trace
