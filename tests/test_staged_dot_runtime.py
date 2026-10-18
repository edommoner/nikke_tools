import sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from staged_dot_specs import specification
from staged_dot_runtime import prepare,tick,damage_stack,zero,binding
from effect_runtime import pool,state

def effects(count=3,override=1,name='ramp',parent='parent',gap=.2,cap=10):
    attack=dict(name=parent,type='damage',stat='sequential_damage:'+str(count),target='target')
    dot=dict(name=name,type='damage',stat='dot_damage',target='same_target:'+parent,scaling='stack_count',max_stack=cap,tick_interval=.4,duration=2,ramp_interval=gap,post_ramp_tick_delay=.5)
    if override is not None:dot['ramp_damage_stack']=override
    return attack,dot

def manager(attack,dot):
    carrier=SimpleNamespace(uid=1,effect=dot,caster='owner',stack=1,expires_at=2)
    events=[];m=SimpleNamespace(_effects=[(attack,'owner'),(dot,'owner')],_active=[carrier],_dot_timers={},_bump_value_version=lambda:None,ref_count=lambda caster,name:None)
    m._damage_handler=lambda effect,caster,t:events.append((t,carrier.stack,damage_stack(m,effect,caster)))
    return m,carrier,events

class StagedDotTests(unittest.TestCase):
    def test_compiled_fractional_cap_fails_before_cuda(self):
        import engine_worker as a
        import detail_gpu as g
        names=['리타','크라운','앨리스','모더니아','N102']
        chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in names]
        attack,dot=effects()
        for e in (attack,dot):e['source']='스킬1';e['fixed_value']=100;e['trigger']=dict(timing=['battle_start'],condition=[])
        program=g.compile_effects(chars,[(attack,names[0]),(dot,names[0])])
        next(row for row in program['effects'] if row[340]>0)[9]=1.5
        stats={n:dict(atk=1000,hp=10000,**{'def':0}) for n in names}
        with self.assertRaisesRegex(ValueError,'staged periodic'):g.run(None,[program],[[0,0,0,0,0,-1,0,0]],[[0,0]],[stats])
    def test_count_is_latched_before_registration_callbacks(self):
        attack,dot=effects('resource');m,c,events=manager(attack,dot);m.ref_count=lambda owner,name:3
        bound=binding(m,dot,'owner',0);m.ref_count=lambda owner,name:0
        prepare(m,dot,'owner',0,bound);self.assertEqual(pool(m,'staged_dot')[1].total,3)
    def test_fixed_damage_is_separate_from_accumulating_state_and_tail_clock(self):
        attack,dot=effects();m,c,events=manager(attack,dot);prepare(m,dot,'owner',0)
        self.assertEqual(c.stack,0);self.assertAlmostEqual(c.expires_at,2.6)
        self.assertAlmostEqual(m._dot_timers[id(dot)][1],1.1)
        for t in (.200001,.400001,.600001):tick(m,t)
        self.assertEqual([(s,v) for t,s,v in events],[(1,1),(2,1),(3,1)])
        self.assertEqual(c.stack,3)
    def test_accumulated_damage_and_cap(self):
        for cap,expected in ((10,[1,2,3]),(1,[1,1,1])):
            attack,dot=effects(override=None,cap=cap);m,c,events=manager(attack,dot);prepare(m,dot,'owner',0);tick(m,.600001)
            self.assertEqual([v for t,s,v in events],expected)
    def test_due_order_is_deadline_then_binding_order(self):
        a,da=effects(2,None,'A','parentA',.1);b,db=effects(1,None,'B','parentB',.15)
        m,c,events=manager(a,da);cb=SimpleNamespace(uid=2,effect=db,caster='owner',stack=1,expires_at=2)
        m._active.append(cb);m._effects.extend([(b,'owner'),(db,'owner')]);m._damage_handler=lambda e,owner,t:events.append((e['name'],damage_stack(m,e,owner)))
        prepare(m,da,'owner',0);prepare(m,db,'owner',0);tick(m,.21)
        self.assertEqual(events,[('A',1),('B',1),('A',2)])
    def test_child_refresh_cancels_old_due_steps_without_restoring_old_stack(self):
        for refreshes in (1,130):
            with self.subTest(refreshes=refreshes):
                attack,dot=effects(3,1,gap=.1);m,c,events=manager(attack,dot);prepare(m,dot,'owner',0)
                def damage(e,owner,t):
                    events.append(damage_stack(m,e,owner))
                    if len(events)==1:
                        for _ in range(refreshes):prepare(m,e,owner,t)
                        self.assertEqual(damage_stack(m,e,owner),0)
                m._damage_handler=damage;tick(m,.21)
                self.assertEqual(events,[1]);self.assertEqual(c.stack,0)
                self.assertEqual(pool(m,'staged_dot')[1].generation,1+refreshes)
                tick(m,.310001);self.assertEqual(events,[1,1]);self.assertEqual(c.stack,1)
    def test_removed_carrier_does_not_receive_old_steps(self):
        attack,dot=effects();m,c,events=manager(attack,dot);prepare(m,dot,'owner',0);m._active.clear();tick(m,1)
        self.assertEqual(events,[])
    def test_exception_restores_query_scope_and_present_zero_is_not_missing(self):
        attack,dot=effects('resource');m,c,events=manager(attack,dot);m.ref_count=lambda owner,name:0
        self.assertTrue(zero(m,dot,'owner'))
        m.ref_count=lambda owner,name:2;prepare(m,dot,'owner',0)
        def fail(*args):raise RuntimeError('authored child error')
        m._damage_handler=fail
        with self.assertRaises(RuntimeError):tick(m,.21)
        self.assertEqual(state(m).damage_stack_scopes,[]);self.assertEqual(c.stack,1)
    def test_descriptor_rejects_ambiguous_reference_and_capacity(self):
        attack,dot=effects(65)
        with self.assertRaises(ValueError):specification(dot,'owner',[(attack,'owner'),(dot,'owner')])
        attack,dot=effects()
        with self.assertRaises(ValueError):specification(dot,'owner',[(attack,'owner'),(attack,'owner'),(dot,'owner')])

if __name__=='__main__':unittest.main()
