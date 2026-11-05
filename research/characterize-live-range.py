"""Native actual buff activation/query boundaries for the next geometry port."""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / f) for f in ['app', 'scripts', 'tests']]
from test_target_counter_runtime import manager, NAMES
from calculator.buff_manager import optimal_range_of, _NIKKE


def effect(name, stat, value, timing='battle_start', conditions=None, duration=-1):
    return dict(name=name, source='스킬1', type='buff', stat=stat, fixed_value=value,
                duration=duration, target='self',
                trigger=dict(timing=[timing], condition=conditions or []))
