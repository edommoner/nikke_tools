"""The real projectile and lock executors coexist without sharing storage."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
spec=importlib.util.spec_from_file_location('lock_projectile_test',ROOT/'research/verify-lock-projectile-composition.py');suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)

class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries,_=suite.prepare();cls.observed=[suite.native_reference(d) for _,_,d in cls.entries if d]

    def test_original_projectile_definition_and_live_lock_packets_share_one_clock(self):
        from portable_heavyarms_lock_cases import source_definitions
        for c in suite.fixtures():self.assertEqual([e for e in c['effects'] if e.get('target')=='all_projectiles'],[source_definitions()[24]])
        n=self.observed[0];self.assertEqual(len(n['typed']['attacks']),1)
        attack=n['typed']['attacks'][0];self.assertTrue(attack['completed']);self.assertEqual(len(attack['receipts']),3)
        self.assertTrue(all(r['delivered'] and r['took']>0 for r in attack['receipts']))
        c=self.entries[0][2][0];source=next(i for i,e in enumerate(c['effects']) if e.get('name')==c['packet_skill'])
        self.assertEqual([r['recipients'] for r in n['skill_trace'] if r['row']==source],[[0],[1],[0],[1]])

    def test_broken_empty_and_capacity128_preserve_real_receipts(self):
        self.assertTrue(all(r['broken'] and r['took']==1 for r in self.observed[1]['typed']['attacks'][0]['receipts']))
        self.assertEqual(self.observed[2]['typed']['attacks'],[])
        self.assertEqual(len(self.observed[3]['typed']['attacks'][0]['receipts']),128)
        self.assertTrue(self.observed[4]['manual_actions']['events'])

    def test_all_old_lock_words_are_relocated_bijectively_and_tail_is_owned(self):
        from portable_lock_typed_layout import check,lock_view,OUTPUT,TYPED_END,LOCK_END
        from portable_physical_lock_layout import BASE,OUTPUT as OLD_OUTPUT
        layout=check(ROOT);self.assertEqual(layout['actor_sets'],32);self.assertEqual(layout['typed_targets'],128)
        block=[0]*OUTPUT
        for i in range(OLD_OUTPUT-BASE):block[TYPED_END+i]=i+1
        view=lock_view(block);self.assertEqual(view[BASE:],list(range(1,OLD_OUTPUT-BASE+1)))
        block[LOCK_END]=1
        with self.assertRaisesRegex(AssertionError,'tail'):lock_view(block)

    def test_static_composition_never_simulates_or_selects_recipients(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in packing')):
            entries,_=suite.prepare();self.assertEqual(len(entries),12);self.assertEqual(sum(d is not None for _,_,d in entries),7)

    def test_no_native_history_rows_removed_and_reentrant_append_order_is_preserved(self):
        old=json.loads((ROOT/'research/target-count-query-evidence/lock-projectile-composition-v1-failure-diagnostic.json').read_text())
        for n,row in zip(self.observed,old['rows'][:5]):self.assertEqual(n['skill_trace'],row['native_skill_trace'])
        self.assertEqual([r['disposition'] for r in self.observed[5]['receipt_fates'][:2]],['suppressed_native_body','ordinary_world_route'])
        self.assertEqual([r['disposition'] for r in self.observed[6]['receipt_fates'][:2]],['ordinary_world_route','suppressed_native_body'])
        self.assertEqual(len(self.observed[6]['battle']['target_counters']['completions']),1)

    def test_reusable_typed_observer_preserves_all_original_battle_fingerprints(self):
        original=suite.module('lock_typed_original_retention','research/verify-destructible-original-battle-short.py')
        golden=json.loads((ROOT/'research/portable-destructible-original-battle-short-expected.json').read_text())
        entries,_=original.prepare()
        for (_,_,domain),expected in zip(entries,golden['entries']):self.assertEqual(suite.cross.digest(original.native_reference(domain)),expected['native_sha256'])

    def test_native_same_name_packets_keep_distinct_creation_rows(self):
        import copy
        c=copy.deepcopy(suite.fixtures()[0]);c['source_effect_identity']=True;c['observe_periodic_skills']=True
        source=next(i for i,e in enumerate(c['effects']) if e.get('target')=='all_projectiles')
        c['effects'].append(dict(copy.deepcopy(c['effects'][source]),target='boss'));c['owners'].append(c['owners'][source])
        duplicate=len(c['effects'])-1
        from portable_runtime import UnsupportedPortable
        with self.assertRaisesRegex(UnsupportedPortable,'Multiple named non-buff carriers'):suite.compile_case(c)
        observed=suite.native_reference((c,None,None))
        suppressed=[observed['skill_trace'][f['index']]['row'] for f in observed['receipt_fates'] if not f['actor_effects_allowed']]
        self.assertEqual(suppressed,[source])
        self.assertEqual(len(observed['typed']['attacks']),1)
        rows=[r['row'] for r in observed['skill_trace'] if r['row'] in (source,duplicate)]
        self.assertEqual(rows,[source,duplicate])

    def test_source_inverse_requires_every_reviewed_layout_and_schema_byte(self):
        from portable_lock_typed_source_contract import project_sources
        ledger=json.loads((ROOT/'tests/fixtures/portable-lock-typed-source-delta.json').read_text());old=project_sources(ROOT)
        for name,row in ledger['sources'].items():
            self.assertEqual(old[name],row['baseline'])
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n// mutation'})

if __name__=='__main__':unittest.main()
