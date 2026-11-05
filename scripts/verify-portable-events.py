"""Reuse the authored clock/lifecycle cases on the shared GPU executor.
CPU state and traces are regression outputs only, never GPU inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from portable_runtime import compile_program,run_programs,PortableExecutionError
from timer_registry_cases import cases,prepare,exercise,NAMES
import engine_worker


def compile_case(case):
    bm=prepare(case)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    script=[[0,0,0,0,0,-1,0,0]]
    for i,t in enumerate(case['times']):
        if t in case.get('events',{}):script.append([t,0,7,0,0,-1,0,0])
        script.append([t,2,0,0,-1,i,0,0])
    return compile_program(chars,bm._effects,script,[bm.state['base_stats'][n]['atk'] for n in NAMES])
