"""Verify the application HTTP -> Python -> shared GPU event path locally."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
import engine_worker
from timer_registry_cases import NAMES
