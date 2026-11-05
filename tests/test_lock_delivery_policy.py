"""Frozen generation semantics and full raw admission boundaries."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from impact_specs import ActorHandle
from world_actor_runtime import ActorSnapshot
from named_generation_locks import GenerationLocks,MODEL as LOCK_MODEL
from lock_delivery_policy import *
spec=importlib.util.spec_from_file_location('delivery_test',ROOT/'research/verify-lock-delivery.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

class DeliveryTests(unittest.TestCase):
    def frozen(self):
        handles=[ActorHandle(5,i) for i in range(3)]
        views=[ActorSnapshot(h,str(i),True) for i,h in enumerate(handles)]
        core=GenerationLocks(capacity_limit=128,eligible_kinds=[0,1,2,3,4,5],model=LOCK_MODEL)
        for _ in handles:core.acquire(views,handles,capacity=3)
        return core,core.snapshot(),views

    def test_live_clear_cannot_erase_packet_snapshot_or_change_cycle(self):
        core,snapshot,views=self.frozen();core.clear('normal_attack')
        self.assertFalse(core.snapshot().handles)
        self.assertEqual([select(snapshot,i,7,views,model=MODEL).handle.identity for i in range(1,8)],[0,1,2,0,1,2,0])
        self.assertEqual(len(snapshot.handles),3)

    def test_dead_missing_and_reborn_slots_do_not_shift_later_hits(self):
        core,snapshot,views=self.frozen()
        for now,status in [(views[1:],MISSING),([ActorSnapshot(ActorHandle(5,0), 'dead',False),*views[1:]],DEAD),([ActorSnapshot(ActorHandle(5,0,2),'reborn',True),*views[1:]],STALE)]:
            first=select(snapshot,1,4,now,model=MODEL);self.assertEqual(first.status,status)
            self.assertEqual(first.handle,ActorHandle(5,0,1));self.assertEqual(select(snapshot,2,4,now,model=MODEL).handle,ActorHandle(5,1,1))
            self.assertEqual(select(snapshot,4,4,now,model=MODEL).status,status)

    def test_explicit_policy_and_full_view_validation_precede_selection(self):
        _,snapshot,views=self.frozen();before=copy.deepcopy(snapshot)
        for hit,hits,rows,model in [(True,3,views,MODEL),(0,3,views,MODEL),(4,3,views,MODEL),(1,257,views,MODEL),(1,3,views+views[:1],MODEL),(1,3,views,'game-default')]:
            with self.subTest(hit=hit,hits=hits),self.assertRaises(ValueError):select(snapshot,hit,hits,rows,model=model)
            self.assertEqual(snapshot,before)
        from named_generation_locks import LockSnapshot
        with self.assertRaisesRegex(ValueError,'Immutable'):select(LockSnapshot(snapshot.revision,list(snapshot.handles)),1,3,views,model=MODEL)

    def test_probe_covers_all_kinds_statuses_limits_and_reserved_words(self):
        rows,_=probe.prepare();positive=[c for _,_,c in rows if c is not None]
        statuses={probe.native_reference(c)['status'] for c in positive};self.assertEqual(statuses,{READY,EMPTY,MISSING,STALE,DEAD})
        self.assertTrue(any(len(c['frozen'])==128 for c in positive))
        self.assertEqual({c['frozen'][0][0] for c in positive if c['name'].startswith('lock-delivery/typed-')},set(range(6)))
        self.assertEqual(sum(c is None for _,_,c in rows),17)

if __name__=='__main__':unittest.main()
