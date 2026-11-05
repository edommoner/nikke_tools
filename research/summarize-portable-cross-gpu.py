"""Compact exact comparisons while complete reports/raw remain on each host."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=ROOT/'research/portable-cross-v79-expected.json'

def load(path):return json.loads(Path(path).read_text())
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized(raw):
 text=raw.decode().replace('\r\n','\n').replace('\r','\n');text='\n'.join(x for x in text.split('\n') if not re.match(r'^\s*#line\b',x))
 return hashlib.sha256(re.sub(r'(?m)^#include "[^"\n]*slang-cuda-prelude.h"','#include "slang-cuda-prelude.h"',text).encode()).hexdigest()
