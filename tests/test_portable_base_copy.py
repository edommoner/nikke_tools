"""Copy policy rejection, immutable native workloads and canonical packing."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_base_copy_cases import fixtures
from portable_base_copy_specs import FLAG,MAGIC,OFFSET,STATE_BASE,STATE_WORDS
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import validate_effect,UnsupportedPortable
from world_projectile_native import observe


class BaseCopyTests(unittest.TestCase):
    def test_native_static_hp_sync_policy_is_encoded_without_battle_state(self):
        spec=importlib.util.spec_from_file_location('copy_policy_adapter',ROOT/'research/verify-world-base-copy-short.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        from world_enemy_attack_cases import field
        cases=fixtures()
        negative=next(c for c in cases if c['name']=='base-copy-hp_copy--10')
        positive=next(c for c in cases if c['name']=='base-copy-hp_copy-50')
        self.assertEqual(module.suite.compile_case(negative)[0][L['HP_UNCLAMP_POLICY']],1)
        self.assertEqual(module.suite.compile_case(positive)[0][L['HP_UNCLAMP_POLICY']],1)
        synchronized=copy.deepcopy(negative)
        synchronized['effects'].append(field('max_hp_only_pct',10,'self','finite',duration=.3))
        synchronized['owners'].append(0)
        self.assertEqual(module.suite.compile_case(synchronized)[0][L['HP_UNCLAMP_POLICY']],0)

    def test_policy_requires_exact_selector_and_private_combat(self):
        effect=fixtures()[0]['effects'][0]
        for changes,world,combat in [({'copy_from':'allies_top_hp:2'},True,{}),({},False,{}),({},True,None),({'scaling':'lost_hp_pct'},True,{}),({'duration_bullets':2},True,{}),({'type':'instant'},True,{})]:
            with self.subTest(changes=changes),self.assertRaises(UnsupportedPortable):
                validate_effect(dict(effect,**changes),world_frame=world,combat=combat)
        validate_effect(effect,world_frame=True,combat={})

    def test_packing_keeps_canonical_identities_without_execution(self):
        spec=importlib.util.spec_from_file_location('copy_adapter',ROOT/'research/verify-world-base-copy-short.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        import portable_backend
        from calculator import timeline
        def forbidden(*a,**k):raise AssertionError('Execution during packing')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):
            entries,raw=module.prepare()
        self.assertEqual(len(entries),47);self.assertEqual(sum(e[2] is not None for e in entries),32)
        for _,words,domain in entries:
            if domain is None:continue
            for i,effect in enumerate(domain[0]['effects']):
                if effect['stat'] not in ('atk_copy','hp_copy'):continue
                d=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS'];meta=L['MODE_BASE']+i*L['MODE_WORDS']+OFFSET
                stat=85 if effect['stat']=='atk_copy' else 86
                self.assertEqual(words[d+F['KIND']],0);self.assertEqual(words[d+F['STAT']],stat)
                self.assertEqual(words[meta:meta+4],[MAGIC,stat,1 if stat==85 else 2,0])
                self.assertEqual(words[L['DEFINITION_EXTRA_BASE']+i*L['DEFINITION_EXTRA_WORDS']+3],FLAG)
        self.assertEqual(STATE_WORDS,L['CARRIERS']*6)
        self.assertGreaterEqual(STATE_BASE,L['LAZY_BANK_BASE']+L['LAZY_BANK_WORDS'])
        self.assertLessEqual(STATE_BASE+STATE_WORDS,786416)

    def test_full_native_cases_retain_input_and_copy_observations(self):
        for case in fixtures():
            before=copy.deepcopy(case);battle,trace=observe(case)
            self.assertEqual(case,before);self.assertIn('base_copies',battle)
            for row in battle['base_copies']:
                self.assertIn(row['stat'],('atk_copy','hp_copy'))
                self.assertGreaterEqual(row['source'],0);self.assertLess(row['source'],5)
                self.assertEqual(row['basis'],case['base_atk'][row['source']] if row['stat']=='atk_copy' else case['environment']['allies'][row['source']]['base_hp'])


if __name__=='__main__':unittest.main()
