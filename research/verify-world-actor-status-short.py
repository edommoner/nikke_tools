"""68 new status/recipient inputs;one shared CUDA/Metal comparison driver."""
import argparse,array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
suite=module('status_short_suite','research/verify-world-actor-status.py');cross=module('status_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-actor-status-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 entries=[]
 for label,driver in [('status',suite),('recipient',suite.recipient)]:
  rows,programs,bad=driver.prepare()
  for c,(words,meta,bindings) in zip(rows,programs):
   w=list(words);w[0]=L['WORLD_ACTOR_STATUS_ABI'];entries.append((label+'/native/'+c['name'],w,(driver,c,meta,bindings)))
  for name,words in bad:
   w=list(words);w[0]=L['WORLD_ACTOR_STATUS_ABI'];entries.append((label+'/reject/'+name,w,None))
 assert len(entries)==68
 a=array.array('I',[68])
 for _,w,_ in entries:a.extend(w)
 if sys.byteorder!='little':a.byteswap()
 return entries,a.tobytes()
