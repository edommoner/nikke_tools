"""Typed membership/quotas on real actor providers; spatial/game rules separate."""
import copy,sys,unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import engine_worker
from named_generation_locks import GenerationLocks,NamedGenerationLocks,MODEL,registry_views,MAX_ACTORS
from impact_specs import ActorHandle,ActorKind
from world_actor_runtime import ActorSnapshot,ActorRegistry,registry_for
from calculator.boss_pattern import BossScript,validate,ADD_PREFIX
from portable_heavyarms_lock_cases import source_definitions
from test_target_counter_runtime import manager,NAMES

def view(kind,identity,generation=1,alive=True):
    return ActorSnapshot(ActorHandle(kind,identity,generation),str((kind,identity)),alive)

def core():return GenerationLocks(capacity_limit=256,eligible_kinds=tuple(ActorKind),model=MODEL)
def candidate(row):return row.handle

class GenerationLockTests(unittest.TestCase):
    def test_repeated_acquisitions_exclude_locked_handles_and_preserve_kind(self):
        state=core();rows=[view(k,0) for k in ActorKind];choices=[candidate(row) for i,row in enumerate(rows)]
        got=[state.acquire(rows,choices,capacity=6).selected for _ in rows]
        self.assertEqual(got,[r.handle for r in rows]);self.assertEqual(len(set(got)),6)
        self.assertIsNone(state.acquire(rows,choices,capacity=6).selected)
        self.assertEqual(state.snapshot().handles,tuple(got))
    def test_external_order_is_preserved_without_geometry_or_identity_sort(self):
        state=core();rows=[view(5,1),view(0,0),view(1,0)]
        choices=[rows[2].handle,rows[0].handle,rows[1].handle]
        self.assertEqual(state.acquire(rows,choices,capacity=3).selected,rows[2].handle)
        self.assertEqual(state.acquire(rows,choices,capacity=3).selected,rows[0].handle)
        self.assertEqual(state.acquire(rows,choices,capacity=3).selected,rows[1].handle)
    def test_rebirth_drops_exact_old_generation_without_aliasing_new_one(self):
        state=core();old=view(5,0);state.acquire([old],[candidate(old)],capacity=5);frozen=state.snapshot()
        new=view(5,0,2);answer=state.acquire([new],[candidate(old),candidate(new)],capacity=5)
        self.assertEqual(answer.selected,new.handle);self.assertEqual([(r.handle,r.reason) for r in answer.removed],[(old.handle,'generation_replaced')])
        self.assertEqual(frozen.handles,(old.handle,));self.assertEqual(state.snapshot().handles,(new.handle,))
        with self.assertRaisesRegex(ValueError,'backwards'):state.sync([old])
        self.assertEqual(state.snapshot().handles,(new.handle,))
    def test_dead_absent_and_unknown_candidates_never_retarget_to_body(self):
        state=core();body=view(0,0);add=view(5,0);state.acquire([body,add],[candidate(add)],capacity=5)
        dead=view(5,0,alive=False);result=state.acquire([body,dead],[candidate(add)],capacity=5)
        self.assertIsNone(result.selected);self.assertEqual(result.snapshot.handles,());self.assertEqual(result.removed[0].reason,'not_live')
        state.acquire([body,add],[candidate(add)],capacity=5);self.assertEqual(state.sync([body])[0].handle,add.handle)
        self.assertIsNone(state.acquire([body],[ActorHandle(2,99)],capacity=5).selected)
    def test_snapshot_survives_physical_clear_and_capacity_drop_is_not_eviction(self):
        state=core();rows=[view(5,i) for i in range(15)];choices=[candidate(r) for i,r in enumerate(rows)]
        for _ in rows:state.acquire(rows,choices,capacity=15)
        frozen=state.snapshot();answer=state.acquire(rows,choices,capacity=5)
        self.assertEqual(answer.reason,'capacity_reached');self.assertEqual(answer.snapshot,frozen)
        self.assertEqual(state.clear('normal_attack'),frozen);self.assertEqual(state.snapshot().handles,())
        self.assertEqual(len(frozen.handles),15)
        with self.assertRaises(FrozenInstanceError):frozen.revision=0
        state.acquire(rows,choices,capacity=5);state.clear('taking_cover');self.assertEqual(state.snapshot().handles,())
        with self.assertRaises(ValueError):state.clear('arbitrary')
    def test_invalid_candidates_or_views_fail_before_any_state_mutation(self):
        state=core();row=view(0,0);state.acquire([row],[candidate(row)],capacity=5);before=copy.deepcopy(vars(state))
        for views,choices,capacity in [([row,row],[],5),([row],[candidate(row),candidate(row)],5),([row],[],True),([row],[],257),([object()],[],5)]:
            with self.subTest(capacity=capacity),self.assertRaises(ValueError):state.acquire(views,choices,capacity=capacity)
            self.assertEqual(vars(state),before)
        for value in (object(),0,True,None):
            with self.assertRaises(ValueError):state.acquire([row],[value],capacity=5)
            self.assertEqual(vars(state),before)
    def test_explicit_context_and_bound_are_required(self):
        for kw in (dict(capacity_limit=257),dict(capacity_limit=True),dict(model='implicit'),dict(eligible_kinds=[]),dict(eligible_kinds=[True])):
            args=dict(capacity_limit=256,eligible_kinds=[0,1,5],model=MODEL);args.update(kw)
            with self.subTest(kw=kw),self.assertRaises(ValueError):GenerationLocks(**args)
        state=core();rows=[view(5,i) for i in range(MAX_ACTORS+1)]
        with self.assertRaises(ValueError):state.sync(rows)

