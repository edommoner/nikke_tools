"""Real BossScript pools and source quota combined without a distance guess."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests','scripts')]
s=importlib.util.spec_from_file_location('lock_executor_suite',ROOT/'research/verify-generation-locks.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class LockExecutorTests(unittest.TestCase):
 def test_distinct_quota_changes_do_not_evict_frozen_snapshot(self):
  c=suite.fixtures()[0];r=suite.observe(c)
  self.assertEqual([x[0] for x in r['receipts'].values()],[15]*16+[5])
  self.assertEqual([x[1] for x in r['receipts'].values()],list(range(1,16))+[15,15])
  self.assertEqual(r['snapshots'][30],r['snapshots'][31]);self.assertEqual(len(r['snapshots'][31]['handles']),15)
 def test_live_generation_changes_and_explicit_clears(self):
  rows={c['name'].split('/')[-1]:c for c in suite.fixtures()}
  r=suite.observe(rows['frozen-candidate-stale-generation'])
  self.assertEqual(r['snapshots'][30]['handles'],[])
  self.assertEqual(r['snapshots'][31]['handles'],[[5,0,3]])
  for reason in (1,2):
   r=suite.observe(rows['clear-'+str(reason)])
   self.assertEqual(r['snapshots'][30]['handles'],r['snapshots'][31]['handles'])
   self.assertEqual(r['snapshots'][31]['revision'],3)
 def test_complete_provider_capacity_and_default_observer_retention(self):
  c=suite.fixtures()[-1];w,m,b=suite.compile_case(c);r=suite.observe(c)
  self.assertEqual(len(b),128);self.assertEqual(len(r['snapshots'][31]['handles']),24)
  self.assertEqual(r['pool'],suite.parent.manual.native(c,suite.L))
 def test_cpu_oracles_do_not_build_or_execute_gpu(self):
  from unittest.mock import patch
  import portable_backend
  with patch.object(portable_backend,'build',side_effect=AssertionError('GPU forbidden')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
   entries,data=suite.prepare();self.assertEqual(len(entries),16)
   for _,_,domain in entries:
    if domain:suite.native_reference(domain)
if __name__=='__main__':unittest.main()
