"""Ten charge lifecycle collisions with independent per-frame GPU readbacks."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load('charge_oracle','scripts/verify-heal-charge.py');extra=load('charge_extra','scripts/heal-charge-extra-fixtures.py')
