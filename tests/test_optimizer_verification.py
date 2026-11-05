"""Deferred/full boundary, capture binding and fresh verification, no GPU claims."""
import copy,hashlib,io,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_portable_detail as fixtures
import portable_detail as product
import portable_detail_service as service

class DeferredVerification(unittest.TestCase):
    harness=fixtures.ProductBatchProtocol.harness
    bodies=fixtures.ProductBatchProtocol.bodies

    def test_deferred_skips_cpu_for_each_shared_backend_and_keeps_payload(self):
        for backend,requested in [('native','native_detail')]:
            with self.subTest(backend=backend),tempfile.TemporaryDirectory() as folder,self.harness(folder,backend=backend) as (_,events):
                rows=product.evaluate_many(self.bodies(3,requested),verification='deferred')
                self.assertFalse(any(isinstance(e,tuple) for e in events))
                for row in rows:
                    result=row['result'];self.assertEqual(result['compute']['cpu_verification'],{'status':'pending'})
                    path=Path(folder)/result['compute']['capture_id']
                    self.assertTrue((path/'gpu-payload.json').exists());self.assertFalse((path/'cpu-payload.json').exists())
                    self.assertEqual(json.loads((path/'result.json').read_text())['verification'],'deferred')

    def test_verify_match_and_mismatch_use_fresh_cpu_and_update_capture(self):
        for corrupt in (False,True):
            with self.subTest(corrupt=corrupt),tempfile.TemporaryDirectory() as folder,self.harness(folder,corrupt=corrupt) as (_,events):
                bodies=self.bodies();rows=product.evaluate_many(bodies,verification='deferred')
                inputs=[dict(body=b,capture_id=r['result']['compute']['capture_id']) for b,r in zip(bodies,rows)]
                checked=product.verify_portable_detail(inputs)
                self.assertEqual([r['matched'] for r in checked],[True,not corrupt,True])
                self.assertEqual([e for e in events if isinstance(e,tuple)],[('cpu',0),('cpu',1),('cpu',2)])
                if corrupt:
                    self.assertEqual(checked[1]['differing_fields'],['marker'])
                    self.assertTrue(checked[1]['cpu_result']['compute']['gpu_result_rejected'])
                    self.assertEqual(checked[1]['cpu_result']['compute']['backend'],'cpu')
                for row in inputs:
                    path=Path(folder)/row['capture_id'];record=json.loads((path/'result.json').read_text())
                    self.assertEqual(record['verification'],'deferred-checked');self.assertTrue((path/'cpu-payload.json').exists())
                product.verify_portable_detail(inputs)
                self.assertEqual(sum(isinstance(e,tuple) for e in events),6)

    def test_http_body_cannot_defer_or_reach_cpu_as_internal_options(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder) as (_,events):
            body={**self.bodies(1)[0],'verification':'deferred','_verification':'deferred'}
            with patch.object(product.engine_worker,'evaluate',return_value={'marker':0}) as cpu:
                result=product.evaluate(body)
            self.assertTrue(result['compute']['cpu_verification']['matched'])
            self.assertNotIn('verification',cpu.call_args.args[0]);self.assertNotIn('_verification',cpu.call_args.args[0])

    def test_deferred_transport_errors_still_run_authoritative_cpu(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder,fail=True) as (_,events):
            body=self.bodies(1)[0]
            marker=product.evaluate_many([body],verification='deferred')[0]['result']['cpu_fallback_pending']
            result=product.cpu_fallback_portable_detail([dict(body=body,capture_id=marker['capture_id'])])[0]
            self.assertEqual(result['compute']['backend'],'cpu');self.assertIn(('cpu',0),events)
            self.assertNotIn('cpu_verification',result['compute'])

    def test_verify_rejects_mismatched_body_and_capture_traversal_before_cpu(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder):
            body=self.bodies(1)[0];result=product.evaluate_many([body],verification='deferred')[0]['result']
            for changed,capture in [({**body,'seed':123},result['compute']['capture_id']),(body,'../bad')]:
                with patch.object(product.engine_worker,'evaluate',side_effect=AssertionError('must not run')),self.assertRaises(ValueError):
                    product.verify_portable_detail([dict(body=changed,capture_id=capture)])

    def test_browser_finish_propagates_service_policy_only(self):
        with patch.object(product,'_browser_rows',return_value=[]) as rows:
            product.finish_browser([{}],[{}],verification='deferred')
            self.assertEqual(rows.call_args.kwargs,{'verification':'deferred'})
            product.prepare_browser_wires([{}]);self.assertEqual(rows.call_args.kwargs,{'verification':'full'})

    def test_service_actions_accept_internal_option(self):
        for action,function in [('evaluate_portable_detail_batch','evaluate_many'),('prepare_browser_wires','prepare_browser_wires'),('finish_browser','finish_browser')]:
            request=dict(action=action,evaluations=self.bodies(1),verification='deferred',uploads=[{}])
            with patch.object(sys,'stdin',io.StringIO(json.dumps(request))),patch.object(sys,'stdout',io.StringIO()),patch.object(service,function,return_value=[]) as fn:
                service.main();self.assertEqual(fn.call_args.kwargs,{'verification':'deferred'})
        with patch.object(sys,'stdin',io.StringIO(json.dumps(dict(action='verify_portable_detail',evaluations=[{}])))),patch.object(sys,'stdout',io.StringIO()),patch.object(service,'verify_portable_detail',return_value=[]) as fn:
            service.main();fn.assert_called_once_with([{}])

    def test_browser_deferred_finish_and_fresh_verification_match_and_mismatch(self):
        import test_portable_wasm as browser_fixtures
        for corrupt in (False,True):
            fixture=browser_fixtures.BrowserPhases('test_finish_uses_fresh_cpu_and_honest_evidence')
            fixture.setUp()
            try:
                if corrupt:fixture.decoder.return_value=dict(total_damage=99)
                product.prepare_browser_wires([fixture.body],verification='deferred')
                result=product.finish_browser([fixture.body],[fixture.upload()],verification='deferred')[0]['result']
                fixture.cpu.assert_not_called()
                self.assertEqual(result['compute']['cpu_verification'],dict(status='pending'))
                self.assertFalse(result['compute']['gpu_execution_verified'])
                self.assertTrue(result['compute']['browser_execution_reported'])
                checks=product.verify_portable_detail([dict(body=fixture.body,capture_id=result['compute']['capture_id'])])
                self.assertEqual(checks[0]['matched'],not corrupt);fixture.cpu.assert_called_once()
                if corrupt:self.assertTrue(checks[0]['cpu_result']['compute']['gpu_result_rejected'])
            finally:fixture.doCleanups()

    def test_verification_cpu_error_propagates_without_accepting_pending_result(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder):
            body=self.bodies(1)[0];result=product.evaluate_many([body],verification='deferred')[0]['result']
            with patch.object(product.engine_worker,'evaluate',side_effect=RuntimeError('CPU failed')) as cpu:
                with self.assertRaisesRegex(RuntimeError,'CPU failed'):
                    product.verify_portable_detail([dict(body=body,capture_id=result['compute']['capture_id'])])
                cpu.assert_called_once()
            record=json.loads((Path(folder)/result['compute']['capture_id']/'result.json').read_text())
            self.assertEqual(record['cpu_verification'],dict(status='pending'))
            self.assertEqual(record['verification'],'deferred')

    def test_same_comparator_keeps_existing_top_level_semantics(self):
        self.assertEqual(product.payload_differences({'a':[1],'compute':1},{'a':[1],'compute':2}),[])
        self.assertEqual(set(product.payload_differences({'a':[1],'b':2},{'a':[2],'c':3})),{'a','b','c'})

