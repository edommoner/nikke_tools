#!/usr/bin/env python3
"""Reclaim only zero-block allocation; retain legacy raw bytes and evidence."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from portable_project_storage import sweep

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--storage',type=Path,required=True,help='Fresh external receipt directory')
    p.add_argument('--apply',action='store_true',help='Reclaim verified all-zero blocks (default: plan only)')
    p.add_argument('--limit',type=int)
    a=p.parse_args()
    if a.limit is not None and a.limit<1:p.error('--limit must be positive')
    print(json.dumps(sweep(ROOT,a.storage,apply=a.apply,limit=a.limit),indent=2))
