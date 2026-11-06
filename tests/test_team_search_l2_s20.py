"""Version 2 cycle/recipient arithmetic and raw-double cross-engine contract."""
import copy
import importlib.util
import itertools
import pathlib
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parents[1]/'research/team-search'
sys.path.insert(0, str(HERE))
import l2_fast
import l2_score_s20 as model
import l2_score
spec = importlib.util.spec_from_file_location('s20_verify', HERE/'l2_fast/verify.py')
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class S20(unittest.TestCase):
    def test_uncovered_hit_has_no_scalar_link(self):
        from observe_s20 import Observer
        observer=Observer('x',1.)
        hit=SimpleNamespace(caster='x',damage=1,hit_tag='dealt_fixed_damage')
        observer.hits=[hit]
        observer.events={id(hit):(hit,None)}
        payload=dict(members=[dict(name='x',damage=1)],total_damage=1,
                     burst_timeline=[],base_stats={'x':{'atk':1.}})
        result=observer.compact(payload)
        self.assertEqual(result['uncovered'],{'dealt_fixed_damage':1})
        self.assertEqual(result['groups'],[])

    def profile(self):
        p = verify.synthetic()
        p['s20'] = dict(version=2, switches=15)
        for i, c in enumerate(p['characters'].values()):
            c['base_stats'].update(hp=1000.+i, **{'def':10.+i})
            c['rank_own_s20'] = dict(atk_pct=float(i), atk_flat=2.*i)
            c['metadata'].update(max_ammo=6, clip_count=3, reload_time=2., fire_rate=2.,
                                 is_charge=bool(i%2), input_type='DOWN_Charge')
            c['mechanics_s20'] = [[0, 2, 0, 1, 2.34, 1, 1], [2, 1, 0, 1, 1., 0, 0]] if i == 1 else []
            for g in c['groups']:
                g['own'].update(max_ammo_pct=129.64, reload_speed_pct=17.,
                                attack_speed_pct=20., charge_speed_pct=33.)
                g['action_rate_s20'] = model.action_rate(c, g['own'])
                g['context_unit_s20'] = g['unit']*.8
                g['flags']['is_burst_damage'] = False
                g['cast_scaled_s20'] = bool(i%2)
                g['action_eligible_s20'] = bool(i%3)
            c['buffs'].append(dict(phase=1, condition_s20=1 if i%2 else 2, effect={'target':['allies_top_atk:2','allies_top_atk_excl:1']}, amount={'atk_pct':13.1}))
        return p

    def test_cycle_reentry_and_cdr(self):
        p = self.profile()
        names = list(p['characters'])[1:6]
        casts, fb, cycles = model.cycle(names, p['characters'], 180.)
        self.assertGreater(cycles, 0)
        self.assertGreater(sum(casts.values()), 3*cycles)
        self.assertLessEqual(fb, 180.)
        for c in p['characters'].values():
            c['mechanics_s20'] = []
        self.assertEqual(model.cycle(names, p['characters'],180.), l2_score.cycle(names,p['characters'],180.))

    def test_final_atk_stable_selection(self):
        p = self.profile()
        names = list(p['characters'])[1:6]
        stats = {n:(10.,100.,1000.,20.) for n in names}
        stats[names[3]] = (30.,100.,1000.,20.)
        self.assertEqual(model.recipients('allies_top_atk:2',names[0],names,p['characters'],stats), {names[3],names[0]})
        self.assertEqual(model.recipients('allies_top_atk_excl:2',names[0],names,p['characters'],stats),{names[3],names[1]})

    def test_max_trigger_limits_cooldown_reduction(self):
        p=self.profile();names=list(p['characters'])[1:6]
        for c in p['characters'].values():
            c['mechanics_s20']=[];c['metadata']['burst_cooldown']=40.
        rule=[0,2,0,1,40.,1,1]
        p['characters'][names[0]]['mechanics_s20']=[rule]
        limited=model.cycle(names,p['characters'],180.)[2]
        rule[-1]=0
        unlimited=model.cycle(names,p['characters'],180.)[2]
        self.assertLess(limited,unlimited)

    @unittest.skipUnless(shutil.which('clang++') and shutil.which('node'), 'Existing compilers required')
    def test_all_switches_bit_identity(self):
        try:
            native = l2_fast.build()
            wasm = l2_fast.build(True)
        except FileNotFoundError as e:
            self.skipTest(str(e))
        p = self.profile()
        squads = list(itertools.islice(itertools.permutations(p['characters'],5),48))
        with tempfile.TemporaryDirectory() as d:
            for mask in range(16):
                p['s20']['switches'] = mask
                result = verify.compare(p, squads, pathlib.Path(d), native, wasm, str(mask))
                self.assertEqual(result['differences'],0)


if __name__ == '__main__':
    unittest.main()
