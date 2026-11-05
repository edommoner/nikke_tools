"""Isolated target-selection/ordered damage connection; root production files unchanged."""
import datetime,hashlib,io,json,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
from portable_enemy_target_specs import ABI,META_BASE,COMMAND_BASE,RNG_BASE,RNG_WORDS,QUERY_BASE
BASE='89c19e3'
def patch(p,a,b):
 s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
