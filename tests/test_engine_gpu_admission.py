import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_gpu_admission as admission
from engine_gpu_admission import require_supported,UnsupportedEngineKeys


class EngineGPUAdmissionTests(unittest.TestCase):
    def test_ported_keys_and_cube_are_admitted_by_shared_compiler(self):
        for row in ({'target':'self_and_engaged_allies'},{'target':'allies_down_all'},{'stat':'engaged_state'},{'stat':'normal_atk_width_pct'},{'trigger':{'condition':['during_full_charge']}}):
            require_supported([row])
        require_supported([],['렐릭 베젤 큐브'])


    def test_shared_refusal_mechanism_still_scans_nested_rows(self):
        with patch.object(admission,'SHARED_TARGETS',frozenset(('future-selector',))):
            with self.assertRaisesRegex(UnsupportedEngineKeys,'target:future-selector'):require_supported([{'children':[{'target':'future-selector'}]}])
        with patch.object(admission,'SHARED_CONDITIONS',frozenset(('future-predicate',))):
            with self.assertRaisesRegex(UnsupportedEngineKeys,'condition:future-predicate'):require_supported([{'trigger':{'condition':'future-predicate'}}])


    def test_real_product_characters_and_cube_compile_without_battle_or_device(self):
        import engine_worker,portable_detail,portable_backend
        from portable_specs import LIMITS as L,FIELDS as F
        bodies=json.loads((ROOT/'tests/fixtures/gpu-new-characters-product-v1.json').read_text())
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU battle forbidden')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            for index,body in enumerate(bodies):
                body=dict(body,duration=3)
                prepared,_=portable_detail.prepare(body);source,iw,ow,words,metadata=portable_detail.compile_product(prepared)
                self.assertEqual(source,'gpu/product_fixed_battle_entry.slang');self.assertEqual(len(words),iw)
                if index==1:
                    cube=next(i for i,row in enumerate(prepared['effects']) if row['effect'].get('name')=='큐브:렐릭 베젤 큐브')
                    at=L['DEFINITION_BASE']+cube*L['DEFINITION_WORDS']
                    self.assertEqual(words[at+F['MAX_STACK']],3);self.assertEqual(words[at+F['STAT']],40)
                    self.assertEqual(words[L['EVENT_BASE']+cube*L['EVENT_WORDS']],1)

if __name__=='__main__':unittest.main()
