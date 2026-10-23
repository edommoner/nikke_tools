"""Private bridge keeps native arithmetic/lifecycle and rejects forged receipts."""
import copy
import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript,validate
from calculator.sim_result import HitEvent
from impact_specs import ActorKind,ActorHandle
from portable_interrupt_runtime import InterruptHandle,InterruptRegistry,capture_interrupt_landings
from portable_interrupt_aim_cases import fixtures
from portable_interrupt_aim_contracts import verify
from world_interrupt_aim_native import observe
from world_focus_aim_native import observe as unbridged_observe


def world():
    enemy={'def':0,'core_px':0}
    raw=[dict(id='stop',kind='interrupt',targets=[dict(name='stop',hp=1)],after=['start','stop'],repeat=2,until=dict(targets_cleared=True))]
    boss=BossScript(validate(raw),enemy,lambda *_:True)
    return boss,enemy


def event(tag='normal'):
    return HitEvent(t=0,caster='owner',damage=7,is_crit=False,hit_tag=tag,target='stop')


class InterruptAimTests(unittest.TestCase):
    def test_observer_preserves_uninstrumented_native_battle_trace_and_read_counts(self):
        # Disable the optional typed publication only in this baseline. Its
        # current actor registry cannot represent interrupts. All native hit,
        # accounting, lifesteal and lifecycle executors remain enabled.
        for case in fixtures():
            counts=[[],[]]
            def measured(run,out):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get, \
                     patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live, \
                     patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=run(case);out.extend([get.call_count,live.call_count,sample.call_count]);return result
            with self.subTest(case=case['name']):
                with patch.object(BuffManager,'publish_landing',lambda *args:None):plain,trace=measured(unbridged_observe,counts[0])
                actual,recorded=measured(observe,counts[1]);self.assertTrue(verify(case,actual)['verified'])
                actual.pop('interrupt_landings')
                self.assertEqual(actual,plain);self.assertEqual(recorded,trace);self.assertEqual(*counts)

    def test_registry_uses_exact_native_spawn_generation(self):
        boss,enemy=world();registry=InterruptRegistry(boss)
        with self.assertRaisesRegex(ValueError,'not spawned'):registry.view('stop')
        boss.begin_frame(0,enemy);first=registry.view('stop')
        self.assertEqual(first.handle,InterruptHandle(0,1));self.assertTrue(first.alive)
        boss.hit_target(event(),0)
        self.assertFalse(registry.exact(first.handle).alive)
        boss.begin_frame(1/60,enemy)
        self.assertEqual(registry.view('stop').handle,InterruptHandle(0,2))
        with self.assertRaisesRegex(ValueError,'Stale'):registry.exact(first.handle)
        with self.assertRaises(TypeError):registry.exact(ActorHandle(ActorKind.PROJECTILE,0))
        with self.assertRaises(ValueError):registry.view('missing')
        self.assertEqual([int(k) for k in ActorKind],list(range(6)))

    def test_native_receipts_are_required_and_single_use(self):
        boss,enemy=world();boss.begin_frame(0,enemy);ev=event();manager=NS()
        hit,landing=BossScript.hit_target,BuffManager.publish_landing
        with capture_interrupt_landings() as receipts:
            self.assertEqual(boss.hit_target(ev,0),'interrupt')
            with self.assertRaisesRegex(ValueError,'awaiting'):boss.hit_target(ev,0)
            BuffManager.publish_landing(manager,ev,0,boss)
            self.assertEqual(len(receipts),1)
            self.assertEqual(receipts[0].canonical_credit,0)
            with self.assertRaisesRegex(ValueError,'requires'):BuffManager.publish_landing(manager,ev,0,boss)
            with self.assertRaises(RuntimeError):
                with capture_interrupt_landings():pass
        self.assertIs(BossScript.hit_target,hit);self.assertIs(BuffManager.publish_landing,landing)
        with self.assertRaisesRegex(ValueError,'Unpublished'):
            with capture_interrupt_landings():boss.hit_target(event(),0)
        self.assertIs(BossScript.hit_target,hit);self.assertIs(BuffManager.publish_landing,landing)

    def test_capacity_nonweapon_and_forged_publication_fail_closed(self):
        for capacity in (True,0,-1,65537):
            with self.assertRaises(ValueError):
                with capture_interrupt_landings(capacity=capacity):pass
        boss,enemy=world();boss.begin_frame(0,enemy)
        with capture_interrupt_landings(capacity=1) as receipts:
            with self.assertRaises(ValueError):boss.hit_target(event('skill:x'),0)
            with self.assertRaisesRegex(ValueError,'requires'):BuffManager.publish_landing(NS(),event(),0,boss)
            ev=event();boss.hit_target(ev,0);BuffManager.publish_landing(NS(),ev,0,boss)
            with self.assertRaisesRegex(ValueError,'capacity'):boss.hit_target(event(),0)
            self.assertEqual(len(receipts),1)

    def test_noninterrupt_publication_is_forwarded_and_receipts_precede_lifesteal(self):
        manager=NS();ev=event()
        with patch.object(BuffManager,'publish_landing') as publisher:
            with capture_interrupt_landings() as receipts:
                BuffManager.publish_landing(manager,ev,0,None)
            publisher.assert_called_once_with(manager,ev,0,None)
            self.assertEqual(receipts,[])
        case=next(c for c in fixtures() if c['name']=='interrupt-aim-lifesteal')
        original=BuffManager.notify;seen=[]
        with capture_interrupt_landings() as receipts:
            def notifying(bm,name,*args,**kwargs):
                if name=='event:heal_received':
                    self.assertGreater(len(receipts),0)
                    seen.append(len(receipts))
                return original(bm,name,*args,**kwargs)
            with patch.object(BuffManager,'notify',notifying):unbridged_observe(case)
        self.assertEqual(seen,list(range(1,7)))

    def test_full_receipt_contract_detects_identity_credit_lifecycle_and_quantity_faults(self):
        case=fixtures()[-2];native,_=observe(case)
        for field in ('generation','credit','hits','accounting','hp','damage'):
            bad=copy.deepcopy(native);row=bad['interrupt_landings'][0]
            if field=='generation':row['target']['generation']+=1
            elif field=='credit':row['canonical_credit']=1
            elif field=='hits':row['after']['hits']+=1
            elif field=='accounting':row['accounted_after']+=1
            elif field=='hp':bad['allies'][0]['hp']+=1
            else:row['damage']+=1
            with self.subTest(field=field),self.assertRaises(AssertionError):verify(case,bad)


if __name__=='__main__':unittest.main()
