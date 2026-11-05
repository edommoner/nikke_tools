"""Audit scoped world-notice proof; retain pending global/CUDA/full-world work."""
import hashlib,json,subprocess,sys,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import source_hashes

def load(path):return json.loads((ROOT/path).read_text())
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  while block:=stream.read(8*1024*1024):h.update(block)
 return h.hexdigest()
def previous(commit,path):return json.loads(subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT))
def equal(a,b):
 assert Path(a).read_bytes()==Path(b).read_bytes(),(a,b)
 return dict(previous=str(a),current=str(b),sha256=sha(b),all_bytes_equal=True)
