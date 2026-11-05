"""One fixture packer and comparison for portable GPU backends; no CPU replay."""
import argparse,hashlib,json,platform,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/portable-probe.json'


def pack_cases(cases):
    if not 1<=len(cases)<=64:raise ValueError('Probe requires 1..64 cases')
    words=[len(cases)]
    for case in cases:
        steps=case['steps'];expected=case['expected']
        if not 1<=len(steps)<=16 or len(expected)!=7:raise ValueError('Invalid probe dimensions')
        for row in steps:
            if len(row)!=6 or any(type(v) is not int or not 0<=v<2**32 for v in row) or not 1<=row[0]<=6:raise ValueError('Invalid probe command')
            if row[0]==4 and (row[5]==0 or row[3]<=row[2]):raise ValueError('Invalid clock interval/lifetime')
        if any(type(v) is not int or not 0<=v<2**32 for v in expected):raise ValueError('Invalid expected output')
        words += [len(steps)]+[v for row in steps for v in row]+[0]*((16-len(steps))*6)
    return struct.pack('<'+'I'*len(words),*words)
