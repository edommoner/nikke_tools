"""77 necessary Actor checks;shared fixtures/decoder with Metal285, no normal rerun."""
import argparse,array,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pool=module('short_pools','research/verify-world-actor-pools.py');actor=module('short_registry','research/verify-world-actors.py');cross=module('short_digest','research/summarize-portable-cross-gpu.py')
GOLDEN=ROOT/'research/portable-world-actor-pools-short-expected.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def prepare():
 rows,programs,bad=pool.prepare();ar=actor.cases();ap=[actor.compile_case(c) for c in ar];ab=actor.negatives(ap);entries=[]
 for c,(w,meta,bindings) in zip(rows,programs):entries.append(('pool/native/'+c['name'],w,('pool',c,meta,bindings)))
 for name,w in bad:entries.append(('pool/reject/'+name,w,('reject',)))
 for c,(w,bindings) in zip(ar,ap):
  w=list(w);w[0]=L['WORLD_ACTOR_POOL_ABI'];w.extend([0]*(L['WORLD_ACTOR_POOL_INPUT_WORDS']-len(w)));entries.append(('registry/native/'+c['name'],w,('registry',c,bindings)))
 for name,w in ab:
  w=list(w);w[0]=L['WORLD_ACTOR_POOL_ABI'];w.extend([0]*(L['WORLD_ACTOR_POOL_INPUT_WORDS']-len(w)));entries.append(('registry/reject/'+name,w,('reject',)))
 assert len(entries)==77
 a=array.array('I',[len(entries)])
 for _,w,_ in entries:a.extend(w)
 if sys.byteorder!='little':a.byteswap()
 return entries,a.tobytes()
def semantic(block,domain):
 if domain[0]=='reject':assert block[0]==64;return dict(status=64)
 assert block[0]==0,block[0]
 if domain[0]=='pool':
  _,c,meta,bindings=domain;actual=pool.manual.decoded(block,c,L,bindings) if 'actions' in c else pool.decoded(block,meta,c,bindings);native=pool.manual.native(c,L) if 'actions' in c else pool.observe(c)
  assert all(actual[k]==native[k] for k in native if k!='scope'),c['name'];return native
 _,c,bindings=domain;base=L['WORLD_ACTOR_STATE_BASE'];query=L['WORLD_ACTOR_QUERY_BASE'];actual=dict(count=block[base],queries=[list(block[query+i*8:query+(i+1)*8]) for i in range(len(c['queries']))],registry=[list(block[base+8+i*8:base+8+(i+1)*8]) for i in range(len(bindings))]);native=actor.native(c);assert actual==native,c['name'];return native
