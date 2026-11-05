"""Every own-effect preflight candidate: complete simple-boss real profiles.
No effects are filtered. Missing/failed cases remain failed in the full matrix.
CPU battles run only after GPU readback and never supply GPU state or traces.
"""
import argparse,copy,datetime,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_roster_input import compile_static_battle
from portable_runtime import run_programs,UnsupportedPortable
import portable_runtime as runtime
from portable_conditional_hp_gap import native_reference as observe_native,verify_difference
spec=importlib.util.spec_from_file_location('portable_real_reference',ROOT/'scripts/verify-portable-real-battle.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)


def roster_for(name):
    stage=str(adapter.META[name]['burst_stage'])
    fillers={'1':['도라','드레이크','N102','메어리','미란다'],
             '2':['미란다','드레이크','N102','메어리','도라'],
             '3':['미란다','도라','N102','메어리','드레이크']}
    if stage not in fillers:raise UnsupportedPortable('Add an explicit full-roster policy for stage '+stage)
    return [name]+[n for n in fillers[stage] if n!=name][:4]
