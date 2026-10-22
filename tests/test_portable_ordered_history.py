"""Selection-history protocol, hashlib oracle, allocation and exact source deltas."""
import array,copy,hashlib,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_ordered_history import canonical,semantic_digest,verify_history,MAGIC
from portable_ordered_history_source_contract import ledger,project_sources,baseline_source
from portable_query_diagnostic_source_contract import project_sources as project_diagnostic
from portable_specs import LIMITS as L


def adapter():
    spec=importlib.util.spec_from_file_location('history_test',ROOT/'research/verify-ordered-history-short.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def decoder_fixture(records):
    b=array.array('I',[0])*786432;head=2048;count=len(records)
    for i,r in enumerate(records[:128]):b[8+i*8:16+i*8]=array.array('I',r)
    if count>128:
        b[head:head+8]=array.array('I',[MAGIC,1,count,128,count-128,8,1,(count*8)%16])
        state=list(struct.unpack('>8I',bytes.fromhex(semantic_digest(records))))
        b[head+8:head+16]=array.array('I',state);b[head+32:head+40]=array.array('I',state)
        padding=([int.from_bytes(struct.pack('<I',w),'big') for w in canonical(records[-1])] if count%2 else [])+[0x80000000]
        padding += [0]*(14-len(padding))+[0,count*256]
        b[head+16:head+32]=array.array('I',padding);b[head+48:head+56]=array.array('I',records[-1])
    return b


class OrderedHistoryTests(unittest.TestCase):
    def test_authored_boundary_and_long_hash_oracles(self):
        module=adapter();entries,_=module.prepare()
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(13,10))
        for case in module.CASES[:10]:
            records=module.records(case);block=decoder_fixture(records)
            report=verify_history(block,records,prefix=8,head=2048,total=len(records))
            self.assertEqual(report['raw_suffix_omitted'],max(0,len(records)-128))
            self.assertFalse(report['timestamps_in_semantic_digest'])
        self.assertEqual(semantic_digest([]),hashlib.sha256(b'').hexdigest())

    def test_decoder_detects_prefix_suffix_order_state_and_metadata_faults(self):
        records=adapter().records(dict(count=4550,seed=7));block=decoder_fixture(records);head=2048
        for at in (8+1,head,head+2,head+4,head+6,head+7,head+8,head+16,head+32,head+40,head+48,head+56):
            bad=array.array('I',block);bad[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):verify_history(bad,records,prefix=8,head=head,total=len(records))
        for change in ('suffix-value','suffix-order'):
            bad=copy.deepcopy(records)
            if change=='suffix-value':bad[1000][1]^=1
            else:bad[1000],bad[1001]=bad[1001],bad[1000]
            with self.subTest(change=change),self.assertRaises(AssertionError):verify_history(block,bad,prefix=8,head=head,total=len(records))

    def test_clock_exclusion_is_explicit_and_semantic_words_remain_covered(self):
        a=[3,1,2,3,4,5,6,7];b=list(a);b[6]^=1
        self.assertEqual(semantic_digest([a]),semantic_digest([b]))
        b=list(a);b[4]^=1;self.assertNotEqual(semantic_digest([a]),semantic_digest([b]))

    def test_allocation_and_every_new_delta_guard(self):
        self.assertEqual(L['ORDERED_HISTORY_BASE'],L['NATIVE_QUERY_BASE']+L['NATIVE_QUERY_WORDS'])
        self.assertLessEqual(L['ORDERED_HISTORY_BASE']+L['ORDERED_HISTORY_WORDS'],786416)
        project_sources(ROOT)
        projected,_=project_diagnostic(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            source=projected.get(name,(ROOT/name).read_text())
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    baseline_source(ROOT,name,source.replace(change['current'],change['baseline'],1),diagnostic_projected=True)


if __name__=='__main__':unittest.main()
