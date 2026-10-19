"""One bounded invocation: current full common dispatch and two boundary programs."""
import argparse,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];a=argparse.ArgumentParser();a.add_argument('--backend',choices=('cuda','metal'),required=True);args=a.parse_args()
for script in ('verify-status-regression.py','verify-status-clear-boundaries.py'):
 subprocess.run([sys.executable,str(R/'research'/script),'--backend',args.backend],cwd=R,check=True)
