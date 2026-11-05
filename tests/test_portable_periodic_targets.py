"""Retained target policy, named clock admission, and native ownership contracts."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('periodic_verifier',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from portable_specs import LIMITS as L
from portable_enemy_oracle import observe

class PeriodicTargetTests(unittest.TestCase):
    def case(self,name):return copy.deepcopy(next(c for c in json.loads((ROOT/'tests/fixtures/portable-periodic-targets.json').read_text())['cases'] if c['name']=='periodic-target-'+name))
    def test_named_union_is_owner_local_and_requires_single_stack_dot(self):
        c=self.case('named-alias-unions-in-insertion-order');v.compile_case(c)
        for patch in [dict(stat='auto_damage'),dict(max_stack=2),dict(tick_interval=0),dict(type='buff',stat='atk_pct')]:
            bad=copy.deepcopy(c);bad['effects'][2].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):v.compile_case(bad)
        c=self.case('same-name-different-owner-independent');w,_=v.compile_case(c)
        self.assertEqual([w[L['PERIODIC_DEFINITION_BASE']+i*2+1] for i in (1,2)],[0,0])
    def test_group_requires_combat_owned_targets(self):
        c=self.case('named-alias-unions-in-insertion-order');c.pop('combat');c['script']=[[0,0,0,0,0,-1,0,0]]
        for e in c['effects'][1:]:e['target']='target'
        with self.assertRaisesRegex(ValueError,'combat-owned targets'):v.compile_case(c)
    def test_own_and_external_stack_scaling_are_distinct(self):
        c=self.case('own-stack-scaling');v.compile_case(c)
        c['effects'][1]['scaling_ref']='unported resource'
        words,_=v.compile_case(c)
        self.assertEqual((words[L['REFERENCE_DEFINITION_BASE']+4]>>2)&3,3)
        c['effects'][1].pop('scaling_ref');c['effects'][1]['scaling']='max_hp'
        with self.assertRaisesRegex(ValueError,'own-stack DoT'):v.compile_case(c)
    def test_native_alias_preserves_clock_and_first_coefficient(self):
        c=self.case('named-alias-unions-in-insertion-order');cpu=observe(c)
        self.assertEqual([s[1]['due'] for s in cpu['periodic_snapshots']],[.25,.5,.75,1,1.25])
        self.assertTrue(all(p['delivered_amount']==1000 for p in cpu['packets']))
        self.assertEqual(cpu['periodic_snapshots'][1][1]['targets'],['__enemy__:1','__enemy__','__enemy__:2'])
        self.assertTrue(all(not s[2]['active'] for s in cpu['periodic_snapshots']))
    def test_native_stack_lifetime_does_not_imply_coefficient_scaling(self):
        plain=observe(self.case('stack-count-without-scaling-is-not-coefficient'));scaled=observe(self.case('own-stack-scaling'))
        self.assertEqual([p['delivered_amount'] for p in plain['packets']],[1000]*4)
        self.assertEqual([p['delivered_amount'] for p in scaled['packets']],[2000,3000,3000,3000])
    def test_native_drop_prevents_reappeared_actor_inheriting_the_old_dot(self):
        cpu=observe(self.case('retirement-and-respawn'))
        self.assertEqual([p['target_order'] for p in cpu['packets']],[[0,1,2],[0,2],[0,2],[0,2]])

if __name__=='__main__':unittest.main()
