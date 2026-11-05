"""Existing masked-ally executor: independent recipient table and real skill usage."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from test_named_ally_targets import TARGET,BASE,characters,effect
from calculator.buff_manager import BuffManager
import detail_gpu as g
spec=importlib.util.spec_from_file_location('named_allies_full',ROOT/'scripts/verify-extended-detail.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)




if __name__=='__main__':main()
