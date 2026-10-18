"""Reusable isolated old/new CPU comparison over explicitly provided inputs."""
import argparse,importlib.abc,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--archive',required=True);parser.add_argument('--inputs',required=True);parser.add_argument('--output',required=True);parser.add_argument('--side',choices=['before','after']);args=parser.parse_args()
archive=(ROOT/args.archive).resolve();inputs=ROOT/args.inputs;output=ROOT/args.output
assert archive.is_dir() and (archive/'app/engine_worker.py').is_file()
class Loader(importlib.abc.Loader):
 def __init__(self,path):self.path=path
 def create_module(self,spec):return None
 def exec_module(self,module):
  module.__file__=str(ROOT/'app'/self.path.name);exec(compile(self.path.read_bytes(),module.__file__,'exec'),module.__dict__)
class Finder(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  source=archive/'app'/(name+'.py')
  if '.' not in name and source.exists():return importlib.util.spec_from_loader(name,Loader(source))
def side_path(side):return output.with_name(output.stem+'-'+side+'.json')
if args.side:
 sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
 if args.side=='before':sys.meta_path.insert(0,Finder())
 import engine_worker
 rows={name:engine_worker.evaluate(body) for name,body in json.loads(inputs.read_text(encoding='utf-8'))}
 side_path(args.side).write_text(json.dumps(rows,ensure_ascii=False)+'\n',encoding='utf-8')
else:
 for side in ('before','after'):subprocess.run([sys.executable,__file__,'--archive',args.archive,'--inputs',args.inputs,'--output',args.output,'--side',side],cwd=ROOT,check=True)
 before=json.loads(side_path('before').read_text(encoding='utf-8'));after=json.loads(side_path('after').read_text(encoding='utf-8'));assert before.keys()==after.keys()
 fields=('total_damage','members','burst_timeline','base_stats','boss_timeline','burst_policy','shooting_policy','burst_gauge_mode')
 rows=[dict(name=name,checks={field:old.get(field)==after[name].get(field) for field in fields}) for name,old in before.items()]
 passed=all(all(row['checks'].values()) for row in rows)
 report=dict(passed=passed,archive=args.archive,inputs=args.inputs,cases=rows,scope='Independent old/new CPU regression evidence only; archived behavior is not in-game authority.')
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=passed,cases=len(rows))))
 raise SystemExit(0 if passed else 1)
