"""Audit fixed-source Mac gates and separate physical proof;never dispatch GPU."""
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE=subprocess.check_output(['git','rev-parse','0ae6a14'],cwd=ROOT,text=True).strip()
PRIOR='ba9015c41157c4fa698422ee3638a1ba4f4fba19'
def load(n):return json.loads((P/(n+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(path,commit=SOURCE):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while chunk:=f.read(8*1024*1024):h.update(chunk)
 return h.hexdigest()
