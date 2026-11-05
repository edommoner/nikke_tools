"""Observe native non-core expected accumulation; no GPU admission or execution."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / n) for n in ('app', 'scripts', 'tests')]
from test_target_counter_runtime import manager, NAMES


def marker(conditions):
    return dict(name='non-core-study', source='스킬1', type='buff', stat='atk_pct',
                fixed_value=1, duration=-1, target='self',
                trigger=dict(timing=['on_attack'], condition=conditions))


def bits(value):
    return struct.pack('>d', value).hex()
