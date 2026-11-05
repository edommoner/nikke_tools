"""Seal current split proofs without declaring full-catalog GPU certification."""
import argparse,copy,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path.insert(0,str(R/'app'))
from portable_specs import ABI,LIMITS as L
s=importlib.util.spec_from_file_location('normalizer',P/'seal-stack-increment.py');helper=importlib.util.module_from_spec(s);s.loader.exec_module(helper)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def old(n):return json.loads(subprocess.check_output(['git','show','b8ae1c7:research/'+n+'.json'],cwd=R))
def case_sha(c):return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
