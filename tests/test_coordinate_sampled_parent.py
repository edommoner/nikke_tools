import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_coordinate_sampled_parent_cases import fixtures
from world_coordinate_sampled_parent_native import observe
s=importlib.util.spec_from_file_location('sampled_parent_adapter',ROOT/'research/verify-coordinate-sampled-parent-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class ParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers=[observe(c)[0] for c in cls.cases]
    def test_real_parent_quantities_and_input_immutability(self):
        self.assertEqual(len(self.cases),16);self.assertEqual(self.cases,self.before)
        for c,n in zip(self.cases,self.answers,strict=True):self.assertTrue(n['full_charge_quantities']);self.assertTrue(n['landed_packets'])
    def test_absent_context_zero_negative_and_single_budget(self):
        by={c['name'].rsplit('/',1)[1]:n for c,n in zip(self.cases,self.answers,strict=True)}
        for label in ['zero','negative','absent-hit-count','absent-battle-start']:self.assertFalse([p for p in by[label]['landed_packets'] if p['skill_name']=='sampled-parent'])
        self.assertEqual(len([p for p in by['budget-one']['landed_packets'] if p['skill_name']=='sampled-parent']),1)
    def test_old23_static_inputs_and_native_domains_are_retained(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle packing')):rows,raw=a.prepare();old,_=a.parent.prepare()
        self.assertEqual(rows[:23],old);self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(39,36));self.assertEqual(len(raw),4+39*a.INPUT_WORDS*4)
    def test_exact_ratio_notices_can_be_reconstructed_from_real_packets(self):
        for n in self.answers:
            self.assertTrue(all(isinstance(p['damage'],int) for row in n['physical_pellets'] for p in row['packets']))
    def test_real_odd_muzzle_parent_requires_one_round_after_integer_division(self):
        from world_frame_native import roster_names
        index=next(i for i,c in enumerate(self.cases) if c['name'].endswith('/large-integer'));c=self.cases[index];n=self.answers[index];names=roster_names(c);different=0
        for notice in n['full_charge_quantities']:
            total=sum(p['damage'] for row in n['physical_pellets'] if row['owner']==names[notice['owner']] and row['time']==notice['time'] for p in row['packets'])
            divisor=c['combat']['weapons'][notice['owner']]['muzzles'];different+=float(total)/divisor!=notice['dealt']
        self.assertGreater(different,0)
    def test_exact_whole_battle_total_and_corruption(self):
        from portable_sampled_damage_totals import BASE,WORDS,MAGIC,exact_damage,verify_layout
        from portable_coordinate_physical_specs import LAYOUT as CF
        self.assertTrue(verify_layout())
        needs_integer=False
        for n in self.answers:
            totals=[0]*5;rounded=[0.]*5;counts=[0]*5
            # Current authored worlds contain BODY/PART/INTERRUPT, no ADD.
            kinds={'stop':6}
            for p in n['landed_packets']:
                if kinds.get(p['target'],0)==6:continue
                who=p['owner'];totals[who]+=p['damage'];rounded[who]+=float(p['damage']);counts[who]+=1
            self.assertEqual(totals,n['battle']['damage'])
            needs_integer|=any(int(float(v))!=v for v in totals)
            block=[0]*CF['END'];block[BASE:BASE+4]=[MAGIC,1,5,0]
            for who,v in enumerate(totals):
                at=BASE+4+who*5;block[at:at+5]=[(v>>(32*i))&0xffffffff for i in range(4)]+[counts[who]]
            self.assertEqual(exact_damage(block,rounded,n['landed_packets'],kinds),totals)
            for at in (BASE,BASE+3,BASE+4,BASE+5,BASE+6,BASE+7,BASE+8,BASE+WORDS):
                block[at]^=1
                with self.assertRaises(AssertionError):exact_damage(block,rounded,n['landed_packets'],kinds)
                block[at]^=1
            bad=rounded[:];bad[0]+=1024.
            with self.assertRaises(AssertionError):exact_damage(block,bad,n['landed_packets'],kinds)
        self.assertTrue(needs_integer)
if __name__=='__main__':unittest.main()
