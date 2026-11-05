"""Check actual GPU draws against CPython; never upload reference draws."""
import array,ctypes as C,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]

def plans_for(case):
 return ([[0,32,0] for _ in case['words']]
         +[[0,row['bits'],0] for row in case['bits']]
         +[[1,row['n'],0] for row in case['below']]
         +[[2,len(row['pool']),row['k']] for row in case['samples']])

def expected_for(case):
 rows=[[v] for v in case['words']]+[[r['value']] for r in case['bits']]+[[r['value']] for r in case['below']]+[r['result'] for r in case['samples']]
 return [v for row in rows for v in row+[0xffffffff]*(5-len(row))]

if __name__=='__main__':verify()
