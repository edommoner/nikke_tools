"""Seal the verified baseline before adopting the selected optimization.
The initial unlocalized Metal mismatch is retained as an open finding.
"""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='14c8e2e61fd6eeb9950a13c76f217ae62ca82fd9';PRIOR='ce01fad'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
