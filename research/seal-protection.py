"""Audit full common protection proofs without declaring full-catalog support."""
import argparse,copy,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path.insert(0,str(P))
from protection_source_equivalence import equivalence
s=importlib.util.spec_from_file_location('normalize_generated',P/'seal-stack-increment.py');helper=importlib.util.module_from_spec(s);s.loader.exec_module(helper)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','e96a546:research/'+n+'.json'],cwd=R))
