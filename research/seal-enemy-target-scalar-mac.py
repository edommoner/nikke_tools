"""Seal frozen common source proofs without GPU execution or tolerance changes."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path('/Users/edo/Documents/ChatGPT/nikke_tools');P=ROOT/'research'
SOURCE='73570451569dce424667e37f4729e475ea6b0a86';PRIOR='89c19e32c7951a839a9db1970403dd299ad66a4b'
def load(n):return json.loads((P/(n+'.json')).read_text())
def git_bytes(p,c=SOURCE):return subprocess.check_output(['git','show',c+':'+p],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
TRACKED=None;PINNED=None
def check_hashes(d,groups=('source_sha256','validation_sha256')):
 global TRACKED,PINNED
 if TRACKED is None:
  TRACKED=set(subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE],cwd=ROOT,text=True).splitlines())
  PINNED=json.loads(git_bytes('research/portable-roster-battles-metal.json',PRIOR))['validation_sha256']
 for group in groups:
  for p,digest in d.get(group,{}).items():
   assert file_sha(ROOT/p)==digest,(group,p)
   if p in TRACKED:assert sha(git_bytes(p))==digest,(group,p)
   else:assert p.startswith('research/upstream/nikke-calc-master/') and PINNED.get(p)==digest,('pinned upstream',group,p)
