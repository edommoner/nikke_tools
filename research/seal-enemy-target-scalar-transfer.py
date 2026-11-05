"""Verify transferred CUDA blobs against fixed-source Metal; never launch a GPU."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT=Path('/Users/edo/Documents/ChatGPT/nikke_tools')
SOURCE='73570451569dce424667e37f4729e475ea6b0a86'


def load(name):return json.loads((ROOT/'research'/(name+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(commit,path):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
