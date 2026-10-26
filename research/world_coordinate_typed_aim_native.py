"""Canonical resolver and all original handlers under declared typed candidates."""
import importlib.util
from pathlib import Path
from portable_coordinate_typed_weapon_cases import prepare
from world_coordinate_typed_weapon_native import observe as weapons
from world_destructible_weapon_roster_native import capture_typed

def observe(row):
    case,_=prepare(row);case['python_observers_only']=True
    s=importlib.util.spec_from_file_location('typed_aim_original_observer',Path(__file__).with_name('verify-coordinate-original-short.py'));original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
    def owner(c):
        n=original.native_reference((c,{},(),{}));return n,n['skill_trace']
    if case.get('expect_reference_gap'):
        with capture_typed(case) as (data,samples,heals):
            try:owner(case)
            except ValueError as error:
                if str(error)!='Typed aim logical enemy recipient requires its own actor policy':raise
                assert not data['coordinate_typed_aim_frames'] and not data['coordinate_weapon_attacks'] and not samples
                return dict(reference_model_gap=True,reason=str(error),unhandled_selector=case['expect_reference_gap'],original_definitions=len(case['effects']),original_names=case['names'],blocked_before_first_frame=True),[]
            raise AssertionError('Missing logical recipient was silently admitted')
    native,trace=weapons(case,observer=owner)
    native['coordinate_typed_weapon']['scope']='Declared typed-before-body-v1 frame aim and sampled weapon geometry; no canonical gameplay certification'
    return native,trace
