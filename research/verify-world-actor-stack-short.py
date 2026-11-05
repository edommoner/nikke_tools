"""61 typed stack checks from Metal590;one shared driver for both GPU backends."""
import argparse,array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('stack_short_suite','research/verify-world-actor-stacks.py');cross=module('stack_short_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-actor-stack-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 rows,programs,bad=suite.prepare();entries=[]
 for c,(w,meta,bindings) in zip(rows,programs):entries.append(('native/'+c['name'],w,(c,meta,bindings)))
 for name,w in bad:entries.append(('reject/'+name,w,None))
 assert len(entries)==61
 a=array.array('I',[61])
 for _,w,_ in entries:a.extend(w)
 if sys.byteorder!='little':a.byteswap()
 return entries,a.tobytes()
