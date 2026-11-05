"""Whole-squad and raw resident charge frames, GPU runs before CPU reference."""
import argparse,ast,hashlib,importlib.util,inspect,json,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('charge_definitions','scripts/heal-charge-fixtures.py');g=d.g;v=d.v
def fixtures(group):
    if group=='new':return [(SimpleNamespace(compare=compare),*x) for x in [*d.fixtures(),*d.real_fixtures()]]
    old=load('charge_prior_oracles','scripts/verify-heal-sharing.py');cases=old.fixtures('new')+old.fixtures('legacy');assert len(cases)==178;return cases
