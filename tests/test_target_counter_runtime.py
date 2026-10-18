import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from effect_runtime import state,publish_impact,pool,observes_impacts
from impact_specs import ActorHandle,Impact
from target_counter_specs import specification
from target_counter_runtime import target_death
from target_counter_cases import marker,clone_cases
NAMES=['리타','크라운','앨리스','모더니아','N102']

def manager(effects,owners=None):
    class BM(BuffManager):
        def _register_all(self):
            self._effects=[(copy.deepcopy(e),NAMES[owner]) for e,owner in zip(effects,owners or [0]*len(effects))];self._build_notify_index()
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=10000,**{'def':100}) for n in NAMES},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={}))
    state(bm).counter_trace=[]
    return bm

def observe(bm):
    rows=[r for r in pool(bm,'target_hit_counter').values() if any(ab is r.carrier for ab in bm._active)]
    return len(rows),sum(r.credit for r in rows),len(state(bm).counter_trace),state(bm).counter_epoch

def exercise(case):
    bm=manager(case['effects']);observed=[];completed=[];original=bm.notify
    def notify(event,t,caster,**ctx):
        if event.startswith('event:target_counter_complete:'):
            c=ctx['completion'];completed.append(c)
            assert all(r.done for r in pool(bm,'target_hit_counter').values() if r.credit>=r.spec.threshold)
        return original(event,t,caster,**ctx)
    bm.notify=notify
    for t,action in case['actions']:
        bm.tick(t);kind,*args=action
        if kind in ('activate','refresh'):bm.notify('battle_start' if kind=='activate' else 'on_attack',t,NAMES[0])
        elif kind=='hit':
            f,o,k,i,g,credit,damage,*who=args;publish_impact(bm,Impact(NAMES[who[0] if who else 2],ActorHandle(k,i,g),f,o,damage,credit),t)
        else:target_death(bm,ActorHandle(*args),t)
        observed.append(observe(bm))
    assert observed==case['expected'],(case['name'],observed,case['expected'])
    return bm,completed

class TargetCounterRuntime(unittest.TestCase):
    def test_shared_credit_lifetime_and_completion_table(self):
        for case in clone_cases():
            with self.subTest(name=case['name']):exercise(case)
    def test_completion_context_is_immutable_and_only_retires_its_epoch(self):
        from dataclasses import FrozenInstanceError
        case=next(c for c in clone_cases() if c['name']=='completion-refresh-survives-parent-retirement')
        bm,completed=exercise(case)
        self.assertEqual([c.epoch for c in completed],[1,2]);self.assertEqual(completed[0].uid,completed[1].uid)
        self.assertEqual(completed[0].actor,ActorHandle(0,0,1))
        with self.assertRaises(FrozenInstanceError):completed[0].epoch=9
        self.assertEqual(state(bm).event_stack,[]);self.assertEqual(state(bm).impact_stack,[])
    def test_explicit_policy_boundaries_and_fast_uninterested_manager(self):
        good=marker();self.assertEqual(specification(good).threshold,2)
        mutations=[lambda e:e.pop('target_counter'),lambda e:e['target_counter'].update(threshold=0),
            lambda e:e['target_counter'].update(families=['ammo']),lambda e:e['target_counter'].update(outcomes=['miss']),
            lambda e:e['target_counter'].update(refresh='guess'),lambda e:e['target_counter']['actor'].update(generation=0),
            lambda e:e.update(max_stack=2),lambda e:e.update(duration_bullets=10),lambda e:e.update(stat='possessed')]
        for mutate in mutations:
            e=copy.deepcopy(good);mutate(e)
            with self.assertRaises(ValueError):specification(e)
        bm=manager([]);self.assertFalse(observes_impacts(bm))
    def test_same_name_and_actor_are_private_to_each_owner(self):
        bm=manager([marker(threshold=1),marker(threshold=1)],[0,1])
        bm.notify('battle_start',0,NAMES[0]);bm.notify('battle_start',0,NAMES[1])
        publish_impact(bm,Impact(NAMES[2],ActorHandle(0,0,1),0,2,13),.1)
        self.assertEqual(observe(bm),(0,0,2,2))
        self.assertEqual([c.owner for _,c in state(bm).counter_trace],NAMES[:2])
    def test_compiler_fields_and_forged_counter_fail_before_cuda(self):
        import detail_gpu as g
        chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
        p=g.compile_effects(chars,[(marker(),NAMES[0])]);r=p['effects'][0]
        self.assertEqual(r[295:304],[2,0,0,1,7,4,0,1,0])
        for key,value in [(295,0),(296,6),(298,0),(299,0),(300,1),(303,2)]:
            forged=copy.deepcopy(p);forged['effects'][0][key]=value
            with self.assertRaises(ValueError):g.run(None,[forged],[[0,2,127,0,-1,0,0,0]],[[0,0]],[{}])
        with self.assertRaises(ValueError):g.run(None,[p],[[0,0,58,0,0,-1,0,0],[0,2,127,0,-1,0,0,0]],[[0,0]],[{}])
    def test_single_body_model_does_not_admit_unresolved_components(self):
        from detail_coverage import body_for,a
        import detail_gpu as g
        owner='일레그 : 붐 앤 쇼크'
        b=body_for(['N102','크라운','앨리스','모더니아',owner],8,True)
        b['enemy']['parts']=[dict(name='component',hp=100000,reach=1)]
        for gpu in (False,True):
            with self.assertRaises((ValueError,g.UnsupportedDetail)):a.evaluate({**b,**({'_compile_gpu_detail':True} if gpu else {})})
    def test_child_exception_preserves_refreshed_epoch_and_restores_context(self):
        e=marker(threshold=1);e['trigger']['timing']=['battle_start','event:target_counter_complete:marker'];e['max_trigger']=2
        bm=manager([e]);bm.notify('battle_start',0,NAMES[0]);original=bm._notify
        def fail_after_refresh(event,t,caster):
            original(event,t,caster)
            if event=='event:target_counter_complete:marker':raise RuntimeError('child failure')
        with patch.object(bm,'_notify',fail_after_refresh),self.assertRaisesRegex(RuntimeError,'child failure'):
            publish_impact(bm,Impact(NAMES[2],ActorHandle(0,0,1),0,2,13),.1)
        self.assertEqual(observe(bm),(1,0,1,2));self.assertEqual(state(bm).event_stack,[]);self.assertEqual(state(bm).impact_stack,[]);self.assertEqual(bm._notify_ctx,{})
        publish_impact(bm,Impact(NAMES[2],ActorHandle(0,0,1),0,2,13),.2)
        self.assertEqual(observe(bm),(0,0,2,2))

if __name__=='__main__':unittest.main()
