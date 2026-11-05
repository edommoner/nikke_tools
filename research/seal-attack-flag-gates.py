"""Check the completed fixed-source Mac gates independently of CUDA evidence."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research'
SOURCE = '7492d8b191471f820989dc760bc4adc91494cf6a'
PRIOR = '13c9bdf734fde4325db7376165fcc904b549a242'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())
