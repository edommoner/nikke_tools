"""Shared formula witnesses; reuse frozen identical shader/input readbacks on Mac."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
import world_skill_formula_cases as cases
suite=cases.suite;physical=suite.physical;SOURCE=suite.SOURCE;inspect_native=suite.inspect_native;skill_trace=suite.skill_trace
def fixtures():return cases.fixtures()
def prepare():
 rows=fixtures();return rows,[suite.compile_case(c) for c in rows],[]
def compare(block,case,meta,bindings):
 native,trace=inspect_native(case);actual=physical.decoded(block,meta,case,bindings)
 assert block[0]==0 and all(actual[k]==native[k] for k in native if k!='scope'),case['name']
 assert skill_trace(block)==trace and not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]),case['name']
 return native,trace
def sha(b):return hashlib.sha256(b).hexdigest()
