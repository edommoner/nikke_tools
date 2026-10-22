"""Real optimized CLI must fail closed, retain evidence, and never execute native."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class OptimizedReferenceTests(unittest.TestCase):
    def test_cli_separates_positive_contracts_from_known_reference_model_gaps(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'reference.json'
            result=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'reference','--suite','parts-skill-extended','--out',str(output)],cwd=ROOT,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output.read_text());summary=json.loads(result.stdout)
            for record in (report,summary):
                self.assertEqual(record['case_count'],10)
                self.assertEqual(record['positive_contract_cases'],9)
                self.assertEqual(record['reference_model_gap_cases'],1)
                self.assertFalse(record['calculation_verified']);self.assertFalse(record['gpu_supported'])
            self.assertEqual(sum(c['contract'].get('reference_model_gap') is True for c in report['cases']),1)

    def test_cli_rejects_optimized_python_and_preserves_failure(self):
        for flag in ('-O','-OO'):
            with self.subTest(flag=flag),tempfile.TemporaryDirectory() as folder:
                output=Path(folder)/'reference.json'
                command=[sys.executable,flag,str(ROOT/'scripts/nikke_gpu.py'),'reference','--suite','parts-skill','--out',str(output)]
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=15)
                self.assertNotEqual(result.returncode,0)
                report=json.loads(output.read_text());original=output.read_bytes()
                self.assertFalse(report['passed']);self.assertFalse(report['cpu_reference_verified'])
                self.assertEqual(report['cases'],[]);self.assertNotIn('source_sha256',report)
                self.assertEqual(report['gpu_calls'],dict(build=0,execute=0));self.assertEqual(report['packing_calls'],0)
                self.assertIn('optimized Python is forbidden',report['error'])
                again=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=15)
                self.assertNotEqual(again.returncode,0);self.assertEqual(output.read_bytes(),original)

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
