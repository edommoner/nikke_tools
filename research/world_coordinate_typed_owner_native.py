"""Full original battle with scoped logical-owner query telemetry."""
import importlib.util
from pathlib import Path
from portable_coordinate_typed_owner_cases import prepare
from world_coordinate_typed_weapon_native import observe as weapons
from world_destructible_weapon_roster_native import capture_typed

def observe(row):
    c=row if 'original_run' in row else prepare(row)[0];c['python_observers_only']=True
    s=importlib.util.spec_from_file_location('typed_owner_original',Path(__file__).with_name('verify-coordinate-original-short.py'));original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
    # Use the existing wrapper's same typed scope so owner queries are captured
    # without introducing another world or invoking any extra enemy selection.
    from unittest.mock import patch
    import world_coordinate_typed_weapon_native as module
    from contextlib import contextmanager
    captured={}
    @contextmanager
    def capture(case):
        with capture_typed(case) as value:
            captured['data']=value[0];yield value
    def owner(case):n=original.native_reference((case,{},(),{}));return n,n['skill_trace']
    with patch.object(module,'capture_typed',capture):n,trace=weapons(c,observer=owner)
    n['coordinate_typed_owner_queries']=captured['data']['coordinate_typed_owner_queries']
    n['coordinate_typed_weapon']['scope']='Declared BODY-owned typed targets and current enemy fields; CPU reference only'
    return n,trace
