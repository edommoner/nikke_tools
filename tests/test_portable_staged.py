"""Staged descriptors, zero-count admission and callback-time restoration."""
import copy,json,sys,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
sp=importlib.util.spec_from_file_location('vstaged',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from portable_specs import LIMITS as L
from calculator.buff_manager import BuffManager
CASES=json.loads((ROOT/'tests/fixtures/portable-staged.json').read_text())['cases']
class StagedTests(unittest.TestCase):
    def test_static_count_and_native_capacity_validation(self):
        c=CASES[0];before=copy.deepcopy(c);words,_=v.compile_case(c);at=L['STAGED_DEFINITION_BASE']+2*8
        self.assertEqual(words[at:at+2],[1,3]);self.assertEqual(words[at+6:at+8],[0,2]);self.assertEqual(c,before)
        for field,values in [('ramp_interval',(0,True,1e-7,61)),('post_ramp_tick_delay',(-1,True,3601)),('ramp_damage_stack',(-1,True,65)),('max_stack',(0,65,True))]:
            for value in values:
                c=copy.deepcopy(CASES[0]);c['effects'][2][field]=value
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):v.compile_case(c)
    def test_zero_count_is_explicit_and_does_not_mean_missing(self):
        c=next(c for c in CASES if c['name']=='staged-literal-zero-skips-attachment');words,_=v.compile_case(c);at=L['STAGED_DEFINITION_BASE']+2*8
        self.assertEqual(words[at:at+2],[1,0]);self.assertEqual(words[L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+2],0)
    def test_parent_identity_and_staged_name_are_unique_for_owner(self):
        for change in ('missing','wrong-family','duplicate-child','duplicate-parent'):
            c=copy.deepcopy(CASES[0])
            if change=='missing':c['effects'][2]['target']='same_target:absent'
            elif change=='wrong-family':c['effects'][1]['type']='buff'
            else:c['effects'].append(copy.deepcopy(c['effects'][2 if change=='duplicate-child' else 1]));c['owners'].append(0)
            with self.subTest(change=change),self.assertRaises(ValueError):v.compile_case(c)
    def test_static_index_contains_every_staged_row_once_in_order(self):
        for c in CASES:
            words,_=v.compile_case(c);at=L['STAGED_INDEX_BASE'];expected=[i for i,e in enumerate(c['effects']) if 'ramp_interval' in e]
            self.assertEqual(words[at],len(expected));self.assertEqual(words[at+1:at+1+len(expected)],expected)
            self.assertTrue(all(v==0 for v in words[at+1+len(expected):at+1+L['DEFINITIONS']]))
    def manager(self):
        m=BuffManager.__new__(BuffManager);m._cur_t=99;m._effects=[];m._nikke_reference_health_defined=False;return m
    def test_damage_callback_time_restores_through_nested_calls(self):
        m=self.manager();seen=[]
        def handler(effect,caster,t):
            seen.append(m._cur_t)
            if effect=='outer':m._damage_handler('inner',caster,4);seen.append(m._cur_t)
        m.register_damage_handler(handler);m._damage_handler('outer','owner',3)
        self.assertEqual(seen,[3,4,3]);self.assertEqual(m._cur_t,99)
    def test_damage_callback_time_restores_on_failure_and_disable(self):
        m=self.manager()
        def fail(*args):self.assertEqual(m._cur_t,7);raise RuntimeError('expected')
        m.register_damage_handler(fail)
        with self.assertRaisesRegex(RuntimeError,'expected'):m._damage_handler({},'owner',7)
        self.assertEqual(m._cur_t,99);m.register_damage_handler(None);self.assertIsNone(m._damage_handler)
    def test_expired_callback_counts_source_at_damage_time(self):
        from portable_enemy_oracle import observe
        c=next(c for c in CASES if c['name']=='staged-expired-periodic-source-time');r=observe(c)
        self.assertEqual(r['queries'][0]['damage'][0],12000);self.assertEqual(r['packets'][-1]['time'],1.8499);self.assertEqual(r['packets'][-1]['delivered_amount'],6000)
if __name__=='__main__':unittest.main()
