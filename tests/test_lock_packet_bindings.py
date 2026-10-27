"""Actual emission budgets, queue ownership, and exact source deltas."""
import importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
spec=importlib.util.spec_from_file_location('packet_bind_test',ROOT/'research/verify-lock-packets.py');suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)

class PacketBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries,_=suite.prepare();cls.observed=[suite.native_reference(d) for _,_,d in cls.entries if d]

    def test_all_2048_live_links_are_separate_from_periodic_and_manual_state(self):
        from portable_lock_packet_layout import check,TOKENS,SHOT_TIMES,TRACE_CAPACITY
        from portable_physical_lock_layout import END
        from portable_physical_lock_cover_layout import WORDS
        self.assertEqual(TOKENS,END+WORDS);self.assertEqual(SHOT_TIMES-TOKENS,2048);self.assertEqual(TRACE_CAPACITY,38)
        self.assertEqual(check(ROOT)['actor_set_capacity'],32)
        text=(ROOT/'gpu/world_skill_runtime.slang').read_text()
        self.assertIn('results[at+7]=0;WORLD_PERIODIC_STORE(s,at,r)',text)
        self.assertIn('results[at+7]=index+1;', (ROOT/'gpu/world_periodic_runtime.slang').read_text())

    def test_dynamic_native_hits_are_actual_emitted_budget_not_default_one(self):
        n=self.observed[0];events=n['lock_packet_trace']
        self.assertEqual([(e['hit'],e['hits'],e['token']) for e in events if e['phase']==0],[(1,2,1),(2,2,1),(1,2,2),(2,2,2)])
        case=self.entries[0][2][0];source=next(i for i,e in enumerate(case['effects']) if e.get('name')==case['packet_skill'])
        self.assertEqual([(r['hit'],r['hits']) for r in n['skill_trace'] if r['row']==source],[(1,2),(2,2),(1,2),(2,2)])

    def test_actual_empty_dead_reborn_and_cover_snapshots_keep_packet_identity(self):
        self.assertTrue(any(e['status']==1 for e in self.observed[1]['lock_packet_trace']))
        events=self.observed[2]['lock_packet_trace'];dead=[e for e in events if e['phase']==1 and e['status']==4]
        self.assertEqual([e['generation'] for e in dead],[1,2]);self.assertEqual([e['packet'] for e in dead],[2,2])
        cover=self.observed[3]['lock_packet_trace'];self.assertEqual(cover[0]['hits'],4);self.assertEqual(cover[0]['count'],3)
        self.assertEqual([e['ordinal'] for e in cover[:4]],[0,1,2,0])

    def test_packing_uses_static_definitions_not_cpu_packet_schedule(self):
        from calculator import timeline
        import portable_backend
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule')),patch.object(portable_backend,'execute',side_effect=AssertionError('No GPU in packing')):
            rows,_=suite.prepare();self.assertEqual(len(rows),8);self.assertEqual(sum(d is not None for _,_,d in rows),4)

    def test_source_inverse_rejects_unreviewed_queue_or_periodic_changes(self):
        from portable_lock_packet_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-lock-packet-source-delta.json').read_text());old=project_sources(ROOT)
        for name,row in data['sources'].items():
            self.assertEqual(old[name],row['baseline'])
            with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n// mutation'})

if __name__=='__main__':unittest.main()
