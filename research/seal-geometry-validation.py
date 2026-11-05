"""Seal fixed-source geometry evidence; optimization adoption needs its own proof."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'research'
SOURCE = '17decef851fbea0a300e16706c63ff6702e6e83f'
PRIOR = 'cd5762a8c95914a90d83d5e9552bf49414027a50'


def load(name):
    return json.loads((P / (name + '.json')).read_text())


def save(name, value, compact=False):
    options = dict(separators=(',', ':')) if compact else dict(indent=2)
    (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, **options) + '\n')
