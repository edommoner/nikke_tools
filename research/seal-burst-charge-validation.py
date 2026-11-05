"""Seal completed shared burst-charge validation and the measured optimization decision."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research';SOURCE='20e213bf28544a3ad2709fdc852d239eed108b5e'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
