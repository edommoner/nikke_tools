"""Owned Windows Job cleanup order and budget, without Windows or a GPU."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import types
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cleanup_bounded',ROOT/'research/run-world-bounded.py')
bounded=importlib.util.module_from_spec(spec);spec.loader.exec_module(bounded)


class WindowsCleanupTests(unittest.TestCase):
    def job(self, counts=(0,), wait_error=None):
        events=[];remaining=iter(counts)
        def terminate(handle,code):events.append('terminate');return True
        def query(handle,kind,buffer,size,out):
            events.append('query');struct.pack_into('<II',buffer,0,1,next(remaining));return True
        def wait(timeout):
            self.assertEqual(events[0],'terminate');self.assertGreater(timeout,0);self.assertLessEqual(timeout,5)
            events.append('wait')
            if wait_error:raise wait_error
        job=bounded.WindowsJob.__new__(bounded.WindowsJob)
        job.handle=123;job.termination_waited=False;job.termination_attempted=False
        job.process=types.SimpleNamespace(wait=wait)
        job.dll=types.SimpleNamespace(TerminateJobObject=terminate,QueryInformationJobObject=query,
            CloseHandle=lambda handle:events.append('close') or True)
        return job,events

    def test_descendants_must_disappear_after_child_exit_before_handle_close(self):
        job,events=self.job((2,0));job.terminate_and_wait();self.assertTrue(job.termination_waited)
        self.assertEqual(events,['terminate','wait','query','query'])
        job.close();job.close();self.assertEqual(events[-1],'close');self.assertEqual(events.count('terminate'),1)

    def test_child_wait_timeout_closes_job_without_starting_a_second_cleanup_budget(self):
        job,events=self.job(wait_error=subprocess.TimeoutExpired('child',5))
        with self.assertRaises(subprocess.TimeoutExpired):job.close()
        self.assertEqual(events,['terminate','wait','close']);self.assertIsNone(job.handle)
        self.assertFalse(job.termination_waited)

    @unittest.skipUnless(os.name=='nt','Windows JobObject integration; GPU0')
    def test_real_windows_timeout_observes_empty_owned_job_after_descendant_exit(self):
        from windows_validation_observer import observe_job
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            code="""import pathlib,subprocess,sys,time
p=pathlib.Path(sys.argv[1])
while not (p/'start.json').exists():time.sleep(.01)
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
(p/'descendant.pid').write_text(str(child.pid))
time.sleep(30)
"""
            with observe_job(bounded,root/'job.json'):
                interpreter=getattr(sys,'_base_executable',sys.executable)
                env=os.environ.copy();env.pop('__PYVENV_LAUNCHER__',None)
                facts=bounded.run_bounded([interpreter,'-c',code,str(root)],root,2,env=env)
            diagnostic=json.dumps(dict(execution=facts,job=json.loads((root/'job.json').read_text()),stderr=(root/'stderr.log').read_text(errors='replace')))
            self.assertTrue(facts['timed_out'],diagnostic);self.assertFalse(facts['passed'])
            self.assertTrue((root/'descendant.pid').exists(),diagnostic)
            self.assertIsNone(facts['cleanup_error']);self.assertIsNotNone(facts['final_child_exit_code'])
            row=json.loads((root/'job.json').read_text())['records'][0]
            self.assertTrue(row['pre_gate_verified']);self.assertIsNone(row['inspection_error'])
            self.assertEqual(row['post_wait']['job_members'],[])
            self.assertLessEqual(row['post_wait']['observed_unix_ns'],facts['wait_completed_unix_ns'])
            self.assertIsNotNone(row['post_wait']['job_peak_memory_bytes'])


if __name__=='__main__':unittest.main()
