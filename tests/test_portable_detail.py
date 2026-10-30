"""Product payload parity and fail-closed paths, without a GPU or CPU replay."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_detail as product
from portable_projectile_roster_input import compile_projectile_battle

class PortableDetail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/'tests/fixtures/portable-detail-product-v1.json').read_text(encoding='utf-8'))
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('Preparation must not run a battle')):
            cls.prepared,cls.prepared_run=product.prepare(cls.fixture['body'])
            cls.words,cls.metadata=compile_projectile_battle(cls.prepared)
    def test_saved_actual_gpu_projection_reconstructs_complete_original_product_payload(self):
        with patch.object(product,'decode',return_value=self.fixture['gpu_projection']):
            payload=product.decode_payload(self.fixture['body'],self.prepared,self.prepared_run,self.metadata,[])
        self.assertEqual(payload,self.fixture['cpu_payload'])
        self.assertEqual(self.prepared['cpu_battle_executed'],False)
        self.assertEqual(len(self.prepared['effects']),len(self.metadata['effects']))
    def test_invalid_status_truncation_nonfinite_and_bad_owner_cannot_be_published(self):
        for mutate in (lambda v:v.update(status=64),lambda v:v.update(burst_trace_total=999),
            lambda v:v['queries'][0]['damage'].__setitem__(0,float('nan')),
            lambda v:v['burst_trace'][0].update(owner=9)):
            view=copy.deepcopy(self.fixture['gpu_projection']);mutate(view)
            with patch.object(product,'decode',return_value=view):
                with self.assertRaises((ValueError,RuntimeError)):
                    product.decode_payload(self.fixture['body'],self.prepared,self.prepared_run,self.metadata,[])
    def test_backend_failure_preserves_cpu_label_and_strips_internal_request_flags(self):
        body={**self.fixture['body'],'_compile_gpu_detail':True}
        calls=[]
        def cpu(request):
            calls.append(request);return copy.deepcopy(self.fixture['cpu_payload'])
        with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',NIKKE_DETAIL_CAPTURE_ROOT=folder),\
             patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
             patch.object(product,'execute',side_effect=RuntimeError('device unavailable')),\
             patch.object(product.engine_worker,'evaluate',side_effect=cpu):
            result=product.evaluate(body)
            self.assertEqual(result['compute']['backend'],'cpu')
            self.assertEqual(result['compute']['requested'],'metal_detail')
            self.assertFalse(result['compute']['gpu_execution_verified'])
            self.assertNotIn('_compile_gpu_detail',calls[0])
            self.assertEqual(len(list(Path(folder).glob('*/result.json'))),1)
    def test_product_history_gap_falls_back_before_any_gpu_dispatch(self):
        body=copy.deepcopy(self.fixture['body']);body['enemy']['patterns']=[dict(id='example',kind='idle')]
        with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',NIKKE_DETAIL_CAPTURE_ROOT=folder),\
             patch.object(product,'prepare',return_value=(self.prepared,self.prepared_run)),\
             patch.object(product,'execute',side_effect=AssertionError('No dispatch')),\
             patch.object(product.engine_worker,'evaluate',return_value=copy.deepcopy(self.fixture['cpu_payload'])):
            result=product.evaluate(body)
            self.assertEqual(result['compute']['backend'],'cpu')
            self.assertIn('未接続',result['compute']['unsupported'][0]['reason'])

if __name__=='__main__':unittest.main()
