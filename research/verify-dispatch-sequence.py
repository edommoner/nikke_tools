"""Run all previous core inputs plus44 repeats across the2048 boundary.

Compare raw words, including expected failures, with the completed proof. No
CPU trajectory or synthesized GPU output is used. CPU references remain proved
by that byte-identical prior readback; this is a transport-specific gate.
"""
import argparse,array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import dispatch_programs,pack_programs
from portable_specs import LIMITS as L
from portable_backend import source_hashes
PRIOR='7492276247a23f81ca48d8f17336abb7860b2a62'
class Collected(BaseException):pass
