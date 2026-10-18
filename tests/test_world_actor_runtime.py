"""Actor identity/lifecycle contracts, shared across weapon and skill producers."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator.boss_pattern import BossScript,validate,ADD_PREFIX
from calculator.sim_result import HitEvent
from effect_runtime import state
from impact_specs import ActorHandle,ActorKind,ImpactTrace
from impact_runtime import land_add
from world_actor_runtime import ActorRegistry,registry_for
from world_actor_specs import bindings,empty_bindings,packed_bindings,validate_bindings,ACTOR_WORDS
from test_target_counter_runtime import manager as test_manager,NAMES


def world(*,hit_hp=None):
    spec=dict(name='adds',count=2,**({'hit_hp':hit_hp} if hit_hp else {'hp':13}))
    raw=[dict(id='wave',kind='summon',spec=spec),dict(id='parts',kind='parts',targets=[dict(name='right',hp=10,reach=1),dict(name='left',hp=10,reach=1)])]
    enemy={'def':0,'core_px':0};boss=BossScript(validate(raw),enemy,lambda *_:True)
    return boss,enemy


class WorldActorTests(unittest.TestCase):
    def test_same_world_timestamp_does_not_advance_a_self_destructed_source(self):
        raw=[dict(id='wave',kind='summon',spec=dict(name='npc',count=1,hp=13,attack=dict(coeff=100,atk=200,target='slot:1',pierce=True),self_destruct=True),after=['start','wave'],repeat=2,until=dict(targets_cleared=True))]
        enemy={'def':0,'core_px':0};boss=BossScript(validate(raw),enemy,lambda *_:True)
        self.assertEqual(boss.begin_frame(0,enemy),['event:enemy_spawn','enemy_death'])
        boss.attacks.clear()
        self.assertEqual(boss.begin_frame(0,enemy),[]);self.assertEqual(boss._runs[0].opens,1);self.assertEqual(boss.attacks,[])
        self.assertEqual(boss.begin_frame(1/60,enemy),['event:enemy_spawn','enemy_death']);self.assertEqual(boss._runs[0].opens,2)
        with self.assertRaises(ValueError):boss.begin_frame(0,enemy)

    def test_source_attack_labels_survive_cpu_payload_and_gpu_readback(self):
        from detail_coverage import body_for,a
        from detail_boss import compile_world
        from detail_gpu import incoming_source_label
        raw=[dict(id='wave',kind='summon',spec=dict(name='npc',count=1,hp=1e15,attack=dict(coeff=100,atk=200,target='slot:1',pierce=True)))]
        body=body_for(NAMES,1);body['enemy']['patterns']=raw
        result=a.evaluate(body)
        self.assertEqual([(h['pattern'],h['by']) for h in result['incoming_hits']],[('wave','npc#1')])
        chars=[dict(_weapon=engine_worker.META[n]) for n in NAMES]
        w,metadata=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},{'chars':chars})
        self.assertEqual(incoming_source_label({'world':w},metadata,0),'')
        self.assertEqual(incoming_source_label({'world':w},metadata,2),'npc#1')
        for source in (1,3,.5,float('nan')):
            with self.assertRaises(RuntimeError):incoming_source_label({'world':w},metadata,source)

    def test_summon_source_packet_rejects_forged_pools_and_hp_modes(self):
        from detail_boss import compile_world,validate_world,WB,WA
        raw=[dict(id='wave',kind='summon',spec=dict(count=2,hp=13),until=dict(targets_cleared=True))]
        chars=[dict(_weapon=engine_worker.META[n]) for n in NAMES]
        packet,_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},{'chars':chars})
        validate_world(packet)
        for at,value in ((WB+89,0),(WB+90,0),(WB+90,3),(WB+91,-2),(WB+92,.5),(WB+93,1),(WB+94,2),(266,0),(WA+1+8+1,4)):
            bad=packet.copy();bad[at]=value
            with self.subTest(at=at,value=value),self.assertRaises(ValueError):validate_world(bad)
        for count in (128,1000000000):
            parsed=validate([dict(id='wave',kind='summon',spec=dict(count=count,hp=1))])
            with patch('world_actor_specs.bindings',side_effect=AssertionError('Oversized actors must not be materialized')):
                with self.assertRaisesRegex(ValueError,'capacity'):packed_bindings(parsed,{0:0})

    def test_source_packet_does_not_enable_unconnected_battle_and_keeps_attack_controls(self):
        from detail_boss import compile_world,validate_world,WB
        from detail_gpu import run,compile_effects,UnsupportedDetail
        raw=[dict(id='wave',kind='summon',spec=dict(count=1,hp=13))]
        bm=test_manager([])
        chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
        program=compile_effects(chars,[]);program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
        with self.assertRaisesRegex(UnsupportedDetail,'routing'):
            run(None,[program],[[0,4,0,0,0,-1,0,0],[1,5,0,0,0,-1,0,0],[1,2,134,0,0,0,0,0]],[[0,0]],[bm.state['base_stats']])
        with self.assertRaisesRegex(ValueError,'time0'):
            run(None,[program],[[1,15,0,0,0,-1,0,0],[2,5,0,0,0,-1,0,0],[2,2,134,0,0,0,0,0]],[[0,0]],[bm.state['base_stats']])
        raw[0]['spec']['attack']=dict(coeff=1,atk=1,target='all')
        raw[0]['spec'].update(attack_at=.3,self_destruct=True)
        w,_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
        self.assertEqual(w[WB+76:WB+78],[.3,1]);self.assertEqual(w[WB+80:WB+82],[1,1])
        for at,value in ((WB+77,2),(WB+80,0)):
            bad=w.copy();bad[at]=value
            with self.assertRaises(ValueError):validate_world(bad)

    def test_shared_binding_order_and_strict_immutable_packet(self):
        boss,enemy=world();rows=bindings([r.p for r in boss._runs])
        self.assertEqual([(int(b.kind),b.identity,b.run,b.slot) for b in rows],[(0,0,-1,0),(5,0,0,0),(5,1,0,1),(1,0,1,0),(1,1,1,1)])
        packet=empty_bindings(2)
        self.assertEqual(packet[:25],[3,0,0,0,-1,0,-1,-1,0,1,0,1,-1,0,0,0,0,1,1,1,-1,1,0,0,0])
        for index,value in ((0,0),(1,5),(1+ACTOR_WORDS+1,4),(1+ACTOR_WORDS+5,-1),(1+ACTOR_WORDS+7,1),(len(packet)-1,1)):
            bad=packet.copy();bad[index]=value
            with self.subTest(index=index),self.assertRaises(ValueError):validate_bindings(bad)
        for count in (True,-1,33):
            with self.assertRaises(ValueError):empty_bindings(count)
        with self.assertRaisesRegex(ValueError,'Dynamic part'):packed_bindings([r.p for r in boss._runs],{0:0,1:1})

    def test_compiled_static_world_uses_the_same_cpu_bindings(self):
        from detail_coverage import body_for,a
        from test_target_counter_runtime import NAMES
        from detail_boss import WA,validate_world
        body=body_for(NAMES,1);body['enemy']['parts']=[dict(name='right',hp=1,reach=1),dict(name='left',hp=0,reach=2)]
        compiled=a.evaluate({**body,'_compile_gpu_detail':True});packet=compiled['program']['world']
        self.assertEqual(packet[WA:],empty_bindings(2))
        bad=packet.copy();bad[WA+1+ACTOR_WORDS+1]=4
        # Fixed part bindings must retain the same stable index as their pool.
        with self.assertRaises(ValueError):validate_world(bad)

    def test_configured_order_live_generations_and_parent_links(self):
        boss,enemy=world();manager=NS();registry=registry_for(manager,boss)
        self.assertIs(registry_for(manager,boss),registry)
        label=ADD_PREFIX+'wave#1'
        with self.assertRaisesRegex(ValueError,'not spawned'):registry.view(ActorKind.ADD,label)
        boss.begin_frame(0,enemy)
        for index,label_part in enumerate(('right','left')):
            part=registry.view(ActorKind.PART,label_part)
            self.assertEqual(part.handle,ActorHandle(ActorKind.PART,index))
            self.assertEqual(registry.root(part.handle).handle,ActorHandle(ActorKind.BODY,0))
        first=registry.view(ActorKind.ADD,label)
        self.assertTrue(first.alive);self.assertIsNone(first.parent)
        run=boss._runs[0];boss._open(run,1,'start',[])
        second=registry.view(ActorKind.ADD,label)
        self.assertEqual(first.handle.identity,second.handle.identity)
        self.assertEqual(second.handle.generation,2)
        with self.assertRaisesRegex(ValueError,'Stale'):registry.exact(first.handle)
        run.active=False;self.assertFalse(registry.exact(second.handle).alive)
        self.assertIsNot(registry_for(manager,world()[0]),registry)

    def test_invalid_bindings_and_cycles_fail_without_identity_aliasing(self):
        registry=ActorRegistry();handle=ActorHandle(ActorKind.PART,4)
        registry.bind(ActorKind.PART,'part',lambda:(1,True,handle),identity=4)
        for args in ((ActorKind.PART,'part',lambda:None,5),(ActorKind.PART,'other',lambda:None,4),(True,'bad',lambda:None,0)):
            with self.subTest(args=args[:2]),self.assertRaises(ValueError):registry.bind(*args)
        with self.assertRaisesRegex(ValueError,'Cyclic'):registry.root(handle)
        with self.assertRaisesRegex(ValueError,'Unknown'):registry.view(ActorKind.ADD,'part')
        with self.assertRaisesRegex(ValueError,'Unknown'):registry.exact(ActorHandle(ActorKind.ADD,4))

    def test_reference_add_pool_receipts_preserve_requested_damage(self):
        for hit_hp,expected in ((None,[10,3]),(2,[1,1])):
            with self.subTest(hit_hp=hit_hp):
                boss,enemy=world(hit_hp=hit_hp);boss.begin_frame(0,enemy)
                manager=NS();trace=state(manager).impact_trace=ImpactTrace();label=ADD_PREFIX+'wave#1'
                event=HitEvent(0,'a',10,False,'normal');amounts=[]
                for _ in range(2):
                    self.assertTrue(land_add(manager,boss,event,label,0));amounts.append(trace.last.damage)
                self.assertEqual(amounts,expected);self.assertEqual(event.damage,10)
                self.assertFalse(registry_for(manager,boss).view(ActorKind.ADD,label).alive)
                self.assertEqual(state(manager).dead_actors,{ActorHandle(ActorKind.ADD,0)})
                self.assertFalse(land_add(manager,boss,event,label,0));self.assertEqual(trace.count,2)
                self.assertEqual(boss.add_dealt['a'],sum(expected));self.assertIsNone(boss._typed_add_callback)

    def test_receipt_exception_restores_callback_and_keeps_old_death_generation(self):
        boss,enemy=world();boss.begin_frame(0,enemy);manager=NS();state(manager).impact_trace=ImpactTrace()
        sentinel=lambda *args:None;boss._typed_add_callback=sentinel
        event=HitEvent(0,'a',20,False,'normal');label=ADD_PREFIX+'wave#1'
        from impact_runtime import publish_impact
        def respawn(*args):
            publish_impact(*args);boss._open(boss._runs[0],1,'start',[])
        with patch('impact_runtime.publish_impact',side_effect=respawn):self.assertTrue(land_add(manager,boss,event,label,0))
        self.assertEqual(state(manager).dead_actors,{ActorHandle(ActorKind.ADD,0,1)})
        self.assertTrue(registry_for(manager,boss).view(ActorKind.ADD,label).alive)
        self.assertIs(boss._typed_add_callback,sentinel)
        with patch('impact_runtime.publish_impact',side_effect=RuntimeError('child failure')):
            with self.assertRaisesRegex(RuntimeError,'child failure'):land_add(manager,boss,event,label,1)
        self.assertIs(boss._typed_add_callback,sentinel)

    def test_real_cpu_timeline_reaches_add_receipts_without_enabling_gpu_world(self):
        from detail_coverage import body_for,a
        from test_target_counter_runtime import NAMES
        from impact_runtime import publish_impact
        body=body_for(NAMES,1);body['enemy']['patterns']=[dict(id='wave',kind='summon',spec=dict(name='adds',count=2,hp=1))]
        seen=[]
        def record(manager,packet,t):seen.append(packet);return publish_impact(manager,packet,t)
        # Exercise the normal CPU adapter and timeline with reference-valid
        # summons, rather than manufacturing the weapon hits or bypassing input validation.
        with patch('impact_runtime.observes_impacts',return_value=True),patch('impact_runtime.publish_impact',side_effect=record):
            a.evaluate(body)
        adds=[p for p in seen if p.target.kind==ActorKind.ADD]
        self.assertEqual([(p.target,p.damage) for p in adds],[(ActorHandle(ActorKind.ADD,i),1) for i in range(2)])
        from detail_gpu import UnsupportedDetail
        with self.assertRaises((ValueError,UnsupportedDetail)):a.evaluate({**body,'_compile_gpu_detail':True})

    def test_manager_reset_discards_world_binding(self):
        from test_target_counter_runtime import manager
        bm=manager([]);boss,enemy=world();registry=registry_for(bm,boss);bm.reset()
        self.assertIsNot(registry_for(bm,boss),registry)


if __name__=='__main__':unittest.main()
