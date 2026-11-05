"""Execute all catalog weapons without character effects; never full-character proof.
Static real metadata is packed before GPU dispatch. CPU observations are evaluated
only after readback and are never used as a shot schedule or GPU state input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_weapon_oracle import observe
from portable_runtime import run_programs
import importlib.util
spec=importlib.util.spec_from_file_location('combat_verifier',ROOT/'scripts/verify-portable-combat.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
