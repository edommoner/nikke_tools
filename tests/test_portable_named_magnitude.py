"""Named magnitude proof input contracts and exercised native semantics;GPU0."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_named_magnitude_cases import fixtures
from portable_runtime import validate_effect,UnsupportedPortable
from portable_named_magnitude_specs import STATS
from portable_specs import LIMITS as L,FIELDS as F
from world_projectile_native import observe


class NamedMagnitudeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('named_magnitude_test_adapter',ROOT/'research/verify-world-named-magnitude-short.py')
        cls.adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.adapter)

    def test_private_named_contract_rejects_missing_identity_and_missing_quantity(self):
        effect=next(c for c in fixtures() if c['name']=='named-mag-damage-value-50')['effects'][0]
        for changes,world,combat in [({},False,{}),({},True,None),({'type':'instant'},True,{}),({'target_effect':''},True,{}),({'target_effect':3},True,{})]:
            with self.subTest(changes=changes),self.assertRaises(UnsupportedPortable):validate_effect(dict(effect,**changes),world_frame=world,combat=combat)
        absent=dict(effect);absent.pop('fixed_value')
        with self.assertRaisesRegex(UnsupportedPortable,'authored quantity'):validate_effect(absent,world_frame=True,combat={})
        validate_effect(effect,world_frame=True,combat={})

    def test_lowering_retains_canonical_named_ids_without_battle_or_gpu(self):
        from calculator import timeline
        import portable_backend
        def forbidden(*a,**kw):raise AssertionError('Execution during named lowering')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):
            entries,raw=self.adapter.prepare()
        self.assertEqual(sum(e[2] is None for e in entries),11)
        for name,words,domain in entries:
            if domain is None:continue
            case,metadata,_=domain
            for i,effect in enumerate(case['effects']):
                if effect.get('stat') not in STATS:continue
                at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']
                self.assertEqual(words[at+F['KIND']],0)
                self.assertEqual(words[at+F['STAT']],STATS[effect['stat']])
                self.assertEqual(words[at+F['TARGET_NAME']],metadata['states'][effect['target_effect']])
            if name=='named-mag-received-boss-base-early':
                self.assertEqual(words[L['WORLD_OVERLAY_NODE_BASE']+11],metadata['states']['world·received_dmg_pct']+1)

    def test_full_native_state_observers_and_independent_amplification_witnesses(self):
        cases=fixtures();before=copy.deepcopy(cases);results={c['name']:observe(c)[0] for c in cases}
        self.assertEqual(cases,before)
        base=results['named-mag-damage-baseline']['damage']
        raised=results['named-mag-damage-value-50']['damage']
        self.assertGreater(raised[0],base[0]);self.assertEqual(raised[1:],base[1:])
        for name in ('damage-other-caster','damage-wrong-name','damage-finite-condition-no-carrier','damage-value-0'):
            self.assertEqual(results['named-mag-'+name]['damage'],base)
        for name in ('damage-other-recipient-still-applies','damage-runtime-false-direct-carrier','damage-enemy-carrier-still-applies','damage-gear'):
            self.assertEqual(results['named-mag-'+name]['damage'],raised)
        base=results['named-mag-received-baseline']['damage']
        for name in ('received-wrong-name','received-runtime-false','received-ally-amplifier-does-not-match'):
            self.assertEqual(results['named-mag-'+name]['damage'],base)
        raised=results['named-mag-received-amplified']['damage']
        self.assertTrue(all(a>b for a,b in zip(raised,base)))
        self.assertEqual(results['named-mag-received-other-owner-allowed']['damage'],raised)
        self.assertGreater(results['named-mag-pending-early']['damage'][0],results['named-mag-pending-late']['damage'][0])
        for case in cases:
            self.assertTrue('named_state' in results[case['name']],case['name'])
            self.assertTrue('enemy_fields' in results[case['name']],case['name'])


if __name__=='__main__':unittest.main()
