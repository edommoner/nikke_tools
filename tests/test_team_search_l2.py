"""Profile arithmetic fixtures: source transfers, dependent damage and selection."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('s18_l2',ROOT/'research/team-search/l2_score.py')
l2=importlib.util.module_from_spec(sp);sp.loader.exec_module(l2)


def profile():
    chars={}
    for n,stage in zip('abcde',('1','2','3','3','3')):
        g=dict(kind='normal',phase=False,hits=1,unit=1.,own={'crit_rate':0.,'crit_rate_skill':0.},
               flags={'is_normal_atk':True,'coeff':1.},weapon={'damage_coeff':1.},base_atk=100.,enemy_def=0.)
        chars[n]=dict(groups=[g],buffs=[],dependencies=[],flags=[],base_stats={'atk':100.},
                      metadata={'burst_stage':stage,'burst_cooldown':40.,'weapon_type':'AR','class':'x'},
                      reference={'casts':1,'cycles':1,'phase_seconds':[1.,0.]})
    return dict(settings={'duration':1.},characters=chars)


class ArithmeticTests(unittest.TestCase):
    def test_source_atk_transfer_and_self_not_doubled(self):
        p=profile();c=p['characters'];c['a']['base_stats']['atk']=200.
        c['a']['buffs']=[dict(effect={'target':'all_allies','trigger':{}},phase=False,
                              amount={'atk_flat':999.},caster_atk_coefficient=.5)]
        values=l2.Score(p).member_scores(list('abcde'))
        self.assertEqual(values['a'],100.)
        self.assertEqual(values['b'],200.)
        self.assertEqual(sum(values.values()),900.)

    def test_measured_self_bucket_plus_foreign_delta(self):
        p=profile();c=p['characters'];c['a']['groups'][0]['self_buckets']=[1.,250.,1.,1.,1.,1.,1.]
        self.assertEqual(l2.Score(p)(list('abcde')),650.)
        c['b']['buffs']=[dict(effect={'target':'allies:1','trigger':{}},phase=False,amount={'atk_flat':100.})]
        self.assertEqual(l2.Score(p)(list('abcde')),750.)

    def test_dependencies_scale_source_once(self):
        p=profile();p['characters']['a']['dependencies']=[{'kind':'dealt_fixed_damage','scope':'self','ratio':.5}]
        self.assertEqual(l2.Score(p)(list('abcde')),550.)
        p['characters']['a']['dependencies']=[{'kind':'accum_split_damage','scope':'team','ratio':.1}]
        self.assertEqual(l2.Score(p)(list('abcde')),550.)

    def test_static_selection_and_dynamic_flag(self):
        c=profile()['characters'];s=list('abcde')
        self.assertEqual(l2.recipients('allies_adjacent:1','c',s,c),{'b','c'})
        self.assertEqual(l2.recipients('allies_right:2','c',s,c),{'d','e'})
        self.assertEqual(l2.recipients('allies_class:x:2','c',s,c),{'a','b'})
        self.assertEqual(l2.recipients('allies_burst3','a',s,c),{'c','d','e'})
        self.assertFalse(l2.target_supported('allies_top_atk:2'))
        self.assertEqual(l2.recipients('allies_top_atk:2','c',s,c),set())

    def test_cycle_ordered_ready_and_missing_stage(self):
        c=profile()['characters'];casts,fb,cycles=l2.cycle(list('abcde'),c,90.)
        self.assertGreater(casts['c'],casts['e'])
        self.assertGreater(fb,0);self.assertGreater(cycles,0)
        c['b']['metadata']['burst_stage']='3'
        self.assertEqual(l2.cycle(list('abcde'),c,90.)[1:],(0.,0))

    def test_bucket_arithmetic_matches_reference(self):
        # Isolate reference module installation from unittest's global imports.
        code="""import sys,random,json
sys.path[:0]=['app','research/team-search']
import engine_worker,l2_score
from calculator.damage import default_hit_type
from profile_s18 import factors
rng=random.Random(18)
for i in range(30):
 h=default_hit_type(is_normal_atk=bool(i%2),is_full_burst=bool(i%3),is_full_charge=bool(i%4),is_burst_damage=bool(i%5),is_split=True,core_prob=.4)
 b={k:rng.uniform(0,20) for k in ('atk_pct','atk_flat','crit_dmg','crit_dmg_skill','charge_dmg_pct','received_dmg','normal_atk_dmg_pct','split_dmg_pct','burst_dmg_pct')};b.update(crit_rate=.3,crit_rate_skill=.2,is_element_match=True)
 g=dict(flags=h,weapon=dict(damage_coeff=20,full_charge_mult=250,core_dmg_mult=200),base_atk=50000,enemy_def=31784)
 assert l2_score.buckets(g,b)==factors(g['base_atk'],b,g['weapon'],h,g['enemy_def'])
"""
        subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,text=True,capture_output=True,check=True)

    def test_tiny_profile_builder_preserves_payload_and_reconciles(self):
        code="""import sys,json
sys.path[:0]=['app','research/team-search'];import engine_worker as e
x=e.detail_demo();print(json.dumps(dict(profile=x['profile'],squad=x['squad'],duration=4,level=400,compute_backend='cpu')))
"""
        body=json.loads(subprocess.check_output([sys.executable,'-B','-c',code],cwd=ROOT,text=True))
        results=[]
        for logged in (False,True):
            r=subprocess.run([sys.executable,'-B',str(ROOT/'research/team-search/profile_s18.py')],cwd=ROOT,
                input=json.dumps(dict(body=body,target=body['squad'][0],logged=logged)),text=True,capture_output=True,check=True)
            results.append(json.loads(r.stdout))
        self.assertEqual(results[0]['payload'],results[1]['payload'])
        p=results[1]['profile'];self.assertGreater(p['own_hits'],0)
        self.assertLess(max(p['reconciliation']),1e-10)
        self.assertTrue(p['buffs']);self.assertGreater(p['observed_queries'],0)
        self.assertEqual(sum(p['member_damage'].values()),results[1]['payload']['total_damage'])
        # Exercise compact artifact assembly as well as observation. Leave the
        # tiny owned fixture intact (S18's no-deletion constraint).
        fixture=Path(tempfile.mkdtemp(prefix='s18-profile-builder-'))
        (fixture/'runs').mkdir()
        row=dict(id=0,target=body['squad'][0],members=body['squad'])
        (fixture/'selection.json').write_text(json.dumps(dict(selected=[row])))
        (fixture/'body.json').write_text(json.dumps(body))
        evidence=dict(selection=row,non_interference=True,payload_digest=results[1]['payload_digest'],
                      baseline_digest=results[0]['payload_digest'],profile=p)
        (fixture/'runs/000.json').write_text(json.dumps(evidence))
        subprocess.run([sys.executable,'-B',str(ROOT/'research/team-search/measure_s18.py'),
                        'build','--out',str(fixture)],cwd=ROOT,text=True,capture_output=True,check=True)
        built=json.loads((fixture/'profiles.json').read_text())
        self.assertEqual(list(built['characters']),[body['squad'][0]])
        c=built['characters'][body['squad'][0]]
        self.assertEqual(sum(g['hits'] for g in c['groups']),p['own_hits'])
        self.assertEqual(c['coverage']['reconciliation'],p['reconciliation'])


if __name__=='__main__':unittest.main()
