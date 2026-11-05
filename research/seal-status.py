"""Verify and seal shared status evidence while retaining the unfinished full goal."""
import copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='d2ba01a'
s=importlib.util.spec_from_file_location('previous_sealer',P/'seal-stack-increment.py');previous=importlib.util.module_from_spec(s);s.loader.exec_module(previous)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','3f661c8:research/'+n+'.json'],cwd=R))
