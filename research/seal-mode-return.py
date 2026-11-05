"""Seal the fixed mode-return source only after shared/real/API/remote gates."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

R = Path(__file__).resolve().parents[1]
P = R / 'research'
SOURCE = 'a7f478452f7d9c3dbdca97879a2efdf8634c38a9'
sys.path[:0] = [str(R / d) for d in ('app', 'scripts')]


def load(name):
    return json.loads((P / (name + '.json')).read_text())


def save(name, value):
    (P / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(raw):
    text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    text = '\n'.join(line for line in text.split('\n') if not re.match(r'^\s*#line\b', line))
    return re.sub(r'"([^"\n]+)"', lambda m: '"' + m[1].replace('\\', '/').split('/')[-1] + '"' if '/' in m[1] or '\\' in m[1] or m[1] == 'slang-cuda-prelude.h' else m[0], text).encode('utf-8')
