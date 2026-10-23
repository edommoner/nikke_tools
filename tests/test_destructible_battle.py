"""Actual native battle-clock contracts before the shared GPU battle hookup."""
import copy,sys,unittest,importlib.util,json,array,hashlib
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

    def test_shared_battle_table_packs_without_running_native(self):
        s=importlib.util.spec_from_file_location('typed_battle_test',ROOT/'research/verify-destructible-battle-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        with patch.object(a,'observe',side_effect=AssertionError('No CPU event list may enter GPU input')):rows,data=a.prepare()
        self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(25,14))
        self.assertEqual(len(data),4+25*109536*4)
        for _,words,domain in rows:
            if domain is None:continue
            self.assertFalse(any(words[104400:104400+2320]))
            n=a.native_reference(domain);self.assertTrue(n['typed']['finished'])
            if domain[0]['name'].endswith('/three-real-generations'):
                self.assertEqual([r['receipts'][0]['handle'][2] for r in n['typed']['attacks']],[1,2,3])
            if domain[0]['name'].endswith('/empty-retains-budget'):self.assertEqual(len(n['typed']['attacks']),1)

    def test_battle_source_inverse_rejects_unreviewed_changes(self):
        from portable_destructible_battle_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-destructible-battle-source-delta.json').read_text())
        project_sources(ROOT)
        for name,row in data['sources'].items():
            with self.subTest(source=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})

    def test_full_battle_uses_the_complete_current_shared_executor(self):
        from portable_backend import source_hashes
        ordinary=set(source_hashes('gpu/world_projectile_chain_entry.slang'))
        typed=set(source_hashes('gpu/destructible_battle_entry.slang'))
        self.assertLessEqual(ordinary,typed)

    def test_actual_metal_battle_blocks_reject_state_and_receipt_corruption(self):
        from portable_destructible_coexist_source_contract import verify_retained_sources
        s=importlib.util.spec_from_file_location('typed_battle_saved',ROOT/'research/verify-destructible-battle-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-battle-raw.json').read_text())
        verify_retained_sources(ROOT,'gpu/destructible_battle_entry.slang',fixture['source_sha256'])
        rows,_=a.prepare();by_name={n:(w,c) for n,w,c in rows}
        for record in fixture['records']:
            block=array.array('I',[0])*fixture['output_words']
            for i,v in record['nonzero']:block[i]=v
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            words,domain=by_name[record['name']]
            self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            a.compare(block,domain)
            for offset in (0,786433,789251,787458,790000,790006,790010,790019,790020):
                changed=array.array('I',block);changed[offset]^=2
                with self.subTest(name=record['name'],offset=offset),self.assertRaises((AssertionError,ValueError)):a.compare(changed,domain)

    def test_ordinary_clear_and_typed_lifetimes_have_distinct_owners(self):
        s=importlib.util.spec_from_file_location('typed_coexist_native',ROOT/'research/verify-destructible-battle-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        rows,_=a.prepare();answers={name.split('/')[-1]:a.native_reference(c) for name,_,c in rows if c is not None and c[0]['observe_actor_pools']}
        first=answers['ordinary-part-clear-opens-typed'];cleared=next(r for r in first['battle']['boss_log'] if r['outcome']=='cleared')
        self.assertGreater(cleared['time'],0);self.assertEqual(len(first['typed']['attacks']),2)
        self.assertTrue(all(r['time']>cleared['time'] for r in first['typed']['attacks']))
        repeat=answers['ordinary-clear-and-typed-repeat'];self.assertEqual(len([r for r in repeat['battle']['boss_log'] if r['outcome']=='cleared']),3)
        self.assertEqual([r['receipts'][0]['handle'][2] for r in repeat['typed']['attacks']],[1,2,3])
        separate=answers['typed-death-does-not-clear-ordinary'];self.assertTrue(separate['typed']['attacks'][0]['receipts'][0]['broken'])
        self.assertFalse(any(r['outcome']=='cleared' for r in separate['battle']['boss_log']))
        high=answers['separate-128-typed-and-127-ordinary'];self.assertEqual(len(high['typed']['attacks'][0]['receipts']),128)

    def test_coexistence_source_delta_is_exact(self):
        from portable_destructible_coexist_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-destructible-coexist-source-delta.json').read_text());project_sources(ROOT)
        for name,row in data['sources'].items():
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})

    def test_real_metal_coexistence_blocks_reject_pool_aliasing(self):
        from portable_backend import source_hashes
        from portable_specs import LIMITS as L
        s=importlib.util.spec_from_file_location('coexist_saved',ROOT/'research/verify-destructible-battle-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-coexist-raw.json').read_text())
        self.assertEqual(fixture['source_sha256'],source_hashes('gpu/destructible_battle_entry.slang'))
        rows,_=a.prepare();by_name={n:(w,c) for n,w,c in rows}
        for record in fixture['records']:
            block=array.array('I',[0])*fixture['output_words']
            for i,v in record['nonzero']:block[i]=v
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            words,domain=by_name[record['name']];self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256']);a.compare(block,domain)
            offsets=(L['WORLD_ACTOR_POOL_STATE_BASE']+16,L['WORLD_ACTOR_POOL_STATE_BASE']+20,L['WORLD_FRAME_OUTPUT_BASE']+16+4,787458,787460,790019)
            for offset in offsets:
                changed=array.array('I',block);changed[offset]^=1
                with self.subTest(name=record['name'],offset=offset),self.assertRaises((AssertionError,ValueError)):a.compare(changed,domain)

if __name__=='__main__':unittest.main()
