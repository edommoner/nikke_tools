"""Native session identity is definition/owner scoped and survives refresh only."""
import copy
import json
from pathlib import Path
import sys
import unittest

R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES
from test_weapon_mode_specs import mode
from weapon_mode_runtime import token
from portable_weapon_oracle import authored_weapon,authored_weapon_state
import engine_worker


class NativeSessionIdentity(unittest.TestCase):
    def test_new_weapon_restarts_charge_but_keeps_the_held_input(self):
        effect=mode(toggle=False,duration=10,charge=True,charge_time=.25,post_fire_delay=.25)
        bm=manager([effect]);bm.state['camera']=set();effect=bm._effects[0][0]
        char=dict(name=NAMES[0],skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[NAMES[0]]))
        weapon=dict(mode='auto',capacity=10,interval=.25)
        authored_weapon(char,weapon);actor=authored_weapon_state(char,weapon)
        actor._hold_release_t=3.0
        bm._activate(effect,NAMES[0],0)
        self.assertEqual(actor.tick(0,bm,bm.state['enemy'],{'rng_mode':'expected'}),[])
        self.assertEqual(actor.tick(.5,bm,bm.state['enemy'],{'rng_mode':'expected'}),[])
        self.assertEqual(actor._hold_release_t,3.0)
        self.assertTrue(actor.tick(3,bm,bm.state['enemy'],{'rng_mode':'expected'}))

    def test_refresh_replacement_and_owner_identity(self):
        bm=manager([mode(toggle=False,duration=1)])
        original=bm._effects[0][0]
        bm._activate(original,NAMES[0],0)
        first=token(bm,NAMES[0])
        bm._activate(original,NAMES[0],.1)
        self.assertEqual(token(bm,NAMES[0]),first)
        replacement=copy.deepcopy(original)  # same name, distinct definition
        bm._activate(replacement,NAMES[0],.2)
        second=token(bm,NAMES[0])
        self.assertNotEqual(first,second)
        bm._activate(original,NAMES[1],.2)
        self.assertNotIn(token(bm,NAMES[1]),(first,second))
        self.assertEqual(token(bm,NAMES[0]),second)
        json.dumps(bm.state['weapon_change'],allow_nan=False)

    def test_end_callback_reentry_is_not_removed_by_the_parent_end(self):
        bm=manager([mode(toggle=False,duration=1)])
        effect=bm._effects[0][0]
        bm._activate(effect,NAMES[0],0)
        first=token(bm,NAMES[0]);original=bm.notify;seen=[]
        def notify(event,t,caster,*args,**kwargs):
            if event=='event:state_end:mode':
                seen.append(token(bm,caster))
                bm._activate(effect,caster,t)
            return original(event,t,caster,*args,**kwargs)
        bm.notify=notify
        bm.end_weapon_change(NAMES[0],.1)
        self.assertEqual(seen,[0])
        self.assertNotEqual(token(bm,NAMES[0]),first)
        self.assertIs(bm.get_weapon_change(NAMES[0]),effect)


if __name__=='__main__':unittest.main()
