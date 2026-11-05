"""Shared staged clocks: independent quantities and a few whole-squad interactions."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
from staged_dot_runtime import damage_stack
from staged_dot_specs import MODEL_WARNING
from effect_runtime import pool
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('staged_dot_oracle','scripts/verify-gauge-detail.py');N=v.NAMES;E=v.effect

def definition(count=3,override=1,cap=10):
    parent=E('parent','damage','sequential_damage:'+str(count),100,'target',event='inactive')
    dot=E('phase','damage','dot_damage',100,'same_target:parent',scaling='stack_count',max_stack=cap,tick_interval=.4,duration=2,ramp_interval=.2,post_ramp_tick_delay=.5)
    dot['source']='스킬3'
    if override is not None:dot['ramp_damage_stack']=override
    return parent,dot




if __name__=='__main__':main()
