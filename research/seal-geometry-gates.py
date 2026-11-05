"""Check the completed fixed-source Mac gates independently of CUDA evidence."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research'
SOURCE = '17decef851fbea0a300e16706c63ff6702e6e83f'
PRIOR = 'cd5762a8c95914a90d83d5e9552bf49414027a50'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())
