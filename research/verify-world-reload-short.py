"""New reload-control inputs only; project saved Metal blocks without GPU reruns."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('physical_counter_short_suite','research/verify-world-reload.py');cross=module('counter_short_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-reload-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 rows,programs,bad=suite.prepare();entries=[('native/'+c['name'],w,(c,meta,bindings)) for c,(w,meta,bindings) in zip(rows,programs)]
 entries.extend(('reject/'+name,w,None) for name,w in bad);assert len(entries)==65
 packed=array.array('I',[len(entries)])
 for _,w,_ in entries:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return entries,packed.tobytes()
def compare(block,domain):
 case,meta,bindings=domain;native,trace=suite.inspect_native(case);actual=suite.decoded(block,meta,case,bindings)
 assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
 assert not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]),case['name']
 assert suite.charge.team.skill_trace(block,meta)==trace,case['name']
 return dict(battle=native,skill_trace=trace)
