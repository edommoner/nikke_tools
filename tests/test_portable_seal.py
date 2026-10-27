"""Independent sealing must use a fresh comparison exactly once, never old JSON."""
import os,hashlib,json,tempfile,subprocess
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('seal_test_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class SealTests(unittest.TestCase):
    def test_seal_budget_rejects_invalid_values_before_child_or_io(self):
        for timeout in (0,-1,241,True,1.5,'90'):
            with self.subTest(timeout=timeout),patch.object(cli.subprocess,'run') as run,self.assertRaisesRegex(ValueError,'CPU seal timeout'):
                cli.seal_development(Path('unused'),Path('unused'),Path('unused'),timeout=timeout)
            run.assert_not_called()
    def test_original_comparison_runs_once_and_is_used_without_changes(self):
        result=dict(entries=[dict(native_sha256='fresh')],calculation_verified=True)
        compare=Mock(return_value=result)
        module=SimpleNamespace(compare_readback=compare)
        audit=dict(calculation_verified=True)
        def audited(capture):
            self.assertEqual(capture,'capture')
            self.assertIs(module.compare_readback('manifest',capture),result)
            return audit
        module.audit_capture=audited
        actual,comparison=cli.audited_comparison(module,'capture')
        self.assertIs(actual,audit);self.assertIs(comparison,result)
        compare.assert_called_once_with('manifest','capture')
        self.assertIs(module.compare_readback,compare)

    def test_old_report_or_multiple_comparisons_cannot_be_sealed(self):
        for calls,passed in ((0,True),(2,True),(1,False)):
            compare=Mock(return_value=dict(calculation_verified=passed))
            module=SimpleNamespace(compare_readback=compare)
            def audit(capture):
                for _ in range(calls):module.compare_readback('manifest',capture)
                return dict(calculation_verified=passed)
            module.audit_capture=audit
            with self.subTest(calls=calls,passed=passed),self.assertRaisesRegex(ValueError,'exactly one'):
                cli.audited_comparison(module,'capture')
            self.assertEqual(compare.call_count,calls);self.assertIs(module.compare_readback,compare)

    def test_comparator_failure_is_preserved_and_binding_restored(self):
        compare=Mock(side_effect=ValueError('Raw mismatch'))
        module=SimpleNamespace(compare_readback=compare)
        module.audit_capture=lambda capture:module.compare_readback('manifest',capture)
        with self.assertRaisesRegex(ValueError,'Raw mismatch'):cli.audited_comparison(module,'capture')
        self.assertIs(module.compare_readback,compare)

    def test_rejected_independent_result_exposes_actual_mismatch_without_retry(self):
        mismatch=dict(name='original',reason='late landing differs')
        compare=Mock(return_value=dict(calculation_verified=False,mismatches=[mismatch]))
        module=SimpleNamespace(compare_readback=compare)
        def audit(capture):
            module.compare_readback({},capture)
            return dict(calculation_verified=False,first_difference=mismatch)
        module.audit_capture=audit
        with self.assertRaisesRegex(ValueError,'late landing differs'):cli.audited_comparison(module,'capture')
        compare.assert_called_once();self.assertIs(module.compare_readback,compare)

    def test_nested_observer_error_is_not_hidden_by_cleanup_guard(self):
        try:
            try:raise AssertionError('missing actual creation receipt')
            finally:raise ValueError('profiler changed during cleanup')
        except ValueError as error:
            self.assertEqual(cli.comparison_exception_details(error),'ValueError: profiler changed during cleanup | caused by AssertionError: missing actual creation receipt')
        self.assertEqual(cli.comparison_exception_details(ValueError('ordinary')),'ValueError: ordinary')
        cyclic=ValueError('cycle');cyclic.__cause__=cyclic
        self.assertEqual(cli.comparison_exception_details(cyclic),'ValueError: cycle')

    def test_failed_child_and_timeout_preserve_full_utf8_outputs_without_success(self):
        for error in (subprocess.CalledProcessError(1,['fixture'],output='partial stdout',stderr='失敗の詳細'),
                      subprocess.TimeoutExpired(['fixture'],30,output=b'partial timeout',stderr='中断'.encode())):
            with self.subTest(error=type(error).__name__),tempfile.TemporaryDirectory() as tmp:
                with patch.object(cli.subprocess,'run',side_effect=error) as run:
                    with self.assertRaisesRegex(RuntimeError,'preserved logs') as caught:cli.audit_saved_metal(Path(tmp),Path(tmp)/'capture',timeout=30)
                run.assert_called_once();self.assertIs(caught.exception.__cause__,error)
                folders=list(Path(tmp).glob('nikke-independent-audit-failure-*'));self.assertEqual(len(folders),1)
                expected=error.stderr.decode() if isinstance(error.stderr,bytes) else error.stderr
                self.assertEqual((folders[0]/'stderr.log').read_text(encoding='utf-8'),expected)
                facts=json.loads((folders[0]/'failure.json').read_text());self.assertFalse(facts['calculation_verified']);self.assertEqual(facts['gpu_calls'],0)


    def test_independent_seal_uses_package_relative_oracle_from_another_checkout(self):
        # Old research adapters contain relative spec_from_file_location paths.
        # Use a real child interpreter and different oracles in both checkouts.
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);package=base/'package';other=base/'other';capture=base/'capture'
            for root in (package,other):
                (root/'research').mkdir(parents=True);(root/'gpu').mkdir()
                (root/'gpu/proof.slang').write_text('same GPU source')
            (package/'research/oracle.py').write_text("LABEL='package'\n")
            (other/'research/oracle.py').write_text("LABEL='other'\n")
            digest=hashlib.sha256((package/'gpu/proof.slang').read_bytes()).hexdigest()
            (package/'scripts').mkdir();capture.mkdir();(capture/'run.json').write_text('{"backend":"metal"}')
            fake="""import json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads(path.read_text())
def verify_package(root):return dict(package_id='frozen',purpose='development',golden=dict(source_sha256={'gpu/proof.slang':DIGEST}))
def is_development(manifest):return manifest['purpose']=='development'
def compare_readback(capture):
    label=runpy.run_path('research/oracle.py')['LABEL']
    if label!='package':raise ValueError('Imported oracle from another checkout')
    return dict(input_sha256='input',output_sha256='output',entries=[dict(name=label)],generated_normalized={},calculation_verified=True)
def audit_capture(capture):
    compare_readback(capture)
    return dict(calculation_verified=True)
""".replace('DIGEST',repr(digest))
            (package/'scripts/nikke_gpu.py').write_text(fake)
            output=base/'sealed.json'
            previous=Path.cwd()
            try:
                os.chdir(other)
                with patch.object(cli,'ROOT',other),patch.object(cli.subprocess,'run',wraps=subprocess.run) as child:
                    result=cli.seal_development(package,capture,output,timeout=90)
                    self.assertEqual(child.call_args.kwargs['timeout'],90)
            finally:os.chdir(previous)
            self.assertTrue(result['sealed']);self.assertEqual(result['gpu_calls'],0)
            self.assertEqual(json.loads(output.read_text())['entries'],[dict(name='package')])
            (package/'scripts/nikke_gpu.py').write_text(fake.replace("purpose='development'","purpose='sealed'"))
            with patch.object(cli,'ROOT',other):
                audited=cli.audit_saved_metal(package,capture,timeout=90)
                self.assertEqual(audited['package_id'],'frozen')
                with self.assertRaisesRegex(RuntimeError,'preserved logs') as failed:cli.seal_development(package,capture,base/'not-development.json',timeout=90)
                self.assertIsInstance(failed.exception.__cause__,subprocess.CalledProcessError)
            self.assertFalse((base/'not-development.json').exists())


    def receipt_result(self):
        return dict(package_id='fixture',golden=dict(entries=[dict(name='case')],input_sha256='0'*64,output_sha256='1'*64),audit=dict(calculation_verified=True),independent_comparison=dict(child_pid=os.getpid()+10000,input_count=1,native_cases=1,live_parent_receipt_present=False),independent_audit_seconds=.5)

    def test_same_fresh_audit_can_publish_a_receipt_without_a_second_comparison(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(cli,'audit_saved_metal',return_value=self.receipt_result()) as audit:
            root=Path(tmp);receipt=root/'receipt.json';result=cli.seal_development(root,root/'capture',root/'golden.json',audit_receipt=receipt)
            audit.assert_called_once();saved=json.loads(receipt.read_text());self.assertTrue(saved['calculation_verified']);self.assertFalse(saved['live_parent_receipt_present']);self.assertEqual(saved['native_cases'],1);self.assertEqual(saved['gpu_calls'],0)
            self.assertEqual(result['audit_receipt_sha256'],hashlib.sha256(receipt.read_bytes()).hexdigest())

    def test_receipt_rejects_missing_counts_reuse_owner_and_unbounded_time_before_outputs(self):
        for label,change in [('missing',{'native_cases':None}),('reused',{'live_parent_receipt_present':True}),('owner',{'child_pid':os.getpid()}),('count',{'input_count':True})]:
            value=self.receipt_result();value['independent_comparison'].update(change)
            with self.subTest(label=label),tempfile.TemporaryDirectory() as tmp,patch.object(cli,'audit_saved_metal',return_value=value):
                root=Path(tmp)
                with self.assertRaisesRegex(ValueError,'fresh child'):cli.seal_development(root,root/'capture',root/'golden.json',audit_receipt=root/'receipt.json')
                self.assertFalse((root/'golden.json').exists());self.assertFalse((root/'receipt.json').exists())
        value=self.receipt_result();value['independent_audit_seconds']=1000
        with tempfile.TemporaryDirectory() as tmp,patch.object(cli,'audit_saved_metal',return_value=value):
            root=Path(tmp)
            with self.assertRaisesRegex(ValueError,'bounded elapsed'):cli.seal_development(root,root/'capture',root/'golden.json',audit_receipt=root/'receipt.json')
            self.assertFalse((root/'golden.json').exists())

    def test_receipt_targets_must_be_fresh_and_distinct_before_audit(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(cli,'audit_saved_metal') as audit:
            root=Path(tmp);target=root/'golden.json'
            with self.assertRaisesRegex(ValueError,'distinct'):cli.seal_development(root,root/'capture',target,audit_receipt=target)
            receipt=root/'receipt.json';receipt.write_text('original')
            with self.assertRaises(FileExistsError):cli.seal_development(root,root/'capture',target,audit_receipt=receipt)
            audit.assert_not_called();self.assertEqual(receipt.read_text(),'original')

if __name__=='__main__':unittest.main()
