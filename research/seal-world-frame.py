"""CPU-only audit of fixed-source isolated frame/attack coupling evidence."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='57c2a340ea4c0c13261bc2659d7e3dae28288693'
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while data:=f.read(8*1024*1024):h.update(data)
 return h.hexdigest()
def load(name):return json.loads((P/(name+'.json')).read_text())
def git(path):return subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)
