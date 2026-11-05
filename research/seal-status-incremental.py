"""Historical8c1735b sealer; requires matching pre-optimization source/reports.
Use seal-status.py for the final optimized source.
"""
import argparse,copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='8c1735b'
s=importlib.util.spec_from_file_location('old_sealer',P/'seal-stack-increment.py');old_sealer=importlib.util.module_from_spec(s);s.loader.exec_module(old_sealer)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','3f661c8:research/'+n+'.json'],cwd=R))
