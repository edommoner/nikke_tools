"""Full state footprint, private wire and exact source projection guards."""
import importlib.util,sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_specs import LIMITS as L,check_schema
from portable_scratch_layout import verify
from portable_not_core_specs import address
from portable_not_core_source_contract import project_sources

class NotCoreGPUTests(unittest.TestCase):
    def test_full256_by5_binary64_and_seen_ownership(self):
        check_schema();owned=set()
        for row in range(256):
            for who in range(5):
                at,seen,bit=address(row,who);self.assertNotIn(at,owned);owned.update((at,at+1));self.assertTrue(524248<=seen<524288);self.assertTrue(bit and bit&(bit-1)==0)
        self.assertEqual(len(owned),2560)
        for mode in ('normal','native-query-diagnostic','heal-share-diagnostic','interrupt-aim-diagnostic'):self.assertTrue(verify(L,mode=mode)['verified'])
        self.assertEqual(L['WORLD_RELOAD_OUTPUT_WORDS'],786432)
    def test_private32_inputs_and_existing_entry_rejection_payload(self):
        s=importlib.util.spec_from_file_location('notcore_gpu_cases',ROOT/'research/verify-world-not-core-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,data=m.prepare()
        self.assertEqual(len(rows),32);self.assertEqual(sum(d is not None for _,_,d in rows),27);self.assertEqual(len(data),4+32*104400*4)
        for name,w,d in rows[:27]:self.assertTrue(any(w[L['CONDITION_BASE']+i*L['CONDITION_WORDS']+slot*4]==27 for i in range(w[1]) for slot in range(3)))
    def test_literal_geometry_preparation_cannot_tick_or_query_buffs(self):
        from calculator import timeline
        from calculator.buff_manager import BuffManager
        import portable_backend
        s=importlib.util.spec_from_file_location('notcore_static',ROOT/'research/verify-world-not-core-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        with patch.object(timeline.CharState,'tick',side_effect=AssertionError('No CPU clock')),patch.object(BuffManager,'get_buffs',side_effect=AssertionError('No numerical query')),patch.object(portable_backend,'execute',side_effect=AssertionError('No GPU')):rows,data=m.prepare()
        self.assertEqual(len(rows),32)
    def test_reviewed_source_and_added_numeric_helper_reject_changes(self):
        project_sources(ROOT);name='gpu/not_core_runtime.slang';text=(ROOT/name).read_text()
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace('f64Add(actorNumber(at),','f64Mul(actorNumber(at),',1)})

if __name__=='__main__':unittest.main()
