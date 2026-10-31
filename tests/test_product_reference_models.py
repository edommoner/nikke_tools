"""Product requests must execute declared consumers and fail before omitted GPU work."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from runner import sim
from product_reference_models import normalize,execution,WARNING

class ProductReferenceModels(unittest.TestCase):
    def test_original_anne_reduction_reaches_actual_product_healing_and_restores_aliases(self):
        from portable_enemy_healing_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'enemy_healing':copy.deepcopy(case['enemy_healing'])};before=copy.deepcopy(body)
        aliases=(timeline.simulate,sim.simulate)
        result=engine_worker.evaluate(body)
        self.assertEqual(body,before);self.assertEqual(aliases,(timeline.simulate,sim.simulate))
        model=result['reference_models'];self.assertEqual(model['declarations'],body['reference_models'])
        self.assertEqual(model['evidence'],'declared-model-not-game-verification')
        receipts=model['enemy_healing']['receipts'];self.assertEqual(len(receipts),8)
        self.assertTrue(any(r.get('multiplier',1)<1 for r in receipts))
        self.assertTrue(any(r.get('effective_gain',0)>0 for r in receipts))
        self.assertIn(WARNING,result['app_warnings'])

    def test_preparation_retains_only_literals_and_omitted_gpu_consumer_stops_before_dispatch(self):
        from portable_product_programs import body_for_program
        import portable_detail as product
        body=body_for_program(ROOT,'accumulate')
        body['reference_models']={'enemy_healing':[dict(node='heal',targets=['__enemy__:wave#1'],amount=10)]}
        with patch.object(sim,'execute',side_effect=AssertionError('Static preparation must not simulate')):
            prepared,_=product.prepare(body)
        self.assertEqual(prepared['reference_models'],body['reference_models'])
        with patch.object(product,'execute',side_effect=AssertionError('No unconnected model may reach GPU')) as gpu:
            with self.assertRaisesRegex(product.UnsupportedPortable,'matching shared GPU product wire'):product.compile_product(prepared)
        gpu.assert_not_called()
        for flag in ('_compile_gpu','_compile_gpu_detail'):
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,'no legacy GPU producer'):
                engine_worker.evaluate(dict(body,**{flag:True}))

    def test_invalid_or_unknown_models_fail_before_simulation(self):
        from portable_product_programs import body_for_program
        body=body_for_program(ROOT,'accumulate')
        for value in ([],True,{'lock_on':{}},{'enemy_healing':[]},{'enemy_healing':[dict(node='x',targets=['y'],amount=True)]}):
            with self.subTest(value=value),patch.object(sim,'execute',side_effect=AssertionError('Invalid declarations may not simulate')),self.assertRaises(ValueError):
                engine_worker.evaluate(dict(body,reference_models=value))

    def test_adapter_unwinds_after_execution_error_and_default_installs_nothing(self):
        aliases=(timeline.simulate,sim.simulate)
        with execution({}) as data:self.assertIsNone(data);self.assertEqual(aliases,(timeline.simulate,sim.simulate))
        declarations=normalize({'enemy_healing':[dict(node='x',targets=['y'],amount=1)]})
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with execution(declarations):
                self.assertIsNot(timeline.simulate,aliases[0]);raise RuntimeError('injected')
        self.assertEqual(aliases,(timeline.simulate,sim.simulate))

if __name__=='__main__':unittest.main()
