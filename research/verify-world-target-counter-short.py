"""New counter inputs only; project saved Metal blocks without GPU reruns."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('counter_short_suite','research/verify-world-target-counters.py');cross=module('counter_short_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-target-counter-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 rows,programs,bad=suite.prepare();entries=[('native/'+c['name'],w,c) for c,(w,meta) in zip(rows,programs)]
 entries.extend(('reject/'+name,w,None) for name,w in bad);assert len(entries)==32
 packed=array.array('I',[len(entries)])
 for _,w,_ in entries:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return entries,packed.tobytes()
def compare(block,case):
 native=suite.observe_case(case);wanted=suite.expected_observation(native)
 assert block[0]==0 and suite.decoded(block,case)==wanted,case['name'];return native
