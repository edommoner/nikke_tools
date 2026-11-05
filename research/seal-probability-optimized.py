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
SOURCE = '2b89babe0bd6ffa16c9b8b315de3137e7da669c8'
BASELINE = '988858f853594e2a0770640fa21bbd94d7c08cc0'


def load(name):
    return json.loads((REPORTS / (name + '.json')).read_text())


def save(name, value):
    (REPORTS / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()
