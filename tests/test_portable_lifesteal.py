"""Native packet ordering and incomplete-family admission boundaries."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_lifesteal_oracle import observe
from portable_lifesteal_reference import native_lifesteal
from portable_runtime import UnsupportedPortable
sp=importlib.util.spec_from_file_location('vlife',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
CASES=json.loads((ROOT/'tests/fixtures/portable-lifesteal-prototype.json').read_text())['cases']
class LifestealTests(unittest.TestCase):
    def case(self,name):return copy.deepcopy(next(c for c in CASES if c['name']==name))
    def test_installed_native_routine_has_no_substituted_formula_or_closure(self):
        f=native_lifesteal();self.assertEqual(f.__code__.co_name,'_apply_lifesteal');self.assertEqual(f.__code__.co_freevars,());self.assertIn('apply_shared_body_heal',f.__code__.co_names)
    def test_hand_health_boundaries_match_native(self):
        for c in CASES:
            with self.subTest(c=c['name']):v.contains(observe(c)['queries'],c['expected_queries'])
    def test_positive_rate_notifies_at_cap_and_at_zero_potency(self):
        for name in ('life-full-hp-still-notifies','life-negative-received-clamps-potency','life-rate-underflows-but-notifies'):
            with self.subTest(name=name):self.assertEqual(sum(e['event']=='event:heal_received' for e in observe(self.case(name))['events']),1)
    def test_nonpositive_rate_and_downed_actor_do_not_notify(self):
        for name in ('life-zero-rate-no-notice','life-negative-rate-no-notice','life-down-attacker-no-revival'):
            with self.subTest(name=name):self.assertFalse(any(e['event']=='event:heal_received' for e in observe(self.case(name))['events']))
    def test_native_normal_shot_finishes_notifications_before_lifesteal(self):
        r=observe(self.case('life-auto-attack-notice-grants-this-shot'));events=[e['event'] for e in r['events']]
        self.assertEqual(events.count('event:heal_received'),4);self.assertLess(events.index('on_attack'),events.index('event:heal_received'));self.assertLess(events.index('hit_count'),events.index('event:heal_received'))
    def test_ally_provider_uses_attackers_heal_source_and_outgoing_factor(self):
        c=self.case('life-authored-single-packet');c['owners'][1]=1;c['effects'][1]['target']='all_allies';c['owners'][3]=1;c['effects'][3]['fixed_value']=300
        r=observe(c);self.assertEqual(r['queries'][0]['allies'][0]['hp'],150)
        self.assertEqual([e['source'] for e in r['events'] if e['event']=='event:heal_received'],[0])
    def test_incomplete_skill_landing_family_is_not_opened_in_production(self):
        for c in CASES:
            with self.subTest(name=c['name']),self.assertRaisesRegex(UnsupportedPortable,'Unported buff or recipient selector'):v.compile_case(c)
if __name__=='__main__':unittest.main()
