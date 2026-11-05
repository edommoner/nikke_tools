"""Nested target lifetime and selection contracts, independent of characters."""
import unittest
from impact_specs import ActorHandle,ActorKind,Impact
from effect_runtime import state
from test_target_counter_runtime import manager,NAMES


class TargetContextTests(unittest.TestCase):
    pass

    def test_nested_targets_restore_and_unrelated_events_use_current_aim(self):
        bm=manager([]);seen=[];old=ActorHandle(5,7,3);new=ActorHandle(5,7,4)
        def deliver(event,t,caster):
            frame=state(bm).event_stack[-1];seen.append((event,frame.target,bm._condition_ok(['target_is_add'],caster,t)))
            if event=='hit_count:parent':
                bm.notify('event:full_reload',t,caster)
                bm.notify('hit_count:child',t,caster,target_context=new)
                bm.notify('hit_count:inherited',t,caster)
                bm.notify('hit_count',t,caster)
                seen.append(('restored',frame.target,bm._condition_ok(['target_is_add'],caster,t)))
            if event=='hit_count:failure':raise ValueError('witness')
        bm._notify=deliver
        bm.notify('hit_count:parent',0,NAMES[0],target_context=old)
        self.assertEqual(seen,[('hit_count:parent',old,True),('event:full_reload',None,False),('hit_count:child',new,True),('hit_count:inherited',old,True),('hit_count',old,True),('restored',old,True)])
        with self.assertRaisesRegex(ValueError,'witness'):bm.notify('hit_count:failure',0,NAMES[0],target_context=old)
        self.assertEqual(state(bm).event_stack,[])
        self.assertFalse(bm.context_target_is_add(NAMES[0]))
        bm.enemy_resolver=lambda *_:['__enemy__:new-aim']
        self.assertTrue(bm.context_target_is_add(NAMES[0]))
        for target in (ActorHandle(0,0),ActorHandle(1,3)):
            bm.notify('hit_count:part-or-body',0,NAMES[0],target_context=target)
            self.assertFalse(seen[-1][2])

    def test_conflicting_or_unknown_target_policies_fail_without_context_leaks(self):
        bm=manager([]);bm._notify=lambda e,t,c:bm.context_target_is_add(c)
        packet=Impact(NAMES[0],ActorHandle(5,0,7),0,2,1)
        with self.assertRaisesRegex(ValueError,'Conflicting'):bm.notify('hit_count:bad',0,NAMES[0],impact=packet,target_context=ActorHandle(5,0,8))
        with self.assertRaises(TypeError):bm.notify('hit_count:bad',0,NAMES[0],target_context={})
        with self.assertRaisesRegex(ValueError,'actor policy'):bm.notify('hit_count:unknown',0,NAMES[0],target_context=ActorHandle(ActorKind.PROJECTILE,0))
        self.assertEqual(state(bm).event_stack,[])
