"""Deferred native CPU fallback protocol and exact inline result parity."""
import copy,hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_portable_detail as fixtures
import portable_detail as product

class CpuFallback(unittest.TestCase):
    harness=fixtures.ProductBatchProtocol.harness
    bodies=fixtures.ProductBatchProtocol.bodies

    def test_each_failure_has_identical_inline_and_fresh_result(self):
        causes=[('prepare','projectile early-return'),('compile_product','named modifier carrier'),
                ('execute','transport failed'),('verified_transport','status 64'),
                ('decode_payload','history capacity status 8'),('decode_payload','decode failed')]
        for function,reason in causes:
            results=[]
            for verification in ('full','deferred'):
                with self.subTest(function=function,reason=reason,verification=verification),tempfile.TemporaryDirectory() as folder,self.harness(folder,backend='native') as (_,events),patch.object(product,function,side_effect=RuntimeError(reason)):
                    body=self.bodies(1,'native_detail')[0]
                    result=product.evaluate_many([body],verification=verification)[0]['result']
                    if verification=='deferred':
                        self.assertEqual(list(result),['cpu_fallback_pending'])
                        self.assertFalse(any(isinstance(e,tuple) for e in events))
                        marker=result['cpu_fallback_pending'];capture=Path(folder)/marker['capture_id']
                        self.assertFalse((capture/'cpu-payload.json').exists())
                        self.assertEqual(json.loads((capture/'result.json').read_text())['cpu_fallback_pending'],marker)
                        result=product.cpu_fallback_portable_detail([dict(body=body,capture_id=marker['capture_id'])])[0]
                        self.assertTrue((capture/'cpu-payload.json').exists())
                    self.assertEqual([e for e in events if isinstance(e,tuple)],[('cpu',0)])
                    self.assertEqual(result['compute'].pop('capture_id').__len__(),32)
                    results.append(result)
            self.assertEqual(*results)

    def test_pending_only_for_deferred_native(self):
        for requested,backend in [('native_detail','native'),('native_detail','metal'),('native_detail','cuda')]:
            for verification in ('full','deferred'):
                with self.subTest(requested=requested,verification=verification),tempfile.TemporaryDirectory() as folder,self.harness(folder,backend=backend,fail=True) as (_,events):
                    result=product.evaluate_many(self.bodies(1,requested),verification=verification)[0]['result']
                    pending=requested=='native_detail' and verification=='deferred'
                    self.assertEqual('cpu_fallback_pending' in result,pending)
                    self.assertEqual(('cpu',0) in events,not pending)

    def test_binding_validation_and_cpu_error(self):
        with tempfile.TemporaryDirectory() as folder,self.harness(folder,backend='native',fail=True):
            body=self.bodies(1,'native_detail')[0]
            marker=product.evaluate_many([body],verification='deferred')[0]['result']['cpu_fallback_pending']
            for changed,capture in [({**body,'seed':999},marker['capture_id']),(body,'../bad')]:
                with patch.object(product.engine_worker,'evaluate',side_effect=AssertionError('must not run')),self.assertRaises(ValueError):
                    product.cpu_fallback_portable_detail([dict(body=changed,capture_id=capture)])
            with patch.object(product.engine_worker,'evaluate',side_effect=RuntimeError('CPU failed')) as cpu,self.assertRaisesRegex(RuntimeError,'CPU failed'):
                product.cpu_fallback_portable_detail([dict(body=body,capture_id=marker['capture_id'])])
            cpu.assert_called_once()
            record=json.loads((Path(folder)/marker['capture_id']/'result.json').read_text())
            self.assertEqual(record['cpu_error']['stage'],'cpu')
            self.assertFalse((Path(folder)/marker['capture_id']/'cpu-payload.json').exists())


    def test_service_dispatches_stateless_action(self):
        import portable_detail_service as service
        request=dict(action='cpu_fallback_portable_detail',evaluations=[dict(body={},capture_id='a'*32)])
        with patch.object(sys,'stdin',io.StringIO(json.dumps(request))),patch.object(sys,'stdout',io.StringIO()),patch.object(service,'cpu_fallback_portable_detail',return_value=[]) as fn:
            service.main()
        fn.assert_called_once_with(request['evaluations'])
