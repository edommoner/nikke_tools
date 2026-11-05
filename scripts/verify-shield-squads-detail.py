"""Independent full raw-character battles with authored shield-layer stimuli.

This exercises shield consumption within combat, not a boss attack/HP model.
CPU choices, damage, shield quantities and event times are never GPU inputs.
"""
import copy, hashlib, importlib.util, json, math, random, sys
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'scripts')]
spec = importlib.util.spec_from_file_location('shield_control', ROOT/'scripts/verify-control-detail.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
import detail_gpu
from calculator.buff_manager import BuffManager

SCHEDULE = [2, 4, 8, 12, 20, 28]
SUBJECTS = ['센티', '라푼젤 : 퓨어 그레이스', '모리']
