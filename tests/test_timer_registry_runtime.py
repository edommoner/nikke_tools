import sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from timer_registry_runtime import TimerRegistry,owns,execute
from timer_registry_cases import cases,exercise,prepare
from effect_runtime import state


class TimerRegistryTests(unittest.TestCase):
    def test_authored_boundaries_and_nested_clock_operations(self):
        for case in cases():
            with self.subTest(case=case['name']):self.assertTrue(exercise(case)['passed'])

    def test_clock_identity_refresh_recreation_and_reset(self):
        for preserve in (False,True):
            r=TimerRegistry({1:('a',.25,1)},preserve_phase=preserve);first=r[1]
            r[1]=('a',.25,2);self.assertEqual(owns(r[1],first),preserve)
            r.pop(1);r[1]=('a',.25,1);self.assertFalse(owns(r[1],first))
            current=r[1];r[1]=('a',.5,1);self.assertFalse(owns(r[1],current))
        bm=prepare(next(cases()));self.assertIsInstance(bm._dot_timers,TimerRegistry)
        bm.register_damage_handler(lambda *_:None);bm.notify('battle_start',0,bm.squad_names[0]);self.assertTrue(bm._dot_timers)
        bm.reset();self.assertEqual(bm._dot_timers,{});self.assertIsInstance(bm._dot_timers,TimerRegistry)

    def test_both_families_commit_before_children_cancel_insert_and_exception(self):
        for damage in (False,True):
            timers=TimerRegistry({1:('a',.25,1),2:('b',.25,1)},preserve_phase=damage)
            effect=dict(duration=1,tick_interval=.25,trigger={})
            bm=NS(_dot_timers=timers if damage else {},_instant_timers={} if damage else timers,_eff_by_id={1:effect,2:effect,3:effect})
            seen=[]
            def fire(eff,caster,t,**kw):
                seen.append(caster);self.assertEqual(timers[1][1],.5)
                timers.pop(2);timers[3]=('c',.25,1)
            bm._damage_handler=fire;bm._dispatch_instant=fire
            execute(bm,.25,damage=damage);self.assertEqual(seen,['a']);self.assertIn(3,timers)
            self.assertEqual(state(bm).event_stack,[])
            r=timers[1]
            def fail(*args,**kw):raise ValueError('clock callback')
            bm._damage_handler=fail;bm._dispatch_instant=fail
            with self.assertRaisesRegex(ValueError,'clock callback'):execute(bm,.5,damage=damage)
            self.assertIs(timers[1],r);self.assertEqual(state(bm).event_stack,[])


if __name__=='__main__':unittest.main()
