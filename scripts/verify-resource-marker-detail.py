"""Resource-associated markers reuse the existing carrier and gauge interpreter."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
import detail_gpu as g
spec=importlib.util.spec_from_file_location('marker_oracles',ROOT/'scripts/verify-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.effect;N=v.NAMES




if __name__=='__main__':main()
