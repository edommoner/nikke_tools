"""Whole-squad v41 parity, GPU first, CPU independently observed afterward."""
import argparse,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('sharing_definitions','scripts/heal-sharing-fixtures.py');g=d.g;v=d.v
def fixtures(group):
    if group=='new':return [(v,*x) for x in [*d.fixtures(),*d.real_fixtures()]]
    storage=load('sharing_storage_oracle','scripts/verify-healing-storage.py')
    extra=load('sharing_storage_extra','scripts/healing-storage-extra-fixtures.py')
    old=load('sharing_prior_oracles','scripts/verify-healing-storage-regressions.py')
    cases=[(storage,*x) for x in storage.d.fixtures()]+[(storage,*x) for x in extra.fixtures()]+old.fixtures()
    assert len(cases)==153;return cases
