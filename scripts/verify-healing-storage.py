"""Independent squad and per-name resident buffer snapshots for staged v40."""
import argparse,ast,hashlib,importlib.util,inspect,json,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('storage_definitions','scripts/healing-storage-fixtures.py');g=d.g;v=d.v
