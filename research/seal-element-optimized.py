"""Seal adopted scalar accessors only after both GPUs and all Mac gates finish."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research'
SOURCE = '32653b09d597f0443c0df11f2076b249ec33dbd7'
BASELINE = '80170c3b922b666eadb1f72bec22331c183a89b4'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def save(name, value):
    (REPORTS / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()
