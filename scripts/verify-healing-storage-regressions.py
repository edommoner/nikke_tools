"""Accepted v39 authored19/raw4/prior101 against v40 CPU/GPU implementation."""
import argparse,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
out=load('storage_outgoing_regressions','scripts/verify-outgoing-healing.py');old=load('storage_prior_regressions','scripts/verify-outgoing-healing-regressions.py')
def fixtures():
    cases=[(out,*x) for x in out.fixtures()]+[(out,*x) for x in out.real_fixtures()]+old.fixtures();assert len(cases)==124;return cases
