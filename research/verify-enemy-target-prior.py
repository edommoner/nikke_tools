"""Exact old4070 readback preservation with valid ABI72 ->73 only; no decode normalization."""
import array,datetime,hashlib,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
import portable_runtime as runtime
from portable_specs import LIMITS as L
from portable_enemy_target_specs import ABI

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
