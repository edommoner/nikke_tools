"""Seal full Metal plus new/saved source-identical CUDA evidence honestly."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='795a9e5b684796b3b6a2fb9b59546e60401a5503'
PRIOR='3f6342fcee8d5d2773a89307597dbd5bd184f01e'
def load(name):return json.loads((P/(name+'.json')).read_text())
def save(name,value):(P/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
