import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('portable_timeline_verify',ROOT/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


class PortableTimelineBoundaryTests(unittest.TestCase):
    def setUp(self):self.case=copy.deepcopy(next(c for c in v.fixtures() if c['name']=='autonomous-180-seconds'))

    def test_timeline_input_contains_endpoints_not_cpu_frame_states(self):
        from portable_specs import LIMITS as L
        words,metadata=v.compile_case(self.case)
        self.assertTrue(metadata['timeline']);self.assertEqual(words[2],2)
        self.assertEqual(words[L['COMMAND_BASE']],24)
        self.assertEqual(words[L['COMMAND_BASE']+8],2)
        self.assertEqual(words[5],0)

    def test_mixed_clocks_and_invalid_diagnostic_policy_fail_closed(self):
        cases=[]
        for trace in ('truncate',False,None):
            c=copy.deepcopy(self.case);c['combat']['trace']=trace;cases.append(c)
        for script in ([[0,4,0,0,0,-1,0,0],[1,24,0,0,0,-1,0,0]],
                       [[0,24,0,0,0,-1,0,0],[1,4,0,0,0,-1,0,0]],
                       [[181,24,0,0,0,-1,0,0]],[[1,24,0,0,1,-1,0,0]],
                       [[1,24,0,0,0,-1,1,0]]):
            c=copy.deepcopy(self.case);c['script']=script;cases.append(c)
        for c in cases:
            with self.subTest(c=c['script'],trace=c['combat']['trace']),self.assertRaises(ValueError):v.compile_case(c)

    def test_real_weapon_normalization_never_ticks_cpu(self):
        import engine_worker
        from portable_weapon_input import normalize_static_weapon
        from calculator.timeline import CharState,DEFAULT_ENEMY
        from portable_combat import pack_combat
        from portable_runtime import double_words
        from portable_specs import LIMITS as L
        name='모더니아';char=dict(name=name,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[name])
        with patch.object(CharState,'tick',side_effect=AssertionError('CPU weapon tick called')):
            weapon=normalize_static_weapon(char,1000,DEFAULT_ENEMY)
        self.assertEqual(weapon['mode'],'auto_warmup')
        pack_combat([0]*L['INPUT_WORDS'],dict(weapons=[weapon]+[dict(enabled=False) for _ in range(4)],targets=[{'hp':1000}]),double_words)
        self.assertGreater(weapon['rate_max'],weapon['rate'])

    def test_real_definition_audit_never_executes_cpu_battle(self):
        import engine_worker
        from detail_coverage import body_for
        names=['모더니아','루주','마스트 : 로망틱 메이드','도라','얀']
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU battle called')):
            result=engine_worker.evaluate({**body_for(names),'_audit_portable':True})
        self.assertEqual(result['character'],names[0]);self.assertGreater(result['own_effects'],0)
        self.assertFalse(result['cpu_simulation_executed']);self.assertFalse(result['full_character_verified'])
        self.assertFalse(result['actual_battle_adapter_connected'])


if __name__=='__main__':unittest.main()