class VerificationSourceHistory(unittest.TestCase):
    def test_reviewed_inverse_and_additional_mutations(self):
        import portable_optimizer_verification_source_contract as history
        root=Path(__file__).resolve().parents[1];name='app/portable_detail.py';raw=(root/name).read_bytes()
        before=history.verification_preimage(root,name,raw)
        from portable_browser_backend_source_contract import AFTER_SHA256
        self.assertEqual(hashlib.sha256(before).hexdigest(),AFTER_SHA256[name])
        for changed in (raw+b'\n',raw[:-1],b'!'+raw[1:]):
            with self.assertRaisesRegex(ValueError,'Unreviewed'):history.verification_preimage(root,name,changed)
            self.assertEqual(history.reviewed_bytes(root,name,changed),changed)
        from portable_optimizer_throughput_source_contract import throughput_preimage
        raw=throughput_preimage(root,name,raw)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'tests/fixtures';target.mkdir(parents=True)
            ledger='portable-optimizer-verification-source-delta.json'
            (target/ledger).write_bytes((root/'tests/fixtures'/ledger).read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'ledger changed'):history.verification_preimage(tmp,name,raw)

    def test_inverse_binds_spans_and_historical_digest(self):
        import portable_optimizer_verification_source_contract as history
        root=Path(__file__).resolve().parents[1];name='app/portable_detail.py';raw=(root/name).read_bytes()
        from portable_optimizer_throughput_source_contract import throughput_preimage
        raw=throughput_preimage(root,name,raw)
        data=json.loads((root/'tests/fixtures/portable-optimizer-verification-source-delta.json').read_text())
        for field,error in [('after','inverse span changed'),('before','historical preimage changed')]:
            with tempfile.TemporaryDirectory() as tmp:
                changed=copy.deepcopy(data);changed['files'][name]['hunks'][0][field]='wrong bytes'
                ledger=(json.dumps(changed,indent=2)+'\n').encode();target=Path(tmp)/'tests/fixtures';target.mkdir(parents=True)
                (target/'portable-optimizer-verification-source-delta.json').write_bytes(ledger)
                with patch.object(history,'LEDGER_SHA256',hashlib.sha256(ledger).hexdigest()),self.assertRaisesRegex(ValueError,error):
                    history.verification_preimage(tmp,name,raw)
