"""Enumeration emission reuse preserves changing scale, sums and partition ranks."""
import copy
import ctypes as C
import importlib.util
import itertools
import math
from pathlib import Path
import struct
import sys
import unittest

HERE=Path(__file__).resolve().parents[1]/'research/team-search'
sys.path.insert(0,str(HERE))
import l2_fast
import l2_score_s20
import l2_score_s22


class EnumerationReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('s25_fixture',HERE/'l2_fast/verify.py')
        fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
        p=fixture.synthetic();original=list(p['characters'].values());p['characters']={}
        p['s20']={'version':2,'switches':15};p['s22']={'version':3,'switches':144}
        for i in range(11):
            c=copy.deepcopy(original[i%7]);name=f'm{i:02}'
            c['metadata'].update(burst_stage=str(i%3+1),burst_cooldown=20.+20.*(i%2),max_ammo=10,fire_rate=2.,reload_time=1.)
            c['buffs']=[dict(phase=phase,effect={'target':'all_allies'},amount={'atk_pct':.25,'damage_taken_pct':-0.}) for phase in (0,1)]
            c['groups']+=copy.deepcopy(c['groups'])
            c['groups'][-1]['own']['atk_pct']=-0.
            c['mechanics_s20']=[[0,2,0,1,1.25,1,2]] if i%4==0 else []
            p['characters'][name]=c
        cls.profile=p;cls.lib=l2_fast.build()

    def test_complete_and_sampled_partitions_match_raw_oracle(self):
        fast=l2_fast.Score(self.profile,library=self.lib);oracle=l2_score_s22.Score(self.profile)
        roster=list(range(11));allrows=[]
        for rank,ids in enumerate(itertools.combinations(roster,5)):
            names=[fast.names[i] for i in ids]
            if l2_score_s20.cycle(names,self.profile['characters'],180.)[2]:
                allrows.append((rank,list(ids),oracle(names)))
        try:
            for stride in (1,3,17):
                expected=sorted([(ids,struct.pack('<d',score)) for rank,ids,score in allrows if rank%stride==0],key=lambda row:(-struct.unpack('<d',row[1])[0],row[0]))
                for threads in (1,7,10):
                    r=l2_fast.enumerate_top(fast,roster[::-1],1000,threads,stride)
                    self.assertEqual([(e['indices'],struct.pack('<d',e['score'])) for e in r['entries']],expected)
                    self.assertEqual(r['counts']['visited'],math.comb(11,5))
                    self.assertEqual(r['counts']['scored'],len(expected))
        finally:fast.close()

    def test_balanced_partitions_merge_identically_and_validate_roster(self):
        fast=l2_fast.Score(self.profile,library=self.lib)
        fn=fast.lib.l2_enumerate_balanced
        fn.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_size_t,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(l2_fast.Entry),C.POINTER(C.c_size_t),C.POINTER(l2_fast.Counts)]
        try:
            expected=l2_fast.enumerate_top(fast,list(range(11)),1000,1,3)
            rows=[];visited=covered=scored=0
            for part in range(7):
                ids=(C.c_uint32*11)(*range(11));out=(l2_fast.Entry*1000)();n=C.c_size_t();counts=l2_fast.Counts()
                self.assertEqual(fn(fast.table,ids,11,1000,part,7,3,out,C.byref(n),C.byref(counts)),0)
                visited+=counts.visited;covered+=counts.covered;scored+=counts.scored
                rows.extend((list(e.ids),struct.pack('<d',e.score)) for e in out[:n.value])
            rows.sort(key=lambda row:(-struct.unpack('<d',row[1])[0],row[0]))
            self.assertEqual(rows,[(e['indices'],struct.pack('<d',e['score'])) for e in expected['entries']])
            self.assertEqual((visited,covered,scored),tuple(expected['counts'][key] for key in ('visited','covered','scored')))
            ids[1]=ids[0]
            self.assertEqual(fn(fast.table,ids,11,1000,0,7,1,out,C.byref(n),C.byref(counts)),-1)
        finally:fast.close()
