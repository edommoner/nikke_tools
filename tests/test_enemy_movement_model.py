"""Original duration carriers must affect real colliders, not authored hit lists."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from runner import sim
from enemy_movement_model import EnemyMovement,integrate,normalize
from portable_enemy_movement_cases import fixtures
from world_enemy_movement_native import observe
from portable_enemy_movement_contracts import verify


class MovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.native={}
        for case in cls.cases:
            n,_=observe(case);verify(case,n);cls.native[case['contract']['scenario']]=n

    def test_original_yuni_and_yan_duration_carriers_drive_actual_positions(self):
        for scenario,stat,definitions in [('disable','enemy_movement_disable',69),('force','force_move',71)]:
            n=self.native[scenario]
            self.assertEqual(n['original_input_identity']['definitions'],definitions)
            active=[s for f in n['enemy_movement']['frames'] for s in f['segments'] if any(e['stat']==stat for e in s['fields'])]
            self.assertTrue(active);self.assertTrue(n['logical_packets'])
            self.assertTrue(any(s['before']!=s['after'] for f in n['enemy_movement']['frames'] for s in f['segments']))

    def test_status_omission_changes_real_landing_and_damage_with_identical_original_inputs(self):
        case=self.cases[0]
        with patch.object(EnemyMovement,'fields',return_value=[]):free,_=observe(case)
        actual=self.native['disable']
        self.assertEqual(actual['original_input_identity'],free['original_input_identity'])
        self.assertTrue(actual['logical_packets']!=free['logical_packets'],'Original duration state must change actual packet landings')
        self.assertNotEqual(actual['battle']['add_total'],free['battle']['add_total'])

    def test_overlap_profiles_retain_both_original_effects_and_explicit_precedence(self):
        for key in ('overlap-disable','overlap-force'):
            data=self.native[key]['enemy_movement']
            overlap=[s for f in data['frames'] for s in f['segments'] if s['disabled'] and s['forced']]
            self.assertTrue(overlap)
            for s in overlap:
                self.assertEqual(s['after'],s['before'] if key=='overlap-disable' else [0.,0.])
        self.assertEqual(integrate([9.,3.],[1.,2.],[0.,0.],1.,True,True,'disable-before-force'),[9.,3.])
        self.assertEqual(integrate([9.,3.],[1.,2.],[0.,0.],1.,True,True,'force-before-disable'),[0.,0.])

    def test_rebirth_resets_position_on_actual_actor_generations(self):
        data=self.native['renewal']['enemy_movement']
        self.assertEqual(sorted(r['actor'][2] for r in data['generations']),[1,1,2,2,3,3])
        for born in data['generations']:
            self.assertEqual(born['position'],[-200.,0.])
            same=[r for r in data['frames'] if r['actor']==born['actor']]
            self.assertEqual(same[0]['position'],born['position'])

    def test_reject_implicit_policies_wrong_ownership_and_restore_original_aliases(self):
        good=self.cases[0]['enemy_movement'];before=(timeline.simulate,sim.simulate,timeline.BossScript)
        bad=[{},dict(good,precedence='auto'),dict(good,recipient_policy='assume-spatial'),dict(good,force_policy='game-default')]
        for spec in bad:
            with self.assertRaises(ValueError):normalize(spec)
        case=copy.deepcopy(self.cases[0]);case['enemy_movement']['actors'][0]['label']='__enemy__'
        with self.assertRaises(ValueError):observe(case)
        self.assertEqual(before,(timeline.simulate,sim.simulate,timeline.BossScript))

    def test_half_open_expiry_and_midframe_boundaries_preserve_original_duration_order(self):
        n=self.native['force'];segments=[s for f in n['enemy_movement']['frames'] for s in f['segments']]
        expiries={a['expires_at'] for q in segments if q['forced'] for a in q['fields'] if a['stat']=='force_move'}
        self.assertTrue(any(not s['forced'] and s['start'] in expiries for s in segments))
        for s in segments:
            for field in s['fields']:self.assertLess(s['start'],field['expires_at'])

    def test_numeric_overflow_and_invalid_states_fail_before_position_publication(self):
        with self.assertRaises(ValueError):integrate([1e308,0.],[1e308,0.],[0.,0.],2.,False,False,'disable-before-force')
        for dt in (-1.,float('nan'),True):
            with self.assertRaises(ValueError):integrate([0.,0.],[1.,1.],[0.,0.],dt,False,False,'disable-before-force')

    def test_real_world_clock_splits_expiry_and_respects_existing_generation_visibility(self):
        from calculator.boss_pattern import BossScript,validate
        from world_actor_specs import bindings
        enemy=copy.deepcopy(timeline.DEFAULT_ENEMY)
        patterns=[dict(id='wave',kind='summon',spec=dict(count=1,hp=1e30))]
        boss=BossScript(validate(patterns),enemy,lambda *_:True)
        binding=next(b for b in bindings([r.p for r in boss._runs]) if int(b.kind)==5)
        label=binding.label
        rule=dict(precedence='disable-before-force',force_policy='snap-to-declared-center',recipient_policy='canonical-all-in-range',actors=[dict(label=label,velocity=[2.,0.],force_center=[0.,0.])])
        model=EnemyMovement(rule);shape=dict(x=0.,y=0.,r=1.,w=0.,h=0.,rot=0.,z=1.)
        geometry=SimpleNamespace(spec=[dict(label=label,shape=shape)],boss=boss,bindings={label:binding});model.attach(geometry)
        carrier=SimpleNamespace(target_chars=[label],activated_at=0.,expires_at=.5,effect=dict(name='duration'),caster='source')
        manager=SimpleNamespace(_by_stat=lambda stat:[carrier] if stat=='enemy_movement_disable' else [],enemy_field_visible=lambda *a:True,
            _live=lambda ab,label,t:t<ab.expires_at)
        model.frame(manager,boss,0.,enemy);model.frame(manager,boss,1.,enemy)
        self.assertEqual(shape['x'],1.)
        self.assertEqual([(s['start'],s['end'],s['disabled']) for s in model.data['frames'][-1]['segments']],[(0.,.5,True),(.5,1.,False)])
        carrier.expires_at=10.;manager.enemy_field_visible=lambda *a:False
        model.frame(manager,boss,2.,enemy);self.assertEqual(shape['x'],3.)


if __name__=='__main__':unittest.main()
