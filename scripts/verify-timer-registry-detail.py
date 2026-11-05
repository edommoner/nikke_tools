"""Periodic clock ownership, phase-preserving refresh and boundary checks."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from timer_registry_cases import cases,prepare,exercise,NAMES
from detail_coverage import a
import detail_gpu as g




if __name__=='__main__':main()
