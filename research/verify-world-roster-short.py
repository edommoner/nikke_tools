"""One bounded CUDA run; Metal golden is projected from saved readback only."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_backend import source_hashes,execute
from portable_runtime import decode

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('world_roster_suite',ROOT/'research/verify-world-roster.py');cross=module('world_roster_digest',ROOT/'research/summarize-portable-cross-gpu.py')
GOLDEN=ROOT/'research/portable-world-roster-short-expected.json'
def sha(x):return hashlib.sha256(x).hexdigest()
def prepare():
 cases=suite.prepare();entries=[('native/'+c['name'],w,(c,p,m)) for c,p,w,m in cases]+[('reject/'+name,w,None) for name,w in suite.negative_inputs(cases)]
 p=array.array('I',[len(entries)])
 for name,w,domain in entries:p.extend(w)
 if sys.byteorder!='little':p.byteswap()
 return entries,p.tobytes()
