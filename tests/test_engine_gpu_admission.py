import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_gpu_admission as admission
from engine_gpu_admission import require_supported,UnsupportedEngineKeys


class EngineGPUAdmissionTests(unittest.TestCase):
    def test_every_ported_key_is_admitted_shared_and_named_in_legacy_refusal(self):
        rows=[{'target':v} for v in ('self_and_engaged_allies','allies_down_all')]
        rows += [{'stat':v} for v in ('engaged_state','normal_atk_width_pct')]
        rows += [{'trigger':{'condition':[v]}} for v in ('during_full_charge','ally_down_count_above:1','ally_down_count_below:2')]
        for row in rows:
            require_supported([row])
            with self.subTest(row=row),self.assertRaises(UnsupportedEngineKeys) as error:require_supported([row],legacy=True)
            self.assertIn(row['trigger']['condition'][0] if 'trigger' in row else next(iter(row.values())),str(error.exception))
        require_supported([],['렐릭 베젤 큐브'])
        with self.assertRaisesRegex(UnsupportedEngineKeys,'hp_only_caster_based_pct'):require_supported([],['렐릭 베젤 큐브'],legacy=True)
        self.assertEqual(admission.SHARED_TARGETS|admission.SHARED_STATS|admission.SHARED_CONDITIONS,frozenset())

    def test_shared_refusal_mechanism_still_scans_nested_rows(self):
        with patch.object(admission,'SHARED_TARGETS',frozenset(('future-selector',))):
            with self.assertRaisesRegex(UnsupportedEngineKeys,'target:future-selector'):require_supported([{'children':[{'target':'future-selector'}]}])
        with patch.object(admission,'SHARED_CONDITIONS',frozenset(('future-predicate',))):
            with self.assertRaisesRegex(UnsupportedEngineKeys,'condition:future-predicate'):require_supported([{'trigger':{'condition':'future-predicate'}}])

    def test_legacy_compilation_still_refuses_new_cube_without_battle(self):
        import engine_worker
        demo=engine_worker.detail_demo();body=dict(profile=demo['profile'],squad=demo['squad'],duration=3)
        body['profile']['chars'][body['squad'][0]]['cube']={'name':'렐릭 베젤 큐브','level':15}
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU battle forbidden')):
            for flags in ({'_compile_gpu_detail':True},{'compute_backend':'cuda_detail'},{'_compile_gpu_detail':True,'_compile_gpu':True}):
                with self.subTest(flags=flags),self.assertRaisesRegex(UnsupportedEngineKeys,'cube:렐릭 베젤 큐브'):engine_worker.evaluate(dict(copy.deepcopy(body),**flags))
            coarse=engine_worker.evaluate(dict(copy.deepcopy(body),_compile_gpu=True))
            self.assertEqual(coarse['names'],body['squad'])
            self.assertTrue(any('큐브:렐릭 베젤 큐브'==issue['effect'] for issue in coarse['issues']))

    def test_real_product_characters_and_cube_compile_without_battle_or_device(self):
        import engine_worker,portable_detail,portable_backend
        from portable_specs import LIMITS as L,FIELDS as F
        bodies=json.loads((ROOT/'tests/fixtures/gpu-new-characters-product-v1.json').read_text())
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU battle forbidden')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            for index,body in enumerate(bodies):
                body=dict(body,duration=3)
                with self.assertRaisesRegex(UnsupportedEngineKeys,'cube:렐릭 베젤 큐브' if index==1 else 'engaged_state'):
                    engine_worker.evaluate(dict(copy.deepcopy(body),_compile_gpu_detail=True))
                prepared,_=portable_detail.prepare(body);source,iw,ow,words,metadata=portable_detail.compile_product(prepared)
                self.assertEqual(source,'gpu/product_fixed_battle_entry.slang');self.assertEqual(len(words),iw)
                if index==1:
                    cube=next(i for i,row in enumerate(prepared['effects']) if row['effect'].get('name')=='큐브:렐릭 베젤 큐브')
                    at=L['DEFINITION_BASE']+cube*L['DEFINITION_WORDS']
                    self.assertEqual(words[at+F['MAX_STACK']],3);self.assertEqual(words[at+F['STAT']],40)
                    self.assertEqual(words[L['EVENT_BASE']+cube*L['EVENT_WORDS']],1)

if __name__=='__main__':unittest.main()
