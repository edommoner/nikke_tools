"""Observed trace must preserve source, binary64 payload and delivery order."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_heal_share_trace import BASE,COUNT,WORDS,MAGIC,native_records,gpu_records
class HealShareTraceTests(unittest.TestCase):
    def test_actual_native_records_survive_wire_read_and_detect_changed_order(self):
        import engine_worker
        from portable_heal_share_cases import fixtures
        from world_heal_share_native import observe
        events=observe(fixtures()[-1])[0]['heal_share_events'];expected=native_records(events)
        block=[0]*(BASE+8+COUNT*WORDS);block[BASE:BASE+2]=[MAGIC,len(expected)]
        for i,row in enumerate(expected):block[BASE+8+i*WORDS:BASE+8+(i+1)*WORDS]=row
        self.assertEqual(gpu_records(block,observe_heal_sources=False),expected)
        changed=list(block);a=BASE+8;b=a+WORDS;changed[a:b],changed[b:b+WORDS]=changed[b:b+WORDS],changed[a:b]
        self.assertNotEqual(gpu_records(changed,observe_heal_sources=False),expected)
        changed=list(block);changed[BASE+2]=1
        with self.assertRaises(AssertionError):gpu_records(changed,observe_heal_sources=False)
        changed=list(block);changed[-1]=1
        with self.assertRaises(AssertionError):gpu_records(changed,observe_heal_sources=False)
    def test_source_projection_never_hides_an_observed_source(self):
        event=dict(kind='notify',event='event:heal_received',owner=0,heal_source=1,time=0)
        row=native_records([event])[0];block=[0]*(BASE+8+COUNT*WORDS);block[BASE:BASE+2]=[MAGIC,1];block[BASE+8:BASE+8+WORDS]=row
        self.assertEqual(gpu_records(block,observe_heal_sources=True)[0][2],1)
        self.assertEqual(gpu_records(block,observe_heal_sources=False)[0][2],0xffffffff)
    def test_trace_bank_is_after_revival_and_before_existing_admission_diagnostics(self):
        from portable_specs import LIMITS as L
        self.assertLessEqual(L['REVIVAL_BASE']+L['REVIVAL_WORDS'],BASE)
        self.assertLessEqual(BASE+8+COUNT*WORDS,786416)
