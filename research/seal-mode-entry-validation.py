"""Completed shared-runtime correctness and isolated efficiency decision; no GPU."""
import datetime,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='39bce8aa5c9c5f29f0653e80fc69855f19ad5ad6'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,r):(P/(n+'.json')).write_text(json.dumps(r,indent=2)+'\n')
