"""Actual retirement/queue provenance and unchanged legacy admission."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from runner import sim
from enemy_ammo_self_destruct_model import SelfDestructEnemyAmmo
from enemy_ammo_model import Magazine
from impact_specs import ActorHandle,ActorKind
from world_actor_runtime import ActorRegistry
from portable_enemy_ammo_self_destruct_cases import fixtures
from portable_enemy_ammo_self_destruct_contracts import verify
from world_enemy_ammo_self_destruct_native import observe


class SelfDestructAmmoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.outputs={c['contract']['scenario']:observe(c)[0] for c in cls.cases}

    def test_original_full_roster_contracts(self):
        for case in self.cases:
            with self.subTest(case=case['name']):self.assertTrue(verify(case,self.outputs[case['contract']['scenario']])['verified'])

    def test_dead_queued_hit_requires_exact_object_generation_and_frame(self):
        actor=ActorHandle(ActorKind.ADD,0,1);registry=ActorRegistry();state=[1,False]
        label='__enemy__:self-ammo#1'
        registry.bind(ActorKind.ADD,label,lambda:(state[0],state[1],None),identity=0)
        hit=SimpleNamespace(source='self-ammo#1',pattern='self-ammo',index=0)
        for failure in ('none','clone','later','old-generation','valid'):
            runtime=SelfDestructEnemyAmmo(self.cases[0]['enemy_ammo']);runtime.registry=registry;runtime.refresh=lambda t:None
            mag=Magazine(label,actor,16,3,1.,True);runtime.history[actor]=mag
            runtime.pending[id(hit)]=(hit,actor);state[:]=[2 if failure=='old-generation' else 1,False]
            if failure!='none':runtime.retired_shots[id(hit)]=(copy.copy(hit) if failure=='clone' else hit,actor,1.)
            calls=[];runtime.attack(lambda *args:calls.append(args),hit,2. if failure=='later' else 1.)
            self.assertEqual(mag.ammo,2 if failure=='valid' else 3)
            self.assertEqual(len(calls),int(failure=='valid'))
            self.assertEqual(runtime.data['attempts'][-1]['status'],'fired' if failure=='valid' else 'stale' if failure=='old-generation' else 'dead')
            with self.assertRaisesRegex(ValueError,'original queued'):runtime.attack(lambda *a:None,hit,1.)

    def test_default_magazines_still_reject_self_destruct_and_restore_patches(self):
        from world_enemy_ammo_native import observe as legacy
        before=(timeline.BossScript,timeline.simulate,sim.simulate,timeline._register_instant_handlers)
        with self.assertRaisesRegex(ValueError,'Self-destruct launch timing'):legacy(self.cases[0])
        self.assertEqual(before,(timeline.BossScript,timeline.simulate,sim.simulate,timeline._register_instant_handlers))
        bad=copy.deepcopy(self.cases[0]);bad['enemy_ammo'][0]['label']='unknown'
        with self.assertRaisesRegex(ValueError,'real BODY/ADD'):observe(bad)
        self.assertEqual(before,(timeline.BossScript,timeline.simulate,sim.simulate,timeline._register_instant_handlers))

    def test_no_reload_after_retirement_and_no_invented_shots(self):
        final=self.outputs['reload-final']['enemy_ammo']
        self.assertTrue(any(a.get('retired_queue') and a['status']=='reloading' for a in final['attempts']))
        self.assertFalse(any(r['kind']=='complete' for r in final['reloads']))
        for scenario in ('hp-before-shot','time-close'):
            self.assertEqual(self.outputs[scenario]['enemy_ammo']['attempts'],[])
            self.assertEqual(self.outputs[scenario]['enemy_ammo']['retirements'],[])

    def test_contract_rejects_missing_hits_forged_generation_and_ammo(self):
        case=next(c for c in self.cases if c['contract']['scenario']=='coincident')
        for kind in ('hits','generation','ammo','retirement','completion'):
            bad=copy.deepcopy(self.outputs['coincident'])
            if kind=='hits':bad['battle']['squad_hits'].pop()
            elif kind=='generation':bad['enemy_ammo']['attempts'][0]['actor'][2]=99
            elif kind=='ammo':bad['enemy_ammo']['attempts'][0]['after']+=1
            elif kind=='retirement':bad['enemy_ammo']['retirements'][0]['queued_indices']=[]
            else:bad['enemy_ammo']['charges'][0]['completion']=[]
            with self.subTest(kind=kind),self.assertRaises((AssertionError,KeyError)):verify(case,bad)

    def test_cli_and_work_classification_preserve_gpu_boundary(self):
        from portable_reference import REFERENCES
        from portable_readiness_semantics import enemy_ammo_prerequisites
        self.assertEqual(REFERENCES['enemy-ammo-self-destruct-common'][0],'portable_enemy_ammo_self_destruct_cases')
        contract=enemy_ammo_prerequisites()['declared_enemy_ammo_self_destruct_contract']
        self.assertEqual((contract['cases'],contract['original_definitions']),(8,76))
        self.assertFalse(contract['gpu_wire_connected']);self.assertFalse(contract['default_path_installed'])

    def test_exact_extension_inverse_rejects_unknown_source_changes(self):
        import json
        from portable_enemy_ammo_self_destruct_source_contract import project_sources
        ledger=json.loads((ROOT/'tests/fixtures/portable-enemy-ammo-self-destruct-source-delta.json').read_text())
        old=project_sources(ROOT)
        for name,row in ledger['files'].items():self.assertEqual(old[name],row['before'])
        for name in [*ledger['files'],*ledger['added_sources']]:
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})


if __name__=='__main__':unittest.main()
