"""Retained histories must account for every omitted event explicitly."""
import array,copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_roster_team_history import fractional_view

class OriginalHistoryTests(unittest.TestCase):
    def data(self,count):
        b=array.array('I',[0x57465231,min(count,2048),7,max(count-2048,0),0,0,0,0])
        n=dict(fractional_hits=list(range(count)),fractional_accumulators=[dict(value=.5)],damage=[12])
        return b,n
    def test_exact_retention_boundaries_keep_final_state_and_originals(self):
        for count in (0,2047,2048,2049,3870):
            b,n=self.data(count);before=copy.deepcopy((b,n));view,expected=fractional_view(b,n,0)
            self.assertEqual((b,n),before)
            self.assertEqual(expected['fractional_hits'],n['fractional_hits'][:2048])
            self.assertEqual(expected['fractional_accumulators'],n['fractional_accumulators'])
            self.assertEqual(expected['damage'],n['damage']);self.assertEqual(view[3],0)
    def test_wrong_count_omissions_magic_and_reserved_words_are_rejected(self):
        for offset in (0,1,3,4,5,6,7):
            b,n=self.data(3870);b[offset]+=1
            with self.assertRaises(AssertionError):fractional_view(b,n,0)
    def test_omission_without_overflow_is_rejected(self):
        b,n=self.data(2048);b[3]=1
        with self.assertRaises(AssertionError):fractional_view(b,n,0)

if __name__=='__main__':unittest.main()
