"""Real original enemy reduction, source-owned health and lifecycle boundaries."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from runner import sim
from calculator.boss_pattern import BossScript,validate
from calculator.sim_result import HitEvent
from enemy_healing_model import normalize,EnemyHealing,enemy_healing
from portable_enemy_healing_cases import fixtures
from portable_enemy_healing_contracts import verify
from world_enemy_healing_native import observe

class EnemyHealingModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.native={}
        for c in cls.cases:
            n,_=observe(c);verify(c,n);cls.native[c['contract']['scenario']]=n

    def test_original_levels_change_real_add_healing_and_preserve_all_definitions(self):
        for level in (1,10):
            n=self.native['level'+str(level)];rows=n['enemy_healing']['receipts']
            reduced=[r for r in rows if r['multiplier']<1]
            self.assertEqual(len(reduced),2);self.assertTrue(all(r['effective_gain']>0 and r['applied']<1000 for r in reduced))
            self.assertEqual(n['original_input_identity']['definitions'],69)
            self.assertTrue(n['original_input_identity']['effects_owners_weapons_chars_config_seed_verified'])
        a=min(r['multiplier'] for r in self.native['level10']['enemy_healing']['receipts'])
        b=min(r['multiplier'] for r in self.native['level1']['enemy_healing']['receipts'])
        self.assertLess(a,b)

    def test_maximum_health_clipping_preserves_hits_and_scored_damage(self):
        for r in self.native['capped']['enemy_healing']['receipts']:
            self.assertEqual(r['hp_after'],r['max_hp']);self.assertEqual(r['dealt_after'],0)
            self.assertEqual(r['hits_before'],r['hits_after']);self.assertEqual(r['scored_before'],r['scored_after'])

    def test_dead_add_cannot_be_healed_or_counted_for_damage_again(self):
        n=self.native['dead'];self.assertEqual(n['battle']['add_total'],2)
        self.assertTrue(all(r['status']=='dead-or-inactive' for r in n['enemy_healing']['receipts']))

    def test_frozen_packet_to_dead_same_generation_still_owns_overkill(self):
        from calculator.sim_result import HitEvent
        enemy=copy.deepcopy(timeline.DEFAULT_ENEMY)
        boss=BossScript(validate([dict(id='wave',kind='summon',spec=dict(count=1,hp=1.))]),enemy,lambda *_:True)
        boss.begin_frame(0.,enemy);add=boss._runs[0].adds[0]
        hit=lambda amount:HitEvent(t=0.,caster='probe',damage=amount,is_crit=False,hit_tag='normal')
        self.assertTrue(boss.hit_add(hit(10),add.id,0.))
        self.assertFalse(boss.hit_add(hit(20),add.id,0.))
        self.assertFalse(add.alive);self.assertEqual(add.dealt,1.)
        self.assertEqual(boss.add_dealt,{'probe':1.})
        self.assertEqual(boss.add_overkill,29.)
        self.assertEqual(add.hits,0)

    def test_unexpired_old_generation_reduction_is_excluded_on_rebirth(self):
        rows=[r for r in self.native['renewal']['enemy_healing']['receipts'] if r['excluded_stale_fields']]
        self.assertEqual(len(rows),2)
        for r in rows:
            self.assertEqual(r['actor'][2],2);self.assertEqual(r['multiplier'],1)
            self.assertTrue(any(f['actor'][2]==1 and f['expires_at']>r['time'] for f in r['excluded_stale_fields']))

    def test_fractional_health_credit_is_retained_before_public_rounding(self):
        n=self.native['fractional-death'];data=n['enemy_healing']
        self.assertTrue(any(not float(v).is_integer() for v in data['final_scored_damage'].values()))
        self.assertFalse(float(data['final_overkill']).is_integer())
        expected={name:round(data['final_scored_damage'].get(name,0.)) for name in n['battle']['add_char_total']}
        self.assertEqual(n['battle']['add_char_total'],expected)
        self.assertEqual(n['battle']['add_total'],sum(expected.values()))

    def test_strict_literals_and_binding_errors_restore_aliases(self):
        good=self.cases[0]['enemy_healing'];before=(timeline.simulate,sim.simulate,timeline.BossScript)
        bad=[[],good*9,[dict(good[0],amount=True)],[dict(good[0],amount=float('nan'))],[dict(good[0],amount=-1)],[dict(good[0],targets=['x','x'])],[dict(good[0],other=1)]]
        for spec in bad:
            with self.subTest(spec=spec),self.assertRaises(ValueError):normalize(spec)
        for change in (dict(node='absent'),dict(node='healing-wave'),dict(targets=['__enemy__'])):
            c=copy.deepcopy(self.cases[0]);c['enemy_healing'][0].update(change)
            with self.assertRaises(ValueError):observe(c)
            self.assertEqual(before,(timeline.simulate,sim.simulate,timeline.BossScript))

    def test_corrupt_actual_hp_or_multiplier_receipt_is_rejected(self):
        for field in ('multiplier','hp_after','dealt_after'):
            bad=copy.deepcopy(self.native['level10']);bad['enemy_healing']['receipts'][2][field]+=1
            with self.subTest(field=field),self.assertRaises(AssertionError):verify(self.cases[0],bad)

    def test_real_source_healing_changes_native_death_and_keeps_cumulative_score(self):
        class Manager:
            def _live(self,*args):return False
            def enemy_field_visible(self,*args):return True
            def heal_received_mult(self,*args):return 1.
        def run(enabled):
            enemy=copy.deepcopy(timeline.DEFAULT_ENEMY)
            boss=BossScript(validate([dict(id='wave',kind='summon',spec=dict(count=1,hp=100)),dict(id='heal',kind='idle',delay=1)]),enemy,lambda *_:True)
            manager=Manager();model=EnemyHealing([dict(node='heal',targets=['__enemy__:wave#1'],amount=50)])
            if enabled:model.frame(manager,boss,0.,enemy)
            else:boss.begin_frame(0.,enemy)
            add=boss._runs[0].adds[0]
            def hit(amount,t):boss.hit_add(HitEvent(t=t,caster='probe',damage=amount,is_crit=False,hit_tag='normal'),add.id,t)
            hit(80,.5);hits=add.hits
            if enabled:model.frame(manager,boss,1.,enemy)
            else:boss.begin_frame(1.,enemy)
            self.assertEqual(add.hits,hits);self.assertEqual(boss.add_dealt['probe'],80)
            hit(50,1.1);return add.alive,boss.add_dealt['probe']
        self.assertEqual(run(False),(False,100.))
        self.assertEqual(run(True),(True,130.))

    def test_double_initial_frame_does_not_execute_one_source_twice(self):
        c=copy.deepcopy(self.cases[0]);c['body']['duration']=2.;c['patterns'][1]['delay']=0.
        c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'])
        n,_=observe(c);self.assertEqual(len(n['enemy_healing']['sources']),1)
        self.assertEqual(len(n['enemy_healing']['receipts']),2)

    def test_reference_contract_never_becomes_gpu_admission(self):
        import nikke_gpu
        from portable_reference import REFERENCES
        self.assertIn('enemy-healing-common',REFERENCES);self.assertNotIn('enemy-healing-common',nikke_gpu.SUITES)
        c=self.cases[0];result=verify(c,self.native['level10'])
        self.assertFalse(result['gpu_supported']);self.assertFalse(result['gpu_wire_connected'])
        self.assertTrue(result['reference_model_gap'])
        from portable_readiness_semantics import reference_readiness
        issue=dict(phase='effect',kind='buff',stat='heal_received_pct',target='all_enemies')
        r=reference_readiness(issue);contract=r['declared_enemy_healing_contract']
        self.assertTrue(contract['actual_finite_ADD_health']);self.assertTrue(contract['cpu_reference_verified'])
        self.assertFalse(contract['gpu_wire_connected']);self.assertFalse(r['gpu_supported'])
        self.assertEqual(r['lane'],'reference_model_gap')

    def test_hit_count_health_and_combined_actor_overflow_are_rejected(self):
        for spec in (dict(count=1,hit_hp=3),dict(count=1,hp=100,hit_hp=3,hit_hp_after=1),dict(count=128,hp=100)):
            enemy=copy.deepcopy(timeline.DEFAULT_ENEMY)
            boss=BossScript(validate([dict(id='wave',kind='summon',spec=spec),dict(id='heal',kind='idle')]),enemy,lambda *_:True)
            model=EnemyHealing([dict(node='heal',targets=['__enemy__:wave#1'],amount=1)])
            with self.subTest(spec=spec),self.assertRaises(ValueError):model.frame(SimpleNamespace(),boss,0.,enemy)

if __name__=='__main__':unittest.main()
