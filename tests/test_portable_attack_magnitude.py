"""Canonical79 admission, static packing and independent full-native witnesses."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_attack_magnitude_cases import fixtures
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F
from world_projectile_native import observe

class AttackMagnitudeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=importlib.util.spec_from_file_location('attack_magnitude_test',ROOT/'research/verify-world-attack-magnitude-short.py');cls.adapter=importlib.util.module_from_spec(s);s.loader.exec_module(cls.adapter)

    def test_private_identity_and_static_input_have_no_battle_or_gpu_values(self):
        from calculator import timeline
        import portable_backend
        def forbidden(*a,**kw):raise AssertionError('Execution forbidden during static input construction')
        with patch.object(timeline,'simulate',forbidden),patch.object(timeline.CharState,'tick',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):entries,_=self.adapter.prepare()
        self.assertEqual(len(entries),52);self.assertEqual(sum(d is None for _,_,d in entries),10)
        for _,words,domain in entries:
            if domain is None:continue
            c,metadata,_=domain
            for i,e in enumerate(c['effects']):
                if e.get('stat')!='atk_buff_mag_pct':continue
                at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']
                self.assertEqual(words[at+F['KIND']],0);self.assertEqual(words[at+F['STAT']],79)
                self.assertEqual(words[at+F['TARGET_NAME']],metadata['states'][e['target_effect']])
                self.assertEqual((words[L['RECIPIENT_BASE']+i*8+7]>>2)&1,0)
        effect=fixtures()[2]['effects'][1]
        for changes,world,combat in [({},False,{}),({},True,None),({'target_effect':''},True,{}),({'type':'instant'},True,{})]:
            with self.assertRaises(UnsupportedPortable):validate_effect(dict(effect,**changes),world_frame=world,combat=combat)

    def test_native_additive_factor_membership_and_deliberate_runtime_omission(self):
        cases=fixtures();before=copy.deepcopy(cases);rows={c['name']:observe(c)[0] for c in cases};self.assertEqual(cases,before)
        baseline=rows['attack-mag-baseline']['damage'];raised=rows['attack-mag-value-50']['damage']
        self.assertTrue(all(a>b for a,b in zip(raised,baseline)))
        for name in ('value-0','wrong-name','finite-false-no-carrier'):
            self.assertEqual(rows['attack-mag-'+name]['damage'],baseline,name)
        self.assertEqual(rows['attack-mag-other-owner-applies']['damage'],raised)
        self.assertEqual(rows['attack-mag-runtime-false-still-applies']['damage'],raised)
        one=rows['attack-mag-one-recipient']['damage'];self.assertGreater(one[1],baseline[1]);self.assertEqual(one[:1]+one[2:],baseline[:1]+baseline[2:])
        self.assertTrue(all(a>b for a,b in zip(rows['attack-mag-two-additive']['damage'],raised)))
        for name,row in rows.items():self.assertTrue('named_state' in row,name);self.assertTrue('enemy_fields' in row,name)
        self.assertEqual(rows['attack-mag-enemy-amplifier-does-not-affect-allies']['actor_add_damage'],baseline)
        def grant_recipients(label):return next(c['recipients'] for c in rows['attack-mag-'+label]['named_state']['allied_carriers'] if c['name']=='grant')
        self.assertEqual(grant_recipients('base-lazy'),[0])
        self.assertEqual(grant_recipients('base-lazy-incoming-freezes-before-rank-reversal'),[1])

    def test_stat79_does_not_amplify_ordinary_attack_or_copy_or_enemy_incoming(self):
        cases={c['name']:c for c in fixtures()}
        for label in ('only-atk-caster','only-atk-caster-hp','only-atk-caster-copy','enemy-attack-not-amplified'):
            c=cases['attack-mag-'+label];without=copy.deepcopy(c);without['effects']=without['effects'][:-1];without['owners']=without['owners'][:-1]
            actual=observe(c)[0];base=observe(without)[0]
            self.assertEqual(actual['damage'],base['damage'],label);self.assertEqual(actual['allies'],base['allies'],label)

if __name__=='__main__':unittest.main()
