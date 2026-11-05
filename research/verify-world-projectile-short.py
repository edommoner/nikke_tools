"""One short shared63 CUDA dispatch; golden projects saved Metal blocks, GPU0."""
import argparse,array,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
suite=module('projectile_short_suite','research/verify-world-projectile.py');cross=module('projectile_short_digest','research/summarize-portable-cross-gpu.py');GOLDEN=ROOT/'research/portable-world-projectile-short-expected.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare():
 rows,programs,bad=suite.prepare();entries=[('native/'+c['name'],w,(c,m,b)) for c,(w,m,b) in zip(rows,programs)];entries.extend(('reject/'+n,w,None) for n,w in bad);assert len(entries)==63
 packed=array.array('I',[len(entries)])
 for _,w,_ in entries:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return entries,packed.tobytes()
def compare(block,domain):
 c,m,b=domain;native,trace=suite.inspect_native(c);actual=suite.decoded(block,m,c,b);assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope'),c['name'];assert suite.reload.charge.team.skill_trace(block,m)==trace;assert not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]);return dict(battle=native,skill_trace=trace)
def development_entries():
 from portable_readiness_cases import fixtures
 rows=fixtures();entries=[]
 for c in rows:
  w,m,b=suite.compile_case(c);entries.append(('development/'+c['name'],w,(c,m,b)))
 seed=entries[0][1]
 from portable_specs import FIELDS as F
 for name,offset,value in [('lost-hp-invalid-stat',F['STAT'],0),('lost-hp-invalid-kind',F['KIND'],4)]:
  w=list(seed);w[L['DEFINITION_BASE']+offset]=value;entries.append(('reject/'+name,w,None))
 direct=entries[4][1]
 for name in ('direct-health-unknown-flag','direct-health-non-health'):
  w=list(direct)
  if name.endswith('unknown-flag'):w[L['DEFINITION_BASE']+F['FLAGS']] |= 512
  else:w[L['HEALTH_DEFINITION_BASE']+1]=0
  entries.append(('reject/'+name,w,None))
 return entries
