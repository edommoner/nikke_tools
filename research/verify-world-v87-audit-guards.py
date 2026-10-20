"""Reject missing/contradictory metadata without editing stored GPU evidence."""
import importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('audit87_guards',ROOT/'research/seal-world-v87-cuda.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
def main():
 original_read=Path.read_text;original_audit=d.audit;results=[]
 def check(label,mutator=None,wrong_bound=False):
  def read(path,*args,**kwargs):
   text=original_read(path,*args,**kwargs)
   if mutator and path.name in ('portable-cross-v87-receipt.json','windows-portable-world-v87-summary.json'):
    data=json.loads(text);mutator(path.name,data);return json.dumps(data)
   return text
  def audit(**kwargs):
   if wrong_bound:kwargs['summary_omission_counts']={'old484':68}
   return original_audit(**kwargs)
  rejected=False
  with patch.object(Path,'read_text',read),patch.object(d,'audit',audit):
   try:d.main()
   except (AssertionError,KeyError):rejected=True
  assert rejected,label;results.append(dict(name=label,rejected=True))
 def missing(name,data):
  if name=='portable-cross-v87-receipt.json':data.pop('old484_execution_count')
 def positive(name,data):
  if name=='portable-cross-v87-receipt.json':data['old484_execution_count']=1
 def wrong_count(name,data):
  if name=='windows-portable-world-v87-summary.json':data['evidence']['transport']['cases']=484
 def wrong_command(name,data):
  if name=='portable-cross-v87-receipt.json':data['bounded_driver']['shared_gpu_command']='python research/verify-world-actor-recipients.py --backend cuda'
 try:
  check('summary omission plus missing receipt is rejected',missing);check('positive old484 execution count is rejected',positive);check('different physical dispatch count is rejected',wrong_count);check('different fixed command is rejected',wrong_command);check('non-smaller suite cannot establish omission',wrong_bound=True)
 finally:d.main()
 (ROOT/'research/portable-world-v87-audit-guards.json').write_text(json.dumps(dict(passed=True,cases=results,original_gpu_json_modified=False,gpu_executions=0),indent=2)+'\n');print('Five audit counter omission/contradiction guards passed;stored GPU evidence unchanged;GPU0')
if __name__=='__main__':main()
