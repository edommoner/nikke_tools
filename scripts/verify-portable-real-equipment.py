"""Real preparation -> 45 equipment definitions -> shared GPU initialization.
This explicitly excludes character skills and battle policies. It is not an
all-character battle certification or a CPU-trace-to-GPU conversion.
"""
import argparse,copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_runtime import compile_program,run_programs
