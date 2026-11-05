"""Real optimized CLI must fail closed, retain evidence, and never execute native."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class OptimizedReferenceTests(unittest.TestCase):
    pass


    def test_direct_parts_contract_still_rejects_bad_native_under_optimization(self):
        code="""import sys
sys.path[:0]=['app','research','scripts']
import engine_worker
from portable_parts_skill_cases import fixtures
from portable_parts_skill_contracts import verify
try:verify(fixtures()[2],{'damage':[],'parts_skill_events':[]})
except AssertionError:print('rejected')
else:raise RuntimeError('Invalid native was certified')
"""
        result=subprocess.run([sys.executable,'-O','-c',code],cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),'rejected')
