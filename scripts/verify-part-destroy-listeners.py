"""Raw accepted destruction listeners, exercised by actual GPU part destruction."""
import argparse,hashlib,importlib.util,json,random,sys
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('listener_parts',ROOT/'scripts/verify-live-parts-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from calculator.buff_manager import BuffManager
SUBJECTS=['레이븐','아크레인저 블랙','로산나 : 시크 오션','E.H.','모리']
