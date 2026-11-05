"""Seal current fixed-source Mac proofs; never dispatch GPU or waive differences."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='39bce8aa5c9c5f29f0653e80fc69855f19ad5ad6'
PRIOR='d181fcd9ec57734bac2b3e08c75d828509a8b668'
def load(n):return json.loads((P/(n+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(path,commit=SOURCE):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while chunk:=f.read(8*1024*1024):h.update(chunk)
 return h.hexdigest()
