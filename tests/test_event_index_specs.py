import random,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from event_index_specs import build_index,candidates,EVENT_COUNT,TRIGGER_BASE,TRIGGER_WIDTH

def row(events):
    values=[0.0]*304;values[144]=len(events)
    for at,event in enumerate(events):values[TRIGGER_BASE+at*TRIGGER_WIDTH]=event
    return values

class EventIndexSpecification(unittest.TestCase):
    def test_ordered_candidates_equal_original_scan_with_duplicates_and_empty_events(self):
        rng=random.Random(812)
        for count in (0,1,17,256):
            rows=[row([rng.randrange(EVENT_COUNT) for _ in range(rng.randrange(9))]) for _ in range(count)]
            plan=build_index(rows)
            self.assertEqual(len(plan['offsets']),129);self.assertLessEqual(len(plan['definitions']),count*8)
            for event in range(EVENT_COUNT):
                expected=tuple(i for i,r in enumerate(rows) if any(r[TRIGGER_BASE+at*TRIGGER_WIDTH]==event for at in range(int(r[144]))))
                self.assertEqual(plan['definitions'][plan['offsets'][event]:plan['offsets'][event+1]],expected)
    def test_direct_continuations_bypass_declared_triggers_without_out_of_bounds(self):
        plan=build_index([row([0,0,58]),row([7])])
        self.assertEqual(candidates(plan,0),(0,));self.assertEqual(candidates(plan,58),(0,))
        for event in (28,47,57,61):
            self.assertEqual(candidates(plan,event,1),(1,))
            self.assertEqual(candidates(plan,event,-1),());self.assertEqual(candidates(plan,event,2),())
        with self.assertRaises(ValueError):build_index([row([128])])
        with self.assertRaises(ValueError):build_index([row([0]*9)])

if __name__=='__main__':unittest.main()
