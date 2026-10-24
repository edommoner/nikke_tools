import sys,unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from impact_specs import ActorHandle,ActorKind,HitFamily,HitOutcome,Impact,ImpactTrace,impact_command,decode_command,classify_hit,gpu_source_matches
from effect_runtime import state,publish_impact,CATALOG


class ImpactContract(unittest.TestCase):
    def packet(self,**kwargs):
        return Impact(**dict(attacker='a',target=ActorHandle(ActorKind.PART,3,7),family=HitFamily.WEAPON,outcome=HitOutcome.DAMAGING,damage=125,**kwargs))
    def test_identity_generation_and_wire_boundaries(self):
        names=['a','b']
        for kind in ActorKind:
            for family in HitFamily:
                for outcome in HitOutcome:
                    p=Impact('b',ActorHandle(kind,2**28-1,2**31-1),family,outcome,7 if outcome==2 else 0,0 if outcome==0 else .25,2**24-1)
                    self.assertEqual(decode_command(impact_command(.5,p,names),names),p)
        p=self.packet()
        with self.assertRaises(FrozenInstanceError):p.target.generation=9
        self.assertTrue(gpu_source_matches())
    def test_invalid_descriptors_and_independent_credit(self):
        for thunk in (lambda:ActorHandle(True,0),lambda:ActorHandle(0,True),lambda:ActorHandle(0,0,0),
                      lambda:Impact('a',ActorHandle(0,0),0,0,0,1),lambda:Impact('a',ActorHandle(0,0),0,1,5),
                      lambda:Impact('a',ActorHandle(0,0),0,2,float('nan')),
                      lambda:decode_command([0,8,0,.5,0,1,0,0],['a'])):
            with self.assertRaises(ValueError):thunk()
        trace=ImpactTrace();trace.record(self.packet(),.5)
        row=trace.fields(['a']);self.assertEqual(row[25:27],[1,125]);self.assertEqual(row[27:30],[1,3,7])
        self.assertEqual([classify_hit(t) for t in ('normal_skill','core:pellet:1','full_charge','dot_damage','sequential_damage')],[1,0,0,2,1])
    def test_nested_delivery_context_and_failure_cleanup(self):
        import engine_worker
        from calculator.buff_manager import BuffManager
        manager=BuffManager.__new__(BuffManager);manager._effects=[];manager._active=[];manager._notify_ctx={}
        manager.is_down=lambda name:False
        p=self.packet();seen=[]
        def deliver(event,t,caster):
            seen.append((event,state(manager).event_stack[-1].impact,manager.notify_ctx('impact')))
            if event=='hit_count:parent':
                manager.notify('squad_ammo_consume:1',t,caster)
                manager.notify('hit_count:child',t,caster)
                seen.append(('restored',state(manager).event_stack[-1].impact,manager.notify_ctx('impact')))
        manager._notify=deliver
        def handler(owner,packet,t):
            owner.notify('hit_count:parent',t,'a')
            raise ValueError('witness')
        with patch.object(CATALOG,'impact_interests',((handler,None),)),self.assertRaisesRegex(ValueError,'witness'):
            publish_impact(manager,p,.5)
        self.assertEqual(seen,[('hit_count:parent',p,p),('squad_ammo_consume:1',None,None),('hit_count:child',p,p),('restored',p,p)])
        self.assertEqual(state(manager).event_stack,[]);self.assertEqual(state(manager).impact_stack,[]);self.assertEqual(manager._notify_ctx,{})
        with self.assertRaises(TypeError):manager.notify('hit_count:bad',0,'a',impact={})
        self.assertEqual(state(manager).event_stack,[])
    def test_native_target_receipt_distinguishes_parts_interrupt_and_retired(self):
        import engine_worker
        from impact_runtime import target_landing
        manager=NS();state(manager).impact_trace=ImpactTrace()
        run=NS(p=NS(kind='parts',targets=[NS(name='left')],summon=None),opens=7,active=True,targets=[NS(spec=NS(name='left'),destroyed=False)])
        boss=NS(target_kinds={'left':'parts'},_runs=[run])
        event=NS(target='left',part='',caster='a',hit_tag='skill',damage=13)
        for answer in ('parts','interrupt',''):
            with patch.object(boss,'hit_target',side_effect=AssertionError('No native replay'),create=True):target_landing(manager,event,.5,boss,answer)
        self.assertEqual(state(manager).impact_trace.count,1)
        self.assertEqual(state(manager).impact_trace.last.target,ActorHandle(ActorKind.PART,0,7))

    def test_target_capture_keeps_native_total_then_typed_impact_then_lifesteal(self):
        import ast
        from impact_runtime import Landings
        source="""def simulate():
 def _land_target(ev,t):
  if boss.hit_target(ev,t)=='parts':events.append('total')
  _apply_lifesteal(ev,bm,base_stats,t)
 _land_target(None,0)
"""
        rewrite=Landings();tree=ast.fix_missing_locations(rewrite.visit(ast.parse(source)))
        self.assertEqual(rewrite.counts,dict(body=0,part=0,target=1,add=0,target_capture=1))
        with self.assertRaisesRegex(ValueError,'Reserved native target'):
            Landings().visit(ast.parse(source.replace("if boss.hit_target(ev,t)=='parts':","if (_nikke_target_kind := boss.hit_target(ev,t))=='parts':")))
        for kind in ('parts','interrupt',''):
            events=[]
            def hit(*args):events.append('native');return kind
            def published(*args):
                if args[-1]=='parts':events.append('typed')
            scope=dict(events=events,boss=NS(hit_target=hit),bm=NS(publish_target_landing=published),base_stats={},_apply_lifesteal=lambda *args:events.append('heal'))
            exec(compile(tree,'native-target-order','exec'),scope);scope['simulate']()
            self.assertEqual(events,['native','total','typed','heal'] if kind=='parts' else ['native','heal'])

    def test_part_respawn_is_a_distinct_actor_and_unknown_targets_do_not_alias_body(self):
        import engine_worker
        from impact_runtime import landing
        manager=NS();state(manager).impact_trace=ImpactTrace()
        run=NS(p=NS(kind='parts',targets=[NS(name='left')],summon=None),opens=7,active=True,targets=[NS(spec=NS(name='left'),destroyed=False)])
        boss=NS(target_kinds={'left':'parts'},_runs=[run])
        event=NS(target='',part='left',caster='a',hit_tag='core:pellet:1',damage=13)
        landing(manager,event,.5,boss);first=state(manager).impact_trace.last
        run.opens=8;landing(manager,event,.6,boss);second=state(manager).impact_trace.last
        self.assertEqual(first.target,ActorHandle(ActorKind.PART,0,7));self.assertEqual(second.target,ActorHandle(ActorKind.PART,0,8))
        self.assertNotEqual(first.target,second.target)
        event.part='unknown'
        with self.assertRaisesRegex(ValueError,'explicit handle'):landing(manager,event,.7,boss)
        self.assertEqual(state(manager).impact_trace.count,2)

if __name__=='__main__':unittest.main()
