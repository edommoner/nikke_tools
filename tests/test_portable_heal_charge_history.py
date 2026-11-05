"""Complete ordered SHA chain, bounded raw prefix, zero-history and corruption gates."""
import array,hashlib,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_heal_charge_specs import TRACE_BASE,TRACE_COUNT,TRACE_WORDS,TRACE_MAGIC
from portable_heal_charge_history import TAIL,MAGIC,digest,verify
from portable_specs import LIMITS as L

def rows(count):return [[1+i%3,i%256,i%5]+list(struct.unpack('<10I',struct.pack('<5d',i/30.,float(i),float(i+1),1500.,10.)))+[0]*7 for i in range(count)]
def block(records):
    n=len(records);w=array.array('I',[0])*L['WORLD_RELOAD_OUTPUT_WORDS'];head=[TRACE_MAGIC if n else 0,min(n,TRACE_COUNT),n,0,0,0,0,0]
    if n>TRACE_COUNT:head[3:]=[MAGIC,1,TRACE_COUNT,n-TRACE_COUNT,TRACE_WORDS]
    w[TRACE_BASE:TRACE_BASE+8]=array.array('I',head)
    for i,r in enumerate(records[:TRACE_COUNT]):w[TRACE_BASE+8+i*TRACE_WORDS:TRACE_BASE+8+(i+1)*TRACE_WORDS]=array.array('I',r)
    if n>TRACE_COUNT:w[TAIL:TAIL+8]=array.array('I',struct.unpack('>8I',digest(records)))
    return w
class HealingHistoryTests(unittest.TestCase):
    def test_empty_prefix_boundary_first_overflow_and_real_length(self):
        for count in (0,1,511,512,513,1272):
            r=rows(count);out=verify(block(r),r);self.assertEqual(out['total'],count);self.assertTrue(out['complete_order_and_quantities_verified'])
    def test_hashlib_chain_wire_is_exact_and_includes_clocks(self):
        self.assertEqual(digest([[1,2,3]+[0]*17]).hex(),'d8525a199921adfae34f7ca0d72f046b9141d2428f32aeec685059e5e8df4cab')
        r=rows(513);h=digest(r);r[-1][3]^=1;self.assertNotEqual(digest(r),h)
    def test_prefix_suffix_amount_order_hash_and_version_corruption_rejected(self):
        r=rows(1272);w=block(r)
        for at in (TRACE_BASE,TRACE_BASE+2,TRACE_BASE+3,TRACE_BASE+6,TRACE_BASE+8+7,TAIL):
            wrong=array.array('I',w);wrong[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):verify(wrong,r)
        for mode in ('amount','clock','order'):
            altered=[list(row) for row in r]
            if mode=='order':altered[-1],altered[-2]=altered[-2],altered[-1]
            else:altered[-1][7 if mode=='amount' else 3]^=1
            with self.subTest(mode=mode),self.assertRaises(AssertionError):verify(w,altered)
    def test_short_capture_keeps_old_zero_tail_and_bank_ends_before_parts(self):
        r=rows(512);w=block(r);w[TAIL]=1
        with self.assertRaises(AssertionError):verify(w,r)
        from portable_scratch_layout import verify as layout
        result=layout(L,mode='heal-charge');bank=next(b for b in result['banks'] if b['name']=='heal-charge');self.assertEqual(bank['end'],781328)
if __name__=='__main__':unittest.main()
