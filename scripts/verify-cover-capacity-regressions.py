"""Focused v37 regression of previous cover/heal/HP/down lifecycles."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
cap=load('capacity_legacy_loader','scripts/verify-cover-capacity.py');old=cap.v;surv=old.s;hp=load('capacity_HP_oracle','scripts/verify-hp-edge.py')
def fixtures():
    planned=[(old,*x) for x in old.fixtures()]+[(old,*x) for x in old.real_fixtures() if x[0].endswith(('-incoming','-revival'))]+[(hp,*x) for x in hp.fixtures()]+[(surv,*x) for x in surv.fixtures(quick=True)]
    planned += [(surv.v,*x) for x in surv.v.fixtures() if x[0].startswith(('cover-','lowest-cover-'))]
    assert len(planned)==74,len(planned)
    return planned
