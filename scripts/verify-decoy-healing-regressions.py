"""Focused v38 regressions for existing layers, HP/cover, and down/revive."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('decoy_regression_loader','scripts/verify-decoy-healing.py');old=d.v;surv=old.s;incoming=surv.v;cap=load('decoy_cover_capacity_oracle','scripts/verify-cover-capacity.py')
def fixtures():
    planned=[(old,*x) for x in old.fixtures()]+[(surv,*x) for x in surv.fixtures(quick=True)]+[(cap,*x) for x in cap.fixtures()]+[(cap,*x) for x in cap.real_fixtures() if x[0]=='raw-Tia-capacity-owned-cover-cube']
    planned += [(incoming,*x) for x in incoming.fixtures() if x[0].startswith('layers-') or x[0]=='decoy-consumed-state-end']
    assert len(planned)>=60,len(planned);return planned
