"""Shared admission contracts for logical enemy selection."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import validate_effect
spec=importlib.util.spec_from_file_location('spawn_verifier',ROOT/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class EnemySpawnAdmissionTests(unittest.TestCase):
    def test_logical_nearest_alias_keeps_combat_and_clock_guards(self):
        e=dict(name='near',type='damage',stat='damage',fixed_value=100,target='enemies_nearest_in_range',trigger=dict(timing=['on_attack'],condition=[]))
        validate_effect(e,combat={})
        with self.assertRaises(ValueError):validate_effect(e)
        with self.assertRaises(ValueError):validate_effect({**e,'tick_interval':.2,'duration':1},combat={})
    def test_enemy_buff_defense_ranks_share_the_damage_model_guard(self):
        for route in ('high','low'):
            template=next(c for c in v.fixtures() if c['name']=='enemy-spawn-buff-defense-'+route)
            for stat in ('def_pct','def_caster_based_pct','received_dmg_pct'):
                c=copy.deepcopy(template);c['effects'][0]['stat']=stat
                v.compile_case(c)
                c['combat']['targets'][1]['defense']=1
                with self.subTest(route=route,stat=stat),self.assertRaisesRegex(ValueError,'zero add defenses'):v.compile_case(c)

if __name__=='__main__':unittest.main()
