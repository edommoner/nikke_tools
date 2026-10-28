"""Original percentage arithmetic, real incoming HP and generation boundaries."""
import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from runner import sim
from enemy_ammo_model import EnemyAmmo,Magazine,normalize,rebind_percentage_operator,source_label
from impact_specs import ActorHandle,ActorKind
from world_actor_runtime import ActorRegistry
from portable_enemy_ammo_cases import fixtures
from portable_enemy_ammo_contracts import verify
from world_enemy_ammo_native import observe


class EnemyAmmoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.native={};cls.handlers=[]
        register=timeline.BuffManager.register_instant_handler
        def capture(manager,stat,fn):
            if stat=='ammo_charge_pct' and fn.__name__=='handle_ammo_charge_pct':cls.handlers.append(fn)
            return register(manager,stat,fn)
        with patch.object(timeline.BuffManager,'register_instant_handler',capture):
            for c in cls.cases:cls.native[c['contract']['scenario']]=observe(c)[0]

    def test_original_rosters_and_live_shots(self):
        for c in self.cases:
            with self.subTest(case=c['name']):self.assertTrue(verify(c,self.native[c['contract']['scenario']])['verified'])

    def test_source_display_name_maps_to_configured_actor_not_body(self):
        self.assertEqual(source_label(SimpleNamespace(source='ammo-wave#1')),'__enemy__:ammo-wave#1')
        self.assertEqual(source_label(SimpleNamespace(source='')),'__enemy__')

    def test_native_operator_identity_ties_clamps_and_completion(self):
        original=self.handlers[0]
        manager=dict(zip(original.__code__.co_freevars,[c.cell_contents for c in original.__closure__]))['bm']
        actor=ActorHandle(ActorKind.ADD,0,1)
        for value,expected in [(5,3),(15,5),(25,5),(-5,3),(-15,1),(-25,1),(1000,10),(-1000,0)]:
            mag=Magazine('enemy',actor,10,3,1.,True)
            operator=rebind_percentage_operator(original,{'enemy':mag},lambda eff,caster:['enemy'])
            self.assertIs(operator.__code__,original.__code__)
            with patch.object(manager,'notify') as notify:operator({'name':'original-completion'},'벨벳',.5,value)
            self.assertEqual(mag.ammo,expected)
            notify.assert_called_once_with('event:original-completion',.5,'벨벳')
        for name,count in [('',0),('empty',1)]:
            operator=rebind_percentage_operator(original,{},lambda eff,caster:[])
            with patch.object(manager,'notify') as notify:operator({'name':name},'벨벳',1.,-100)
            self.assertEqual(notify.call_count,count)

    def test_original_reload_cancel_control_has_no_full_reload_event(self):
        original=self.handlers[0]
        manager=dict(zip(original.__code__.co_freevars,[c.cell_contents for c in original.__closure__]))['bm']
        for enabled in (True,False):
            mag=Magazine('enemy',ActorHandle(ActorKind.ADD,0,1),10,0,1.,enabled,reloading_until=4.)
            operator=rebind_percentage_operator(original,{'enemy':mag},lambda eff,caster:['enemy'])
            with patch.object(manager,'notify') as notify:operator({'name':'charge'},'벨벳',2.,100)
            self.assertEqual(mag.ammo,10)
            self.assertEqual(mag.reloading_until,-1. if enabled else 4.)
            notify.assert_called_once_with('event:charge',2.,'벨벳')

    def test_stale_dead_or_missing_queued_identity_cannot_spend_new_magazine(self):
        runtime=EnemyAmmo(self.cases[0]['enemy_ammo']);registry=ActorRegistry();state=[1,True]
        registry.bind(ActorKind.ADD,'__enemy__:ammo-wave#1',lambda:(state[0],state[1],None),identity=0)
        runtime.registry=registry;runtime.refresh=lambda t:None
        handle=ActorHandle(ActorKind.ADD,0,1);hit=SimpleNamespace(source='ammo-wave#1',pattern='ammo-wave',index=0)
        current=Magazine('__enemy__:ammo-wave#1',ActorHandle(ActorKind.ADD,0,2),16,16,1.,True)
        runtime.current[current.name]=current;calls=[]
        for generation,alive,status in [(2,True,'stale'),(1,False,'dead')]:
            state[:]=[generation,alive];runtime.pending[id(hit)]=(hit,handle)
            runtime.attack(lambda *args:calls.append(args),hit,1.)
            self.assertEqual(runtime.data['attempts'][-1]['status'],status)
        self.assertEqual(current.ammo,16);self.assertEqual(calls,[])
        with self.assertRaisesRegex(ValueError,'original queued'):runtime.attack(lambda *args:None,hit,1.)
        runtime.pending[id(hit)]=(hit,ActorHandle(ActorKind.ADD,99,1))
        with self.assertRaisesRegex(ValueError,'Unknown world actor handle'):runtime.attack(lambda *args:None,hit,1.)

    def test_bad_literals_binding_and_failure_cleanup(self):
        good=self.cases[0]['enemy_ammo'];row=good[0]
        for bad in ([],[row,row],[dict(row,capacity=True)],[dict(row,initial=17)],[dict(row,reload_seconds=float('nan'))],[dict(row,reload_seconds=0)],[dict(row,cancel_on_full=1)],[dict(row,extra=1)]):
            with self.subTest(spec=bad),self.assertRaises(ValueError):normalize(bad)
        before=(timeline.simulate,sim.simulate,timeline._register_instant_handlers,timeline.BossScript)
        case=copy.deepcopy(self.cases[0]);case['enemy_ammo'][0]['label']='absent'
        with self.assertRaisesRegex(ValueError,'real BODY/ADD'):observe(case)
        self.assertEqual(before,(timeline.simulate,sim.simulate,timeline._register_instant_handlers,timeline.BossScript))

    def test_contract_rejects_corrupt_actual_damage_completion_and_generation(self):
        case=self.cases[0]
        for mutation in ('damage','completion','generation','rounding'):
            bad=copy.deepcopy(self.native['level10'])
            if mutation=='damage':bad['battle']['squad_hits'].pop()
            elif mutation=='completion':bad['enemy_ammo']['charges'][0]['completion'][0]['remaining'].clear()
            elif mutation=='generation':bad['enemy_ammo']['attempts'][0]['actor'][2]=99
            else:bad['enemy_ammo']['charges'][0]['targets'][0]['change']=0
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):verify(case,bad)

    def test_common_cli_registration_keeps_gpu_admission_separate(self):
        from portable_reference import REFERENCES
        self.assertEqual(REFERENCES['enemy-ammo-common'],('portable_enemy_ammo_cases','world_enemy_ammo_native','portable_enemy_ammo_contracts'))


if __name__=='__main__':unittest.main()