class NamedLockRegistryTests(unittest.TestCase):
    def make(self,bm=None,caster=0,marker='록 온'):
        bm=bm or manager([source_definitions()[20]])
        return NamedGenerationLocks(bm,NAMES[caster],marker,base_count=5,capacity_limit=256,eligible_kinds=(0,1,2,3,4,5),model=MODEL)
    def test_original_source20_quota_is_read_fresh_and_scoped_to_caster_and_name(self):
        bm=manager([source_definitions()[20]]);model=self.make(bm);other=self.make(bm,1);named=self.make(bm,marker='other')
        self.assertEqual(model.capacity(0),5);bm._activate(bm._effects[0][0],NAMES[0],1.)
        self.assertEqual(model.capacity(1.1),15);self.assertEqual(other.capacity(1.1),5);self.assertEqual(named.capacity(1.1),5)
        bm.consume_bullet_buffs(NAMES[0],2.);self.assertEqual(model.capacity(2.1),15)
        bm.consume_bullet_buffs(NAMES[0],3.);self.assertEqual(model.capacity(3.1),5)
    def test_real_boss_registry_rebirth_replaces_lock_without_touching_frozen_snapshot(self):
        raw=[dict(id='wave',kind='summon',spec=dict(count=2,hp=13))]
        enemy={'def':0,'core_px':0};boss=BossScript(validate(raw),enemy,lambda *_:True);bm=manager([source_definitions()[20]]);registry=registry_for(bm,boss);model=self.make(bm)
        before=registry_views(registry);self.assertEqual(len(before),1);boss.begin_frame(0,enemy)
        provider=lambda rows:[r.handle for r in rows if r.handle.kind==ActorKind.ADD]
        first=model.acquire(registry,provider,0.).selected;self.assertEqual(first,ActorHandle(ActorKind.ADD,0,1));snapshot=model.capture(registry,0.)
        boss._open(boss._runs[0],1.,'start',[])
        second=model.acquire(registry,provider,1.).selected;self.assertEqual(second,ActorHandle(ActorKind.ADD,0,2))
        self.assertEqual(snapshot.state.handles,(first,));self.assertEqual(model.capture(registry,1.).state.handles,(second,))
        boss._runs[0].active=False;self.assertEqual(model.capture(registry,1.1).state.handles,())
    def test_providers_are_read_once_and_malformed_prebirth_is_not_silently_skipped(self):
        registry=ActorRegistry();calls=[]
        registry.bind(ActorKind.ADD,'not-born',lambda:(calls.append(1) or 0,False,None),identity=0)
        self.assertEqual(registry_views(registry),());self.assertEqual(len(calls),1)
        for generation,alive in [(True,False),(0,True),(-1,False),(1,1)]:
            r=ActorRegistry();r.bind(ActorKind.ADD,'bad',lambda:(generation,alive,None))
            with self.subTest(generation=generation,alive=alive),self.assertRaises(ValueError):registry_views(r)
    def test_bad_candidate_provider_or_quota_cannot_partially_advance_membership(self):
        bm=manager([source_definitions()[20]]);model=self.make(bm);registry=ActorRegistry();registry.bind(ActorKind.BODY,'body',lambda:(1,True,None))
        before=copy.deepcopy(vars(model.core))
        with self.assertRaises(ValueError):model.acquire(registry,lambda rows:[object()],0.)
        self.assertEqual(vars(model.core),before)
        with self.assertRaises(ValueError):model.capture(registry,float('inf'))
        self.assertEqual(vars(model.core),before)

if __name__=='__main__':unittest.main()
