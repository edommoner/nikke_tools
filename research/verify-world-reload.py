"""Actual full-native reload programs through one shared CUDA/Metal executable."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from portable_reload_specs import pack as pack_reload
from portable_team_hit_specs import bound_effects
from world_reload_cases import fixtures
from world_reload_native import observe as inspect_native
from world_frame_native import roster_names
s=importlib.util.spec_from_file_location('reload_charge_suite',ROOT/'research/verify-world-charge-control.py');charge=importlib.util.module_from_spec(s);s.loader.exec_module(charge)
INPUT=L['WORLD_RELOAD_INPUT_WORDS'];OUTPUT=L['WORLD_RELOAD_OUTPUT_WORDS'];SOURCE='gpu/world_reload_entry.slang'

def compile_case(case):
 w,m,b=charge.compile_case(case);names=roster_names(case);effects=bound_effects([(e,names[o]) for e,o in zip(case['effects'],case['owners'])],m,names)
 w.extend(pack_reload((e for e,owner in effects),manual_swap=case.get('manual_swap')));w[0]=L['WORLD_RELOAD_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=22
 assert len(w)==INPUT;return w,m,b

def decoded(block,meta,case,bindings):
 from portable_reload_observation import readback
 r=charge.decoded(block,meta,case,bindings);r.update(readback(block,meta));return r

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];p=L['WORLD_RELOAD_INPUT_BASE'];seed=programs[0][0];f=L['DEFINITION_BASE'];force=f+L['DEFINITION_WORDS']
 changes=[('old-abi',0,L['WORLD_CONTROL_ABI']),('old-mode21',L['TARGET_COUNTER_INPUT_BASE']+6,21),('reload-magic',p,0),('reload-version',p+1,2),('reload-count',p+2,3),('reload-reserved',p+3,1),('reload-unused-flags',p+10,1),('reload-unknown-flags',p+8,4),('reload-fixed-force-flag',p+8,2),('reload-force-missing-flag',p+9,0),('reload-force-fixed-flag',p+9,1),('reload-fixed-kind',f+F['KIND'],4),('reload-fixed-stat',f+F['STAT'],91),('reload-force-stat',force+F['STAT'],1),('reload-force-kind',force+F['KIND'],0),('reload-fixed-nan',f+F['VALUE']+1,0x7ff80000),('reload-force-infinite',force+F['VALUE']+1,0x7ff00000),('reload-force-enemy-recipient',L['RECIPIENT_BASE']+8,4),('reload-control-marker',L['WORLD_CONTROL_INPUT_BASE'],0)]
 for name,at,value in changes:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad

def sha(b):return hashlib.sha256(b).hexdigest()
