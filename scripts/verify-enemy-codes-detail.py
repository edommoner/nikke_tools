"""Matched and mismatched real enemy-code branches; CPU observations are output."""
import sys,json,hashlib,importlib.util
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for
spec=importlib.util.spec_from_file_location('code_predicates_oracle',ROOT/'scripts/verify-predicates-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.buff_manager import BuffManager
