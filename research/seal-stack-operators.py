"""Seal v51 component evidence without certifying the unfinished full catalog."""
import copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ba890da'
spec=importlib.util.spec_from_file_location('previous_sealer',P/'seal-stack-increment.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','029aa07:research/'+n+'.json'],cwd=R))
