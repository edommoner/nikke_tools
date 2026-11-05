"""Shared clocks: authored quantities, independent CPU runs and raw squad inputs."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
from periodic_source_runtime import refresh,tick,count
from effect_runtime import pool
from periodic_source_specs import LEGACY_WARNING
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
v=load('periodic_source_oracle','scripts/verify-gauge-detail.py')
N=v.NAMES
def source(name,slots,base,step=0,event='battle_start',legacy=False):
    e=dict(name='refresh '+name+' '+event,source='스킬1',type='instant',stat='feather_refresh' if legacy else 'periodic_source_refresh',target='self',trigger=dict(timing=[event],condition=[]))
    if legacy:e.update(feather_id=name,feather_slots=slots,feather_interval_base=base,feather_interval_step_pct=step)
    else:e['periodic_source']=dict(name=name,slots=slots,base_interval=base,population_reduction_pct=step)
    return e





if __name__=='__main__':main()
