"""Named attack repetition, phase ordering and four real five-member squads.

Reuses the existing independent whole-squad comparator. CPU observations below
only prove that gated effects actually fired; they never feed GPU execution.
"""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
spec=importlib.util.spec_from_file_location('named_periodic',ROOT/'scripts/verify-periodic-detail.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
E=p.effect




if __name__=='__main__':main()
