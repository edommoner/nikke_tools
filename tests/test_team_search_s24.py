"""Exact cache behavior across contexts, ordering, tables and enumeration."""
import copy
import importlib.util
import itertools
from pathlib import Path
import random
import shutil
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/team-search'))
import l2_fast
import l2_score_s22
import l2_score_s20


@unittest.skipUnless(shutil.which('clang++'),'clang++ required')
class ReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('s24_fixture',ROOT/'research/team-search/l2_fast/verify.py')
        fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
        cls.profile=fixture.synthetic()
        p=cls.profile;p['s20']={'version':2,'switches':15};p['s22']={'version':3,'switches':144}
        for i,(name,c) in enumerate(p['characters'].items()):
            c['metadata'].update(max_ammo=10,fire_rate=2.,reload_time=1.,is_charge=bool(i%2))
            c['base_stats'].update(hp=1000.+i,**{'def':10.+i})
            c['mechanics_s20']=[[0,2,i%4,1,1.25,1,2],[3,0,(i+1)%4,1,-2.,0,0]]
            if i==1:c['mechanics_s20'].append([1,0,2,1,2.,0,0])
            for b in c['buffs']:
                b['recipients']=[name];b['condition_s20']=i%4
            c['groups'] += copy.deepcopy(c['groups'])
            c['groups'][-1]['own']['atk_pct']=-0.
            c['buffs'].append(dict(phase=1,effect={'target':'allies_top_atk_excl:2'},amount={'atk_pct':3.25},recipients=[]))
        cls.lib=l2_fast.build()

    def test_raw_batches_and_interleaved_tables(self):
        p=self.profile;q=copy.deepcopy(p);q['settings']['duration']=73.5
        q['characters']['a']['metadata']['burst_cooldown']=17.
        rng=random.Random(240024);names=list(p['characters'])
        rows=[rng.sample(names,5) for _ in range(600)];rows+=rows[:100]
        a=l2_fast.Score(p,library=self.lib);b=l2_fast.Score(q,library=self.lib)
        try:
            for fast,profile in [(a,p),(b,q),(a,p),(b,q)]:
                oracle=l2_score_s22.Score(profile)
                expected=b''.join(struct.pack('<6d',max(sum(v.values()),1.),*v.values()) for v in map(oracle.member_scores,rows))
                totals,members=fast.score_indices(fast._indices(rows),True)
                actual=b''.join(struct.pack('<6d',totals[i],*members[5*i:5*i+5]) for i in range(len(rows)))
                self.assertEqual(actual,expected)
        finally:a.close();b.close()

    def test_tiny_exhaustive_topk_matches_oracle(self):
        fast=l2_fast.Score(self.profile,library=self.lib);oracle=l2_score_s22.Score(self.profile)
        try:
            for n in (6,7):
                expected=[];covered=0
                for ids in itertools.combinations(range(n),5):
                    squad=[fast.names[i] for i in ids]
                    if not l2_score_s20.cycle(squad,self.profile['characters'],180.)[2]:continue
                    covered+=1;expected.append((ids,struct.pack('<d',oracle(squad)),oracle(squad)))
                expected.sort(key=lambda x:(-x[2],x[0]))
                for threads in (1,10):
                    r=l2_fast.enumerate_top(fast,list(range(n)),100,threads)
                    self.assertEqual([(tuple(e['indices']),struct.pack('<d',e['score'])) for e in r['entries']],[(ids,bits) for ids,bits,_ in expected])
                    self.assertEqual(r['counts']['scored'],covered)
        finally:fast.close()
