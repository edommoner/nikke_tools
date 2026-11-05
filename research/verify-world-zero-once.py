"""Distinct sub-EPS initial-zero cases through the common CUDA/Metal entry."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
spec=importlib.util.spec_from_file_location('world_frame',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def fixtures():
 base=copy.deepcopy(f.fixtures()[0]);base['duration']=.05;base['patterns'][0]['spec']['hits']=1;base['patterns'][0]['until']=dict(time=5e-10);base['name']='initial-zero-once-sub-epsilon-expiry';rows=[base]
 c=copy.deepcopy(base);c['name']='initial-zero-once-sub-epsilon-repeat';c['patterns'][0].update(after=['start','a'],repeat=0);rows.append(c)
 c=copy.deepcopy(base);c['name']='initial-zero-once-sub-epsilon-follow';c['patterns']=[dict(id='wait',kind='idle',until=dict(time=5e-10)),dict(c['patterns'][0],id='a',after=['wait'])];rows.append(c)
 c=copy.deepcopy(base);c['name']='initial-zero-once-zero-duration-finish';c['duration']=0;rows.append(c)
 return rows
