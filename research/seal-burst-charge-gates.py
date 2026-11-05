"""Independent audit of completed fixed-source Mac validation; no GPU dispatch."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCE='20e213bf28544a3ad2709fdc852d239eed108b5e'
PRIOR='3c3cd7d4fe3731a66587ea3577bf0496ef74a458'


def load(name):return json.loads((ROOT/'research'/(name+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(path,commit=SOURCE):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(8*1024*1024):h.update(block)
    return h.hexdigest()
