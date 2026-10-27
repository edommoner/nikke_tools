"""No row exemptions: all fate words, unused slots and tail are checked."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import portable_packet_fates as fates

class FateTests(unittest.TestCase):
    def sample(self):
        case=dict(names=['a','b','c','d','e'],owners=[0,0],effects=[dict(name='typed'),dict(name='child')])
        trace=[dict(row=0,created=.2,landed=.22,amount=40.,share=40.,hit=1,hits=1,recipients=[0]),dict(row=1,created=.2,landed=.22,amount=50.,share=50.,hit=1,hits=1,recipients=[0])]
        events=[dict(caster='a',name='typed',created=.2,landed=.22,amount=40.)]
        native=dict(skill_trace=trace,receipt_fates=fates.native_fates(case,trace,events))
        block=[0]*fates.OUTPUT;block[fates.HEAD:fates.FLAGS]=[fates.MAGIC,1,1,1]+[0]*12;block[fates.FLAGS]=1
        return case,trace,events,native,block

    def test_complete_projection_retains_proposals_and_explicit_suppression(self):
        _,trace,_,n,b=self.sample();before=copy.deepcopy(n)
        projected=fates.compare_and_project(b,n);self.assertEqual(len(projected),806912);self.assertEqual(n,before)
        self.assertEqual(n['receipt_fates'][0],dict(index=0,disposition='suppressed_native_body',requested_recipients=[0],actor_effects_allowed=False))
        self.assertEqual(len(trace),2)

    def test_bad_flags_counts_reserved_words_and_unowned_tail_cannot_disappear(self):
        _,_,_,n,b=self.sample()
        for at,value in [(fates.HEAD,0),(fates.HEAD+1,0),(fates.HEAD+2,2),(fates.HEAD+3,0),(fates.HEAD+15,1),(fates.FLAGS,0),(fates.FLAGS+1,1),(fates.END-1,1),(fates.END,1),(fates.OUTPUT-1,1)]:
            bad=list(b);bad[at]=value
            with self.subTest(at=at),self.assertRaises(AssertionError):fates.compare_and_project(bad,n)
        bad=copy.deepcopy(n);bad['receipt_fates'][0]['actor_effects_allowed']=True
        with self.assertRaises(AssertionError):fates.compare_and_project(b,bad)

    def test_missing_duplicate_or_changed_native_stub_is_refused(self):
        c,t,e,_,_=self.sample()
        for trace,events in [(t[1:],e),(t,e+e),(t,[dict(e[0],amount=41.)])]:
            with self.assertRaises(AssertionError):fates.native_fates(c,trace,events)

    def test_resident_cache_entry_reuses_same_calculation_and_requires_both_hits(self):
        import nikke_gpu as cli
        normal=cli.SUITES['lock-projectile-composition'];cached=cli.SUITES['lock-projectile-cache-only']
        for key in ('script','golden','source','input_words','output_words','inputs','native'):self.assertEqual(normal[key],cached[key])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1');self.assertIs(cached['require_paired_generation'],True)

if __name__=='__main__':unittest.main()
