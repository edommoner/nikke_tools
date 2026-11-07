"""S22 split invariance and ranking/depth contracts; no reference execution."""
import importlib.util
import itertools
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]/'research/team-search'
sys.path.insert(0, str(HERE))
import truth_s22 as truth
import build_s22
import l2_score_s22
import l2_score_s20
import l2_fast


class DenseTruthTests(unittest.TestCase):
    def test_subset_hash_ignores_order_but_not_members(self):
        self.assertEqual(truth.subset_key(['가','a','b','c','d']),
                         truth.subset_key(['d','c','b','a','가']))
        self.assertNotEqual(truth.subset_key(['가','a','b','c','d']),
                            truth.subset_key(['나','a','b','c','d']))

    def test_confirmation_depth_counts_worst_true_winner(self):
        rows = [dict(id=i,total=100-i) for i in range(100)]
        pred = [float(100-i) for i in range(100)]
        pred[0],pred[49] = pred[49],pred[0]
        result = truth.metrics(rows,pred)
        self.assertEqual(result['confirmation_depth'], {'1':50,'10':50})
        self.assertEqual(result['recall']['1']['30'], 0)
        self.assertEqual(result['recall']['10']['30'], .9)
        self.assertEqual(result['recall']['10']['100'], 1)

    def test_tied_ranks_have_stable_id_confirmation(self):
        rows = [dict(id=i,total=10) for i in range(12)]
        result = truth.metrics(rows,[2]*12)
        self.assertIsNone(result['spearman'])
        self.assertIsNone(result['kendall_tau_b'])
        self.assertEqual(result['confirmation_depth'], {'1':1,'10':10})


class OccupancyTests(unittest.TestCase):
    def profile(self,mask):
        chars={}
        for i,n in enumerate('abcde'):
            group=dict(kind='normal',phase=1,unit=1.,own={'atk_pct':100.},flags={'is_normal_atk':True},
                       weapon={'damage_coeff':1.},base_atk=100.,enemy_def=0.)
            buff=dict(phase=1,effect={'target':'self','trigger':{'timing':['burst_cast']}},
                      amount={'atk_pct':100.},recipients=[n])
            chars[n]=dict(metadata=dict(burst_stage=['1','2','3','3','1'][i],burst_cooldown=40.,
                                       max_ammo=10,fire_rate=1.,reload_time=1.),
                groups=[group],buffs=[buff],dependencies=[],effects=[],base_stats={'atk':100.},
                reference=dict(casts=5,phase_seconds=[130.,50.]))
        body=dict(profile=dict(chars={n:dict(skill_levels={'1':10,'2':10,'3':10}) for n in chars}))
        return build_s22.build(dict(settings={'duration':180.},s20=dict(version=2,switches=2),characters=chars),mask,body)

    def test_competing_caster_own_occupancy_follows_casts(self):
        p=self.profile(16);squad=list('abcde')
        casts,fb,_=l2_score_s20.cycle(squad,p['characters'],180.)
        result=l2_score_s22.Score(p).member_scores(squad)
        for n in squad:
            expected=(100.+100.*(casts[n]/5.*50./fb))*(fb/50.)
            self.assertAlmostEqual(result[n],expected)
        self.assertLess(result['d'],result['c'])

    def test_own_structural_gate_does_not_remove_unobserved_supply(self):
        p=self.profile(32)
        p['characters']['a']['buffs'][0]['condition_s20']=1
        corrected=l2_score_s22.Score(p).member_scores(list('abcde'))['a']
        p['characters']['a']['buffs'][0]['recipients']=[]
        unchanged=l2_score_s22.Score(p).member_scores(list('abcde'))['a']
        self.assertAlmostEqual(unchanged,2*corrected)

    def test_state_family_requires_finite_unambiguous_burst_marker(self):
        marker=dict(name='window',target='self',trigger={'timing':['burst_cast']},duration=10.,max_stack=1)
        effect=dict(type='damage',stat='core_damage',trigger={'condition':['self_state:window']})
        c=dict(effects=[marker,effect])
        self.assertTrue(build_s22.burst_state_family(c,'core_damage'))
        marker['duration']=-1
        self.assertFalse(build_s22.burst_state_family(c,'core_damage'))

    def test_plain_effect_bound_caps_own_supply(self):
        p=self.profile(144)
        p['characters']['c']['buffs'][0]['caps_s22']={'atk_pct':20.}
        result=l2_score_s22.Score(p).member_scores(list('abcde'))
        self.assertAlmostEqual(result['c'],120.)

    @unittest.skipUnless(shutil.which('clang++') and shutil.which('node'),'Existing toolchains required')
    def test_v3_switches_native_cli_wasm_identity(self):
        spec=importlib.util.spec_from_file_location('s22_verify',HERE/'l2_fast/verify.py')
        verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
        native=l2_fast.build();wasm=l2_fast.build(True)
        with tempfile.TemporaryDirectory() as folder:
            for mask in range(0,256,16):
                p=self.profile(mask)
                p['characters']['a']['buffs'][0]['condition_s20']=1
                p['characters']['c']['groups'][0]['cast_scaled_s22']=True
                p['characters']['e']['reference']['phase_seconds']=[180.,0.]
                p['characters']['c']['buffs'][0]['caps_s22']={'atk_pct':20.}
                squads=list(itertools.islice(itertools.permutations('abcde'),12))
                result=verify.compare(p,squads,pathlib.Path(folder),native,wasm,str(mask))
                self.assertEqual(result['differences'],0)


if __name__ == '__main__':
    unittest.main()
