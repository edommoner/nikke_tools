"""Real queue recipients change HP/counter/healing, never the damage arithmetic."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
spec=importlib.util.spec_from_file_location('live_delivery_test',ROOT/'research/verify-live-lock-delivery.py');suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
from live_lock_delivery_policy import MODEL,select_live,UnresolvedLockDelivery

class LiveDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries,_=suite.prepare();cls.observed=[suite.native_reference(d) for _,_,d in cls.entries if d]

    def packets(self,index):
        c=self.entries[index][2][0];source=next(i for i,e in enumerate(c['effects']) if e.get('name')==c['packet_skill'])
        return [r for r in self.observed[index]['skill_trace'] if r['row']==source]

    def test_real_queue_uses_frozen_slots_after_membership_clear(self):
        self.assertEqual([r['recipients'] for r in self.packets(0)],[[0],[1],[0],[1]])
        self.assertEqual([r['recipients'] for r in self.packets(2)][:4],[[0],[1],[2],[0]])
        for n in self.observed:
            for e in n['lock_packet_trace']:
                if e['phase']==1:self.assertIn(e['time'],n['lock_clears'])

    def test_empty_snapshot_never_falls_back_to_body(self):
        self.assertEqual(self.packets(1)[0]['recipients'],[])
        self.assertEqual(self.observed[1]['lock_packet_trace'][0]['status'],1)

    def test_add_damage_counter_and_healing_use_existing_native_path(self):
        n=self.observed[3];done=n['battle']['target_counters']['completions']
        self.assertEqual(len(done),1);impact=done[0]['impact']
        self.assertEqual(int(impact['target']['kind']),5);self.assertEqual(int(impact['family']),1)
        self.assertEqual(impact['damage'],self.packets(3)[1]['amount'])
        self.assertGreater(n['battle']['allies'][0]['hp'],200000000)
        plain=suite.parent.native_reference(self.entries[3][2])
        self.assertNotEqual(n['battle'],plain['battle']) # Missing selector lowering is intentional, not canonical equivalence.
        self.assertEqual(plain['battle']['target_counters']['completions'],[])

    def test_actual_death_is_refused_not_dropped_or_retargeted(self):
        case=suite.parent.fixtures()[2];before=copy.deepcopy(case)
        with self.assertRaisesRegex(UnresolvedLockDelivery,'Unresolved'):suite.observe(case,delivery_model=MODEL)
        self.assertEqual(case,before)

    def test_missing_stale_dead_and_unknown_model_are_refused(self):
        from test_lock_delivery_policy import DeliveryTests
        from impact_specs import ActorHandle
        from world_actor_runtime import ActorSnapshot
        _,snapshot,views=DeliveryTests().frozen()
        for now in (views[1:],[ActorSnapshot(ActorHandle(5,0),'dead',False),*views[1:]],[ActorSnapshot(ActorHandle(5,0,2),'new',True),*views[1:]]):
            with self.assertRaises(UnresolvedLockDelivery):select_live(snapshot,1,3,now,model=MODEL)
        with self.assertRaisesRegex(ValueError,'Explicit'):select_live(snapshot,1,3,views,model='default')

    def test_static_packing_does_not_compute_cpu_delivery_schedule(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No oracle in packing')):
            entries,_=suite.prepare();self.assertEqual(len(entries),9);self.assertEqual(sum(d is not None for _,_,d in entries),4)

    def test_passive_packet_observer_retains_all_four_sealed_native_fingerprints(self):
        golden=json.loads((ROOT/'research/portable-lock-packet-bindings-v1-expected.json').read_text())
        entries,_=suite.parent.prepare()
        for (name,_,domain),expected in zip(entries,golden['entries']):
            self.assertEqual(name,expected['name'])
            if domain is not None:self.assertEqual(suite.cross.digest(suite.parent.native_reference(domain)),expected['native_sha256'])

    def test_exact_source_inverse_and_unchanged_live_capacity(self):
        from portable_live_lock_source_contract import project_sources
        from portable_lock_packet_layout import check
        ledger=json.loads((ROOT/'tests/fixtures/portable-live-lock-source-delta.json').read_text());old=project_sources(ROOT)
        for name,row in ledger['sources'].items():
            self.assertEqual(old[name],row['baseline'])
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n// mutation'})
        self.assertEqual(check(ROOT)['actor_set_capacity'],32)

if __name__=='__main__':unittest.main()
