import sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from periodic_target_cases import prepare,exercise,reentrant_exercise,predicate_exercise,sibling_exercise,NAMES,world_patterns
from effect_runtime import state
from impact_specs import ActorHandle


class PeriodicTargetTests(unittest.TestCase):
    def test_authored_fire_time_selection_gate_boundary_and_reentrant_refresh(self):
        for policy in ('current','boss','all'):
            with self.subTest(policy=policy):self.assertTrue(exercise(policy)['passed'])
        self.assertTrue(reentrant_exercise()['passed'])
        self.assertTrue(predicate_exercise()['passed'])
        self.assertTrue(sibling_exercise()['passed'])

    def test_registration_ownership_cancellation_sibling_refresh_and_exception_scope(self):
        from periodic_target_runtime import tick
        effects={1:dict(duration=1,tick_interval=.125,trigger={}),2:dict(duration=1,tick_interval=.125,trigger={})}
        def build():return NS(_instant_timers={1:('a',.125,1)},_eff_by_id=effects)
        m=build();m._dispatch_instant=lambda *args,**kwargs:m._instant_timers.pop(1)
        tick(m,.140625);self.assertEqual(m._instant_timers,{})
        m=build();m._instant_timers[2]=('b',.125,1);called=[]
        def refresh(effect,caster,t,from_tick):called.append(caster);m._instant_timers[2]=('b',.5,2)
        m._dispatch_instant=refresh;tick(m,.140625)
        self.assertEqual(called,['a']);self.assertEqual(m._instant_timers[2],('b',.5,2));self.assertEqual(state(m).event_stack,[])
        m=build()
        def fail(*args,**kwargs):raise ValueError('timer witness')
        m._dispatch_instant=fail
        with self.assertRaisesRegex(ValueError,'timer witness'):tick(m,.140625)
        self.assertEqual(state(m).event_stack,[]);self.assertEqual(m._instant_timers[1],('a',.125,1))

    def test_control_aim_stale_generation_world_change_and_reset(self):
        from world_actor_runtime import registry_for
        bm,boss,enemy=prepare();boss.begin_frame(0,enemy)
        self.assertIsNone(bm.sample_control_aim(NAMES[0]));bm.set_control_aim(NAMES[0],ActorHandle(5,1,1))
        self.assertEqual(bm.sample_control_aim(NAMES[0]),ActorHandle(5,1,1))
        boss.begin_frame(.375,enemy);self.assertEqual(bm.sample_control_aim(NAMES[0]),ActorHandle(0,0,1))
        with self.assertRaises(ValueError):bm.set_control_aim(NAMES[0],ActorHandle(5,1,1))
        bm.set_control_aim(NAMES[0],ActorHandle(5,1,2));registry_for(bm,None)
        self.assertIsNone(bm.sample_control_aim(NAMES[0]));bm.set_control_aim(NAMES[0],ActorHandle(0,0,1));bm.reset()
        self.assertIsNone(bm.sample_control_aim(NAMES[0]))

    def test_missing_aim_and_invalid_control_fail_before_cuda(self):
        from detail_gpu import compile_effects,run
        from detail_boss import compile_world
        from detail_coverage import a
        bm,*_=prepare();chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
        program=compile_effects(chars,bm._effects,enemy_fields=True);raw=world_patterns();program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
        finish=[[.01,2,135,0,0,0,12,1],[.02,5,0,0,0,-1,0,0]]
        with self.assertRaisesRegex(ValueError,'explicit time0 aim'):run(None,[program],[[0,15,0,0,0,-1,0,0]]+finish,[[0,0]],[bm.state['base_stats']])
        for at,value in ((2,1),(3,.5),(4,3),(5,0),(6,.5),(7,1)):
            control=[0,17,0,0,0,1,0,0];control[at]=value
            with self.subTest(at=at,value=value),self.assertRaises(ValueError):run(None,[program],[[0,15,0,0,0,-1,0,0],control]+finish,[[0,0]],[bm.state['base_stats']])
