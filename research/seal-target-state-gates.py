"""Check the completed fixed-source Mac gates independently of CUDA evidence."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research'
SOURCE = '795a9e5b684796b3b6a2fb9b59546e60401a5503'
PRIOR = '3f6342fcee8d5d2773a89307597dbd5bd184f01e'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())
