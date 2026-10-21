"""CPU fault injection for redaction, PID reuse and fresh validation job evidence."""
import json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
import windows_validation_observer as observer
from windows_validation_observer import normalize_snapshot,compare_snapshots,observe_job

class WindowsEvidence(unittest.TestCase):
 def snapshot(self,rows,listeners=()):return normalize_snapshot(rows,listeners,'C:/original/nikke','C:/isolated/v102')
 def row(self,pid=4,creation='100',command='python C:/original/nikke/app/gpu_service.py --secret TOKEN'):
  return dict(ProcessId=pid,ParentProcessId=1,Name='python.exe',ExecutablePath='C:/python.exe',CreationTicks=creation,CommandLine=command)
 def test_classification_redacts_command_lines_and_secrets(self):
  r=self.snapshot([self.row()]);self.assertEqual(r['service_status'],'identified');self.assertEqual(r['nikke_service_pids'],[4]);self.assertNotIn('TOKEN',json.dumps(r));self.assertNotIn('CommandLine',json.dumps(r))
 def test_generic_runtime_path_is_not_service_identification(self):
  r=self.snapshot([self.row(command='python -m unrelated_worker')]);self.assertEqual(r['service_status'],'absent');self.assertFalse(r['nikke_service_pids'])
 def test_missing_command_line_does_not_prove_service_absence(self):
  before=self.snapshot([self.row(command=None)]);self.assertEqual(before['service_status'],'unverified');self.assertFalse(compare_snapshots(before,before)['identified_nikke_service_preservation_verified'])
 def test_pid_reuse_does_not_prove_service_preservation(self):
  a=self.snapshot([self.row()]);b=self.snapshot([self.row(creation='101')]);r=compare_snapshots(a,b);self.assertFalse(r['identified_nikke_service_preservation_verified']);self.assertEqual(len(r['missing_existing_processes']),1)
 def test_unrelated_missing_process_is_reported_even_if_service_is_preserved(self):
  a=self.snapshot([self.row(),self.row(pid=8,command='python unrelated_mcp.py')]);b=self.snapshot([self.row()]);r=compare_snapshots(a,b);self.assertTrue(r['identified_nikke_service_preservation_verified']);self.assertFalse(r['all_monitored_processes_preserved']);self.assertEqual(r['termination_cause'],'unknown')
 def test_snapshot_does_not_report_its_own_short_lived_observer_as_lost_work(self):
  before=normalize_snapshot([self.row(pid=os.getpid(),command='python C:/preflight.py'),self.row(pid=123,command='venv-python C:/preflight.py')],[],'C:/original/nikke','C:/isolated/v102',observer_script='C:/preflight.py');after=self.snapshot([]);self.assertEqual([r['role'] for r in before['processes']],['observer','observer']);self.assertTrue(compare_snapshots(before,after)['all_monitored_processes_preserved'])
 def job(self):
  state=dict(closed=0,terminated=False,events=[])
  class Job:
   def __init__(self,process):self.handle=123
   def terminate_and_wait(self,timeout=5):
    state['events'].append('terminated');state['terminated']=True;self.termination_waited=True
   def close(self):
    if self.handle:state['closed']+=1;self.handle=None
  return types.SimpleNamespace(WindowsJob=Job),state
 def test_single_fresh_child_is_saved_before_gate_and_close_always_occurs(self):
  module,state=self.job();counter=[]
  def read(job,process):
   counter.append(1);state['events'].append('inspect')
   return dict(child_pid=7,child_ppid=os.getpid(),child_creation_filetime_ticks='12345',job_members=[] if state['terminated'] else [7])
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'job.json'
   with observe_job(module,path,read):
    job=module.WindowsJob(types.SimpleNamespace(pid=7));self.assertTrue(json.loads(path.read_text())['records'][0]['pre_gate_verified']);job.close()
   r=json.loads(path.read_text());self.assertFalse(r['observer_assigns_processes']);self.assertEqual(r['records'][0]['post_wait']['job_members'],[]);self.assertEqual(state['closed'],1)
   self.assertEqual(state['events'],['inspect','terminated','inspect'])
 def test_foreign_member_prevents_gate_proof_and_closes_only_owned_job(self):
  module,state=self.job()
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'job.json'
   with observe_job(module,path,lambda j,p:dict(child_pid=7,child_ppid=os.getpid(),child_creation_filetime_ticks='12345',job_members=[7,999])):
    with self.assertRaisesRegex(RuntimeError,'membership'):module.WindowsJob(types.SimpleNamespace(pid=7))
   self.assertFalse(json.loads(path.read_text())['records'][0]['pre_gate_verified']);self.assertEqual(state['closed'],1)
 def test_post_observation_failure_is_saved_without_skipping_cleanup(self):
  module,state=self.job();counter=[]
  def read(job,process):
   counter.append(1)
   if len(counter)>1:raise OSError('injected read failure')
   return dict(child_pid=7,child_ppid=os.getpid(),child_creation_filetime_ticks='12345',job_members=[7])
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'job.json'
   with observe_job(module,path,read):module.WindowsJob(types.SimpleNamespace(pid=7)).close()
   self.assertEqual(state['closed'],1);self.assertEqual(json.loads(path.read_text())['records'][0]['inspection_error'],'OSError')
 def test_wrong_parent_prevents_gate_proof(self):
  module,state=self.job()
  with tempfile.TemporaryDirectory() as folder:
   with observe_job(module,Path(folder)/'job.json',lambda j,p:dict(child_pid=7,child_ppid=-1,child_creation_filetime_ticks='12345',job_members=[7])):
    with self.assertRaisesRegex(RuntimeError,'identity'):module.WindowsJob(types.SimpleNamespace(pid=7))
   self.assertEqual(state['closed'],1)
 def test_failed_evidence_write_cannot_skip_owned_job_cleanup(self):
  module,state=self.job()
  with tempfile.TemporaryDirectory() as folder,patch.object(observer.os,'fsync',side_effect=OSError('injected disk failure')):
   with self.assertRaises(OSError):
    with observe_job(module,Path(folder)/'job.json',lambda j,p:dict(child_pid=7,child_ppid=os.getpid(),child_creation_filetime_ticks='12345',job_members=[7])):module.WindowsJob(types.SimpleNamespace(pid=7))
   self.assertEqual(state['closed'],1)
if __name__=='__main__':unittest.main()
