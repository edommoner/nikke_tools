"""Seeded recipient semantics, private admission and immutable preparation."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_enemy_selection_cases import fixtures
from portable_enemy_specs import damage_plan
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L
from world_projectile_native import observe


class EnemySelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('selection_test_adapter',ROOT/'research/verify-world-enemy-selection-short.py')
        cls.adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.adapter)

    def test_parser_private_boundary_and_native_code_convention(self):
        effect=fixtures()[1]['effects'][0]
        self.assertEqual(damage_plan(effect),(10,1,1))
        self.assertEqual(damage_plan(dict(effect,target='enemies_random:256')),(10,128,1))
        for target in ('enemies_random:','enemies_random:0','enemies_random:-1','enemies_random:00','enemies_random:257','enemies_random:1:2','enemies_code:','enemies_lowest_hp_code:x:0'):
            with self.subTest(target=target),self.assertRaises(ValueError):damage_plan(dict(effect,target=target))
        for target in ('enemies_code:전격','enemies_code:풍압','enemies_lowest_hp_code:풍압:1'):
            self.assertEqual(damage_plan(dict(effect,target=target)),(1,1,1))
            with self.assertRaises(UnsupportedPortable):validate_effect(dict(effect,target=target),combat={})
        with self.assertRaises(UnsupportedPortable):validate_effect(effect,world_frame=True)
        with self.assertRaises(UnsupportedPortable):validate_effect(effect,combat={})
        validate_effect(effect,combat={},world_frame=True)

    def test_literal_inputs_have_no_battle_or_rng_outputs_embedded(self):
        from calculator import timeline
        import portable_backend
        def forbidden(*a,**kw):raise AssertionError('Battle/GPU during static recipient preparation')
        with patch.object(timeline,'simulate',forbidden),patch.object(timeline.CharState,'tick',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):
            entries,packed=self.adapter.prepare()
        self.assertEqual(len(entries),60);self.assertEqual(sum(d is not None for _,_,d in entries),51)
        for _,words,domain in entries:
            if domain is None:continue
            self.assertEqual(words[L['ENEMY_TARGET_META_BASE']:L['ENEMY_TARGET_META_BASE']+8],[1,0,0,0,0,0,0,0])
            self.assertEqual(len(words),104400)
        # Enemy-only instant plans reserve every recipient word; private stat
        # key patching must not turn valid plans into unrelated admission failures.
        for name,words,domain in entries:
            if domain is None:continue
            for row in range(words[1]):
                from portable_specs import FIELDS as F
                at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                if words[at+F['KIND']] in (15,20,26) and words[at+F['TARGET']]==2:
                    self.assertEqual(words[L['RECIPIENT_BASE']+row*8:L['RECIPIENT_BASE']+(row+1)*8],[0]*8,name)

    def test_full_native_consumes_shared_rng_and_covers_pool_set_and_twist_boundaries(self):
        cases=fixtures();before=copy.deepcopy(cases);results={c['name']:observe(c)[0] for c in cases}
        self.assertEqual(cases,before)
        for name in ('random-1-1','random-before-spawn-no-draws','random-zero-coefficient-no-draws'):
            rng=results['enemy-selection-'+name]['rng']
            self.assertEqual((rng['draws'],rng['rejects'],rng['samples']),(0,0,0))
            self.assertEqual(rng['state'],list(random.Random(0).getstate()[1][:-1]))
        default=results['enemy-selection-random-default-one']
        explicit=results['enemy-selection-random-5-1']
        self.assertEqual(default['rng'],explicit['rng']);self.assertEqual(default['damage'],explicit['damage'])
        for population,k in ((21,1),(22,1),(85,6),(86,6),(128,21),(128,22)):
            self.assertGreater(results[f'enemy-selection-random-{population}-{k}']['rng']['samples'],0)
        twist=results['enemy-selection-random-buff128-128']['rng']
        self.assertGreater(twist['draws'],1248);self.assertGreater(twist['samples'],5)
        self.assertTrue(results['enemy-selection-random-shared-with-boss-victims']['hits'])
        code=[results['enemy-selection-code-buff-7-'+t] for t in ('enemies_code:전격','enemies_code:풍압','enemies_lowest_hp_code:풍압:1')]
        self.assertEqual(code[0]['damage'],code[1]['damage']);self.assertEqual(code[0]['damage'],code[2]['damage'])
        for row in results.values():
            self.assertEqual(len(row['rng']['state']),624)
            self.assertTrue('named_state' in row and 'enemy_fields' in row)
        budget=results['enemy-selection-random-budget-zero-damage']['rng']
        self.assertEqual(budget['samples'],1) # Budget probe before coefficient0.
        phase=next(c for c in cases if c['name']=='enemy-selection-dot-named-removal-restarts-phase')
        _,ticks=self.adapter.suite.inspect_native(phase)
        self.assertTrue(any(.27<=tick['created']<.31 for tick in ticks)) # Fresh phase precedes the old grid's next tick at0.3166...

    def test_rejection_stage_and_alias_oracles_cannot_be_silently_skipped(self):
        from portable_input_aliases import compare_aliases
        entries,_=self.adapter.prepare();group=next(d for _,_,d in entries if d is not None and len(d[3])>1)
        calls=[]
        def compare(d):calls.append(d);return {'same':1}
        self.assertEqual(compare_aliases(group,compare),{'same':1});self.assertEqual(len(calls),len(group[3]))
        with self.assertRaises(ValueError):compare_aliases(group,lambda d:{'name':d[0]['name']})
        block=[0]*786432;block[0]=64;block[786416]=0x57504144;block[786417]=404
        self.adapter.validate_rejection_stage(block,'reject/enemy-selection-nan')
        block[786417]=12
        with self.assertRaisesRegex(ValueError,'Wrong admission stage'):self.adapter.validate_rejection_stage(block,'reject/enemy-selection-nan')


if __name__=='__main__':unittest.main()
