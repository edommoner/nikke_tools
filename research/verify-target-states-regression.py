"""Full common verifier with exact2503 prior input/readback preservation.

Retains all current input/output bytes before checking hashes or CPU results.
No GPU retry, relaxed guard, tolerance, or prior-output normalization.
"""
import argparse
import array
import datetime
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIOR = '3f6342fcee8d5d2773a89307597dbd5bd184f01e'
BLOCK_PROOF = PRIOR
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'scripts')]
import portable_runtime as runtime
from portable_specs import ABI, LIMITS


def old_report(path):
    return json.loads(subprocess.check_output(['git', 'show', PRIOR + ':' + path], cwd=ROOT))


def packed_words(words):
    packed = array.array('I', words)
    if sys.byteorder != 'little':
        packed.byteswap()
    return packed.tobytes()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
