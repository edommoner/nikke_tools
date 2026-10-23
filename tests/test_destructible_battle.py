"""Actual native battle-clock contracts before the shared GPU battle hookup."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import engine_worker
from calculator import timeline,buff_manager
from runner import sim
import destructible_battle_runtime as battle
from destructible_world_runtime import DestructibleWorld
from portable_projectile_chain_cases import fixtures
import world_frame_native

BINDINGS=[dict(node='idle',kind=2,identity=10,capacity=10000.)]
def effect(name='typed',timing='battle_start',target='all_projectiles',**kwargs):
    return dict(name=name,source='스킬3',type='damage',stat='damage',fixed_value=100.,target=target,trigger=dict(timing=[timing],condition=[]),**kwargs)
def case(effects=None,repeat=False):
    c=copy.deepcopy(fixtures()[0]);c.update(name='typed-battle-contract',duration=.4,effects=[effect()] if effects is None else effects)
    c['owners']=[0]*len(c['effects']);c.update({k:False for k in c if k.startswith('observe_')})
    c['patterns']=[dict(id='idle',kind='idle',until=dict(time=.1 if repeat else 1.))]
    if repeat:c['patterns'][0].update(after=['start','idle'],repeat=3,emit=['event:target_spawn'])
    return c
def observe(c,bindings=BINDINGS,**kwargs):
    with battle.typed_battle(bindings,**kwargs) as data:result=world_frame_native.observe(c)
    return data,result

class BattleTests(unittest.TestCase):
    def test_real_scheduler_reopens_typed_generations_and_finishes(self):
        data,result=observe(case([effect(timing='event:target_spawn')],repeat=True))
        self.assertEqual([r['attack_id'] for r in data['attacks']],[1,2,3])
        self.assertEqual([r['receipts'][0][1].generation for r in data['attacks']],[1,2,3])
        self.assertTrue(all(r['completed'] for r in data['attacks']))
        self.assertEqual(result['damage'],[0.]*5)
        self.assertEqual(data['finished'],[.4]);world=data['worlds'][0]
        self.assertTrue(world.finished);self.assertFalse(world.targets.rows[0].alive)
        with self.assertRaisesRegex(ValueError,'owning battle'):world.advance(.5)
        with self.assertRaisesRegex(ValueError,'owning battle'):world.finish(.5)

    def test_scalar_is_the_existing_native_handler_and_body_is_not_scored(self):
        data,result=observe(case());_,body=observe(case([effect(target='boss')]))
        self.assertEqual(data['attacks'][0]['damage'],body['damage'][0])
        self.assertGreater(body['damage'][0],0);self.assertEqual(result['damage'],[0.]*5)
        self.assertEqual(result['rng'],body['rng'])

    def test_empty_selection_has_no_packet_or_named_child(self):
        c=case([effect(),effect('child','weapon_hit:typed',target='boss')])
        c['patterns'][0]['delay']=1.
        data,result=observe(c)
        self.assertEqual(data['attacks'],[]);self.assertEqual(len(data['activations']),1)
        self.assertEqual(result['damage'],[0.]*5)

    def test_nested_ordinary_child_keeps_its_body_landing(self):
        child=effect('child','weapon_hit:typed',target='boss')
        data,result=observe(case([effect(),child]))
        _,body=observe(case([dict(child,trigger=dict(timing=['battle_start'],condition=[]))]))
        self.assertEqual(len(data['attacks']),1);self.assertEqual(result['damage'],body['damage'])

    def test_physical_packets_and_clock_are_unchanged(self):
        c=case([]);c['combat']['weapons'][0].update(mode='auto',interval=.1,min_cycle=.1,post_reload_delay=0)
        c['post_fire_delays'][0]=0
        baseline=world_frame_native.observe(c);data,result=observe(c)
        self.assertGreater(result['damage'][0],0);self.assertEqual(result,baseline)
        self.assertEqual(data['attacks'],[])

    def test_reentrant_delivery_reserves_identity_before_child(self):
        original=battle.projectiles;entered=[]
        def deliver(world,manager,attacker,*args,**kwargs):
            if not entered:
                entered.append(True);manager._damage_handler(effect('injected-child'),attacker,world.last)
            return original(world,manager,attacker,*args,**kwargs)
        with patch.object(battle,'projectiles',deliver):data,_=observe(case())
        self.assertEqual([r['attack_id'] for r in data['attacks']],[1,2])
        self.assertEqual([r['name'] for r in data['attacks']],['typed','injected-child'])
        self.assertTrue(all(r['completed'] for r in data['attacks']))

    def test_failure_retains_incomplete_record_and_restores_native_hooks(self):
        before=(timeline.simulate,sim.simulate,timeline.HitEvent,timeline.BossScript,buff_manager.BuffManager.register_damage_handler)
        with battle.typed_battle(BINDINGS) as data:
            with patch.object(battle,'projectiles',side_effect=RuntimeError('delivery failed')):
                with self.assertRaisesRegex(RuntimeError,'delivery failed'):world_frame_native.observe(case())
        self.assertEqual(len(data['attacks']),1);self.assertFalse(data['attacks'][0]['completed'])
        after=(timeline.simulate,sim.simulate,timeline.HitEvent,timeline.BossScript,buff_manager.BuffManager.register_damage_handler)
        self.assertEqual(before,after)
        good,_=observe(case());self.assertTrue(good['attacks'][0]['completed'])

    def test_declared_capacity_and_specialized_formulas_are_rejected(self):
        for limit in (0,129,True):
            with self.subTest(limit=limit),self.assertRaises(ValueError):
                with battle.typed_battle(BINDINGS,max_attacks=limit):pass
        with self.assertRaisesRegex(ValueError,'capacity exceeded'):observe(case([effect(timing='event:target_spawn')],repeat=True),max_attacks=2)
        with self.assertRaisesRegex(ValueError,'plain projectile'):observe(case([dict(effect(),stat='projectile_explosion_damage')]))

    def test_canonical_cleared_node_has_no_invented_typed_clear_semantics(self):
        world=DestructibleWorld([dict(id='idle',until=dict(targets_cleared=True))],BINDINGS)
        with self.assertRaisesRegex(ValueError,'target-cleared'):DestructibleWorld.from_clock(world.clock,BINDINGS)

if __name__=='__main__':unittest.main()
