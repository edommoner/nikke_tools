"""Run the unchanged full selection, testing a new mechanism first.

Only module order changes. Every selected test remains, with its original
assertions and full runner source guards. No separate duplicate GPU test run.
"""
import argparse,hashlib,json,runpy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--first',nargs='+',required=True);parser.add_argument('--receipt',required=True);args=parser.parse_args()
original=unittest.defaultTestLoader.loadTestsFromNames
def prioritize(names,module=None):
 names=list(names);assert len(set(args.first))==len(args.first) and all(names.count(name)==1 for name in args.first),'Prioritized modules must belong to the full selection exactly once'
 ordered=args.first+[name for name in names if name not in args.first]
 assert sorted(names)==sorted(ordered) and len(set(names))==len(names),'Do not add/drop/duplicate test modules'
 receipt=dict(selection='full',same_modules=True,original_order=names,execution_order=ordered,runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (ROOT/args.receipt).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 return original(ordered,module)
unittest.defaultTestLoader.loadTestsFromNames=prioritize
sys.argv=[str(ROOT/'scripts/verify-normal-detail.py'),'--scope','full']
try:runpy.run_path(sys.argv[0],run_name='__main__')
finally:unittest.defaultTestLoader.loadTestsFromNames=original
