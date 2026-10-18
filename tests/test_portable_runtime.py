import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
import engine_worker
from portable_runtime import compile_program,UnsupportedPortable
from portable_specs import check_schema,LIMITS
from timer_registry_cases import cases,prepare,NAMES


class PortableBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
        self.effects=prepare(next(cases()))._effects
        self.script=[[0,0,0,0,0,-1,0,0],[1,2,0,0,-1,0,0,0]]

    def compile(self):
        return compile_program(self.chars,self.effects,self.script,[1000]*5)

    def test_existing_authored_definitions_compile_without_mutation(self):
        before=copy.deepcopy((self.chars,self.effects,self.script))
        check_schema();program,meta=self.compile()
        self.assertEqual(len(program),LIMITS['INPUT_WORDS'])
        self.assertEqual(meta['effects'],['no critical','clock'])
        self.assertEqual((self.chars,self.effects,self.script),before)

    def test_unported_semantics_fail_before_any_gpu_dispatch(self):
        variants=[dict(trigger=dict(timing=['passive'],condition=['has_burst1_ally'])),dict(stat='max_hp_pct'),dict(target='allies_top_atk:1'),dict(scaling='stack_count'),
                  dict(trigger=dict(timing=['battle_start'],condition=['full_burst'])),
                  dict(trigger=dict(timing=['received_hit'],condition=[])),
                  dict(trigger=dict(timing=['battle_start'],condition=['self_hp_max']))]
        for change in variants:
            with self.subTest(change=change):
                saved=self.effects;self.effects=copy.deepcopy(saved)
                self.effects[0][0].update(change)
                with self.assertRaises(UnsupportedPortable):self.compile()
                self.effects=saved
        self.effects.append(copy.deepcopy(self.effects[0]))
        with self.assertRaises(UnsupportedPortable):self.compile()

    def test_descriptor_boundaries_fail_before_gpu(self):
        from portable_trigger_specs import validate_input
        validate_input(dict(trigger=dict(timing=['battle_start']*8,condition=['during_full_burst']*3)))
        for trigger in (dict(timing=['battle_start']*9),dict(timing=[]),
                        dict(timing=['battle_start'],condition=['during_full_burst']*4),
                        dict(timing=['every:0s']),dict(timing=['every:nan']),
                        dict(timing=['every:inf']),dict(timing=['received_hit']),
                        dict(timing=['battle_start'],condition=['self_hp_max'])):
            with self.subTest(trigger=trigger),self.assertRaises(ValueError):validate_input(dict(trigger=trigger))

    def test_time_dimensions_and_discrete_ranges_are_checked(self):
        for script in ([[1,0,0,0,0,-1,0,0],[0,2,0,0,-1,0,0,0]],
                       [[float('nan'),0,0,0,0,-1,0,0]],
                       [[0,2,0,0,-1,64,0,0]],[[0,0,0,5,0,-1,0,0]],
                       [[0,18,0,0,-1,-1,float('inf'),0]]):
            with self.subTest(script=script),self.assertRaises(ValueError):
                compile_program(self.chars,self.effects,script,[1000]*5)
        for maximum in (0,1.5,True,2**31):
            self.effects[0][0]['max_stack']=maximum
            with self.subTest(maximum=maximum),self.assertRaises(ValueError):self.compile()


if __name__=='__main__':unittest.main()
