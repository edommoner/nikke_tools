"""Seal completed probability evidence without changing the tested compute source."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'research'
SOURCE = '27a375145147a2d042c8c0e66fffdb908b2b1be3'
PRIOR = 'f2206ef4a32fb89ad9c4f2381bb9dbfa5ec711d1'


def load(name):
    return json.loads((P / (name + '.json')).read_text())


def save(name, value, compact=False):
    options = dict(separators=(',', ':')) if compact else dict(indent=2)
    (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, **options) + '\n')
