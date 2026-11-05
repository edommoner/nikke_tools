"""Seal fixed-source physical attack flag proof; keep whole catalog goal open."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='7492d8b191471f820989dc760bc4adc91494cf6a'
PRIOR='13c9bdf734fde4325db7376165fcc904b549a242'


def load(name):return json.loads((P/(name+'.json')).read_text())
def save(name,value,compact=False):
    options=dict(separators=(',',':')) if compact else dict(indent=2)
    (P/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,**options)+'\n')
