"""Run the accepted v38 101-case suite against staged v39/CPU extension."""
import argparse,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
r=load('outgoing_previous_regressions','scripts/verify-decoy-healing-regressions.py');d=r.d
def fixtures():
    result=[(d,*x) for x in d.fixtures()]+[(d,*x) for x in d.real_fixtures()]+r.fixtures()
    assert len(result)==101;return result
