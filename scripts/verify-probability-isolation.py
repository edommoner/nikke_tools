"""Non-aligned phases distinguish effect identity, parallel squads and lifetimes."""
import sys,json,hashlib,importlib.util,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('isolation_probability_oracle',ROOT/'scripts/verify-probability-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
