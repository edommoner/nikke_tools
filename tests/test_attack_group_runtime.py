import sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker  # Installs the shared catalog in its production order.
from attack_group_runtime import begin,finish,cancel,scope,seal,dispatch
from attack_group_specs import MAX_GROUPS,MAX_TARGETS
from effect_runtime import publish_impact,pool
from impact_specs import Impact,ActorHandle,ActorKind,HitFamily,HitOutcome

def manager():
    effects=[({'trigger':{'timing':['multi_hit:2','multi_hit:1']}},'A'),({'trigger':{'timing':['multi_hit:2','multi_hit:3']}},'A')]
    events=[];m=SimpleNamespace(_effects=effects,notify=lambda *args,**kw:events.append((args,kw)))
    return m,events

def hit(m,identity,kind,actor,*,owner='A',generation=1,outcome=HitOutcome.DAMAGING,credit=1):
    publish_impact(m,Impact(owner,ActorHandle(kind,actor,generation),HitFamily.WEAPON,outcome,10 if outcome==HitOutcome.DAMAGING else 0,credit,identity),0)

class AttackGroupTests(unittest.TestCase):
    def test_retained_target_tuple_survives_child_dispatch_and_errors(self):
        m,events=manager();parent=begin(m,'A',1,0,kinds=[ActorKind.ADD]);hit(m,1,ActorKind.ADD,3)
        retained=seal(m,parent,0);child=begin(m,'A',1,0,kinds=[ActorKind.ADD]);hit(m,1,ActorKind.ADD,4)
        def notify(*args,**kwargs):
            self.assertEqual(retained.result.targets,(ActorHandle(ActorKind.ADD,3),))
            if kwargs['attack_targets'] is retained.result:
                self.assertIs(pool(m,'dispatching_attack_groups')[retained.result.key],retained)
                with self.assertRaises(ValueError):dispatch(m,retained,0)
                finish(m,child,0)
                raise RuntimeError('nested failure')
        m.notify=notify
        with self.assertRaisesRegex(RuntimeError,'nested failure'):dispatch(m,retained,0)
        self.assertFalse(pool(m,'sealed_attack_groups'));self.assertFalse(pool(m,'dispatching_attack_groups'))
        self.assertEqual(retained.result.targets,(ActorHandle(ActorKind.ADD,3),))
        with self.assertRaises(ValueError):dispatch(m,retained,0)

    def test_capacity_counts_sealed_frames_and_reset_invalidates_tickets(self):
        m,events=manager();tickets=[seal(m,begin(m,'A',1,0,kinds=[ActorKind.ADD]),0) for _ in range(MAX_GROUPS)]
        with self.assertRaisesRegex(ValueError,'capacity'):begin(m,'A',1,0,kinds=[ActorKind.ADD])
        dispatch(m,tickets[0],0);begin(m,'A',1,0,kinds=[ActorKind.ADD])
        from test_target_counter_runtime import manager as real_manager,NAMES
        bm=real_manager([]);ticket=seal(bm,begin(bm,NAMES[0],1,0,kinds=[ActorKind.ADD]),0);bm.reset()
        with self.assertRaises(ValueError):dispatch(bm,ticket,0)
    def test_gpu_stimuli_cannot_forge_a_seal_or_enable_unconnected_autonomy(self):
        import detail_gpu as g
        from test_target_counter_runtime import NAMES
        chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
        e=dict(name='test',type='buff',stat='atk_pct',fixed_value=1,target='self',trigger=dict(timing=['multi_hit:2'],condition=[]))
        p=g.compile_effects(chars,[(e,NAMES[0])]);stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES};query=[0,2,103,0,0,0,0,0]
        for row,pattern in [([0,0,62,0,2,-1,0,0],'sealed attack group'),([0,10,64,0,1,-1,1,0],'boundary'),([0,11,0,0,1,-1,0,0],'boundary')]:
            with self.subTest(row=row),self.assertRaisesRegex(ValueError,pattern):g.run(None,[p],[row,query],[[0,0]],[stats])
        for row in ([0,12,0,0,1,-1,0,0],[0,13,0,0,1,-1,0,0],[0,2,132,0,1,0,0,0],[0,2,132,.5,1,0,1,0]):
            with self.subTest(row=row),self.assertRaisesRegex(ValueError,'attack-group'):g.run(None,[p],[row,query] if row[1]!=2 else [row],[[0,0]],[stats])
        with self.assertRaisesRegex(g.UnsupportedDetail,'producers are not connected'):g.run(None,[p],[[0,4,0,0,0,-1,0,0],query],[[0,0]],[stats])
    def test_real_cpu_listener_activates_only_when_the_group_is_sealed(self):
        from test_target_counter_runtime import manager as real_manager,NAMES
        effect=dict(name='group bonus',source='스킬1',type='buff',stat='atk_pct',fixed_value=10,target='self',duration=1,trigger=dict(timing=['multi_hit:2'],condition=[]))
        bm=real_manager([effect]);frame=begin(bm,NAMES[0],7,0,kinds=[ActorKind.ADD])
        for actor in (0,1):publish_impact(bm,Impact(NAMES[0],ActorHandle(ActorKind.ADD,actor),HitFamily.WEAPON,HitOutcome.DAMAGING,10,1,7),0)
        self.assertEqual(bm.get_buffs(NAMES[0],'__enemy__',0).get('atk_pct',0),0)
        finish(bm,frame,0)
        self.assertEqual(bm.get_buffs(NAMES[0],'__enemy__',0)['atk_pct'],10)
    def test_current_hit_is_collected_before_target_counter_children_and_reset(self):
        from test_target_counter_runtime import manager as counter_manager,NAMES
        from target_counter_cases import marker
        bm=counter_manager([marker(threshold=1)]);bm.notify('battle_start',0,NAMES[0])
        frame=begin(bm,NAMES[2],5,0,kinds=[ActorKind.BODY]);observed=[];original=bm.notify
        def notify(event,t,caster,**kwargs):
            if event.startswith('event:target_counter_complete:'):observed.append(finish(bm,frame,t))
            return original(event,t,caster,**kwargs)
        bm.notify=notify
        publish_impact(bm,Impact(NAMES[2],ActorHandle(ActorKind.BODY,0),HitFamily.WEAPON,HitOutcome.DAMAGING,10,1,5),0)
        self.assertEqual(observed[0].targets,(ActorHandle(ActorKind.BODY,0),))
        pending=begin(bm,NAMES[2],6,0,kinds=[ActorKind.BODY]);bm.reset()
        self.assertTrue(pending.closed);self.assertFalse(pool(bm,'attack_groups'))
    def test_distinct_targets_not_pellets_damage_or_other_owners(self):
        m,events=manager();g=begin(m,'A',1,0,kinds=[ActorKind.BODY,ActorKind.ADD])
        for _ in range(12):hit(m,1,ActorKind.BODY,0)
        hit(m,1,ActorKind.PART,1);hit(m,1,ActorKind.ADD,0,owner='B')
        hit(m,1,ActorKind.ADD,1,outcome=HitOutcome.MISS,credit=0)
        hit(m,1,ActorKind.ADD,2,outcome=HitOutcome.BLOCKED)
        r=finish(m,g,0)
        self.assertEqual(r.targets,(ActorHandle(ActorKind.BODY,0),ActorHandle(ActorKind.ADD,2)))
        self.assertEqual([args[0] for args,kw in events],['multi_hit:2','multi_hit:1'])
        self.assertTrue(all(kw['attack_targets'] is r for args,kw in events))
    def test_seal_detaches_before_child_reuses_identity_and_survives_exception(self):
        m,events=manager();g=begin(m,'A',1,0,kinds=[ActorKind.ADD]);hit(m,1,ActorKind.ADD,0)
        replacement=[]
        def child(*args,**kwargs):
            replacement.append(begin(m,'A',1,0,kinds=[ActorKind.ADD]));raise RuntimeError('child failure')
        m.notify=child
        with self.assertRaises(RuntimeError):finish(m,g,0)
        cancel(m,g);self.assertIs(pool(m,'attack_groups')['A',1],replacement[0])
        with self.assertRaises(ValueError):finish(m,g,0)
        self.assertGreater(replacement[0].key.epoch,g.key.epoch)
    def test_generations_and_attack_boundaries_are_independent(self):
        m,events=manager();a=begin(m,'A',1,0,kinds=[ActorKind.ADD]);b=begin(m,'A',2,0,kinds=[ActorKind.ADD])
        hit(m,1,ActorKind.ADD,0,generation=1);hit(m,1,ActorKind.ADD,0,generation=2);hit(m,2,ActorKind.ADD,0)
        self.assertEqual(len(finish(m,a,0).targets),2);self.assertEqual(len(finish(m,b,0).targets),1)
        with self.assertRaises(RuntimeError):
            with scope(m,'A',3,0,kinds=[ActorKind.ADD]):raise RuntimeError('producer failure')
        self.assertFalse(pool(m,'attack_groups'))
        events.clear();m._effects=[({'trigger':{'timing':['multi_hit:1']}},'A')]
        fresh=begin(m,'A',4,0,kinds=[ActorKind.ADD]);hit(m,4,ActorKind.ADD,0);finish(m,fresh,0)
        self.assertEqual([args[0] for args,kw in events],['multi_hit:1'])
    def test_capacity_and_invalid_input_fail_before_partial_insertion(self):
        m,events=manager()
        for kwargs in ({'identity':0},{'t':float('nan')},{'kinds':[]},{'kinds':[True]}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):begin(m,**{**dict(caster='A',identity=1,t=0,kinds=[ActorKind.ADD]),**kwargs})
        for identity in range(1,MAX_GROUPS+1):begin(m,'A',identity,0,kinds=[ActorKind.ADD])
        with self.assertRaises(ValueError):begin(m,'A',MAX_GROUPS+1,0,kinds=[ActorKind.ADD])
        for actor in range(MAX_TARGETS):hit(m,1,ActorKind.ADD,actor)
        with self.assertRaises(ValueError):hit(m,1,ActorKind.ADD,MAX_TARGETS)
        self.assertEqual(len(pool(m,'attack_groups')['A',1].targets),MAX_TARGETS)

if __name__=='__main__':unittest.main()
