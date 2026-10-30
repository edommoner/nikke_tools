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
        expected=copy.deepcopy(self.fixture['cpu_payload'])
        # Run provenance is stamped at response time; the saved capture keeps
        # its historical commit. No calculation/payload fields are excluded.
        expected['evaluator']=product.engine_worker.sim.evaluator()
        self.assertEqual(payload,expected)
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
    def test_original_model_warnings_are_collected_without_a_cpu_battle(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        from staged_dot_runtime import MODEL_WARNING
        from periodic_source_runtime import LEGACY_WARNING
        from target_counter_runtime import SINGLE_BODY_WARNING
        for name,warning in [('사쿠라 : 블룸 인 서머',MODEL_WARNING),
                             ('아인',LEGACY_WARNING),('일레그 : 붐 앤 쇼크',SINGLE_BODY_WARNING)]:
            body=selected_profile_bodies([name],0)[0][2]
            with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
                prepared,run=product.prepare(body)
            self.assertEqual(run._portable_detail_model_warnings,[warning])
            with patch.object(product,'decode',return_value=self.fixture['gpu_projection']):
                payload=product.decode_payload(body,prepared,run,self.metadata,[])
            self.assertEqual(payload['app_warnings'],[self.fixture['cpu_payload']['app_warnings'][0],warning])
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
    def test_real_multi_hit_uses_existing_native_group_wire_without_changing_effects(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L
        body=selected_profile_bodies(['벨로타'],0)[0][2]
        with patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle')):
            prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
            source,iw,ow,words,metadata=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        self.assertEqual(source,'gpu/product_group_battle_entry.slang')
        self.assertEqual((iw,ow,len(words)),(104408,1048576,104408))
        self.assertEqual(len(metadata['effects']),len(prepared['effects']))
        self.assertEqual(words[-8:-5],[0x41475331,2,1])
        event_rows=[i for i in range(words[1]) if words[L['EVENT_BASE']+i*L['EVENT_WORDS']]==62]
        self.assertTrue(event_rows)
        bad=copy.deepcopy(prepared)
        next(item['effect'] for item in bad['effects'] if any(t.startswith('multi_hit:') for t in item['effect']['trigger']['timing']))['trigger']['timing']=['multi_hit:0']
        with self.assertRaises(ValueError):product.compile_product(bad)
    def test_ordinary_periodic_stack_scaling_preserves_hit_count_not_dot_coefficient(self):
        sys.path.insert(0,str(ROOT/'research'))
        from portable_original_identity_inventory import selected_profile_bodies
        from portable_specs import LIMITS as L,FIELDS as F
        from portable_periodic_specs import periodic_flags
        body=selected_profile_bodies(['마스트'],0)[0][2]
        prepared,_=product.prepare(body);before=copy.deepcopy(prepared)
        _,_,_,words,metadata=product.compile_product(prepared)
        self.assertEqual(prepared,before)
        row=metadata['effects'].index('폭풍')
        self.assertEqual(words[L['REFERENCE_DEFINITION_BASE']+row*4]&3,1)
        self.assertEqual(words[L['PERIODIC_DEFINITION_BASE']+row*2]&2,0)
        self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['PRESERVE']],0)
        dot=dict(type='damage',stat='dot_damage',tick_interval=1,scaling='stack_count',target='target')
        self.assertEqual(periodic_flags(dot,0)&2,2)

if __name__=='__main__':unittest.main()
