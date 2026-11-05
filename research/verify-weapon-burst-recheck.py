"""Audit saved real-GPU output; never supply CPU observations to GPU input.

Run verify-portable-combat.py first, then pass its report with --report.
This adds full native controller comparisons for seven older authored cases.
The production implementation and fixtures remain shared by CUDA and Metal.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ('app', 'scripts')]
spec = importlib.util.spec_from_file_location('combat_verifier', ROOT / 'scripts/verify-portable-combat.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
from portable_burst_oracle import observe

NATIVE_CASES = {
    'reentry-b1-request-1', 'reentry-b1-request-2',
    'reentry-waits-own-cooldown-and-entry-notice',
    'zero-valued-b3-reentry-state', 'startup-pending-reentry-consumed-once',
    'expired-reentry-state-does-not-open-slot', 'all-stage-state-uses-current-stage',
}


def differences(actual, expected, path=''):
    """Keep every raw observer discrepancy, without changing acceptance values."""
    if isinstance(expected, dict):
        return sum((differences(actual[k], v, path + '.' + k) for k, v in expected.items()), [])
    if isinstance(expected, list):
        assert len(actual) == len(expected), path
        return sum((differences(a, b, path + f'[{i}]') for i, (a, b) in enumerate(zip(actual, expected))), [])
    return [] if actual == expected else [dict(path=path, gpu=actual, raw_cpu=expected)]
