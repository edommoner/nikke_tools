"""Shared command quantities before autonomous manual-reload mode production."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from test_weapon_mode_specs import effect,mode,chars,NAMES,manager
import detail_gpu as g



if __name__=='__main__':main()
