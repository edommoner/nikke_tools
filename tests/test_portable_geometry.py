import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from portable_runtime import compile_program, UnsupportedPortable
from portable_geometry_specs import from_roster, validate
from timer_registry_cases import NAMES


class GeometryInput(unittest.TestCase):
    def setUp(self):
        self.chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
        self.geometry=from_roster(self.chars,dict(core_px=1,distance=25))

    def effect(self,condition=None,stat='atk_pct'):
        return dict(name='geometry',source='스킬1',type='buff',stat=stat,fixed_value=1,target='self',duration=-1,
                    trigger=dict(timing=['on_attack'],condition=[condition] if condition else []))

    def test_geometry_effects_cannot_compile_without_literal_context(self):
        for effect in [self.effect('core_hit'),self.effect('optimal_range'),self.effect(stat='optimal_range_min'),self.effect(stat='optimal_range_max_pct')]:
            with self.subTest(effect=effect):
                with self.assertRaises(UnsupportedPortable):
                    compile_program(self.chars,[(effect,NAMES[0])],[[0,0,7,0,0,-1,0,0]],[1000]*5)

    def test_malformed_and_ambiguous_geometry_is_rejected(self):
        changes=[lambda g:g.update(core_px=True),lambda g:g.update(core_px=-1),lambda g:g.update(core_px=2**2048),lambda g:g.update(core_px=float('nan')),
                 lambda g:g.update(distance=float('inf')),lambda g:g.update(optimal_weapons=['AR']),
                 lambda g:g.update(distance=None,optimal_weapons=['AR','AR']),lambda g:g.update(unknown=1),
                 lambda g:g['weapons'].pop(),lambda g:g['weapons'][0].update(type='invalid'),
                 lambda g:g['weapons'][0].update(minimum=100,maximum=0),lambda g:g['weapons'][0].update(maximum=float('nan'))]
        for change in changes:
            g=copy.deepcopy(self.geometry);change(g)
            with self.subTest(g=g):
                with self.assertRaises(ValueError):validate(g)

    def test_compilation_retains_caller_metadata_and_authored_effects(self):
        effects=[(self.effect('core_hit'),NAMES[0]),(self.effect('optimal_range'),NAMES[0])]
        before=copy.deepcopy((self.chars,self.geometry,effects))
        compile_program(self.chars,effects,[[0,0,7,0,0,-1,0,0]],[1000]*5,geometry=self.geometry)
        self.assertEqual((self.chars,self.geometry,effects),before)


if __name__=='__main__':unittest.main()
