"""Complete continuation rows, strict ownership and exact historical inverse."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_skill_history as history
from portable_specs import LIMITS as L

class SharedSkillHistory(unittest.TestCase):
    def fixture(self,count):
        block=[0]*history.OUTPUT_WORDS;rows=[];indices=[]
        number=lambda n:list(struct.unpack('<II',struct.pack('<d',n)))
        for i in range(count):
            recipients=[0,3,127] if i%7==0 else [0]
            row=dict(row=11,hit=i%3+1,hits=3,created=i/60,landed=i/60,amount=float(i+5),share=float(i+5)/len(recipients),recipients=recipients)
            words=[0]*48;words[:4]=[1,row['hit'],row['hits'],len(recipients)]
            for j,key in enumerate(('created','landed','amount','share')):words[4+j*2:6+j*2]=number(row[key])
            for slot in recipients:words[12+slot//32]|=1<<(slot%32)
            for j,slot in enumerate(recipients):words[16+j//4]|=(slot+1)<<((j%4)*8)
            at=L['WORLD_SKILL_TRACE_BASE']+i*48 if i<128 else history.BASE+(i-128)*48
            block[at:at+48]=words;rows.append(row);indices.append(copy.deepcopy(row))
        head=L['WORLD_SKILL_HEAD_BASE'];block[head:head+4]=[0x57534b31,count,max((len(r['recipients']) for r in rows),default=0),sum(len(r['recipients']) for r in rows)]
        return block,({},dict(binding_source_indices=[7,11]),(),{}),dict(skill_trace=rows),indices

    def test_all_pages_and_boundaries_use_the_original_decoder(self):
        for count in (0,127,128,129,1618,2048):
            with self.subTest(count=count):
                block,domain,native,indices=self.fixture(count)
                view,legacy,receipts=history.compare_and_project(block,domain,native,indices)
                self.assertEqual(view[L['WORLD_SKILL_HEAD_BASE']+1],min(count,128))
                self.assertEqual(legacy['skill_trace'],native['skill_trace'][:128]);self.assertEqual(receipts,indices[:128])
                self.assertFalse(any(view[history.BASE:history.END]));self.assertEqual(len(native['skill_trace']),count)
                self.assertEqual(block[L['WORLD_SKILL_HEAD_BASE']+1],count)
                self.assertEqual(view[:history.BASE][L['WORLD_SKILL_TRACE_BASE']:L['WORLD_SKILL_TRACE_BASE']+128*48],block[L['WORLD_SKILL_TRACE_BASE']:L['WORLD_SKILL_TRACE_BASE']+128*48])

    def test_late_row_corruption_cannot_be_hidden_by_prefix_projection(self):
        for index in (0,127,128,1617,2047):
            with self.subTest(index=index):
                block,domain,native,indices=self.fixture(2048)
                at=L['WORLD_SKILL_TRACE_BASE']+index*48 if index<128 else history.BASE+(index-128)*48
                block[at+8]^=1
                with self.assertRaisesRegex(AssertionError,'Every ordered'):history.compare_and_project(block,domain,native,indices)

    def test_count_bitmap_padding_and_creation_receipt_are_strict(self):
        for offset in (L['WORLD_SKILL_HEAD_BASE']+1,L['WORLD_SKILL_HEAD_BASE']+2,L['WORLD_SKILL_HEAD_BASE']+4,history.BASE+12,history.BASE+20,history.BASE+48):
            with self.subTest(offset=offset):
                block,domain,native,indices=self.fixture(129);block[offset]^=1
                with self.assertRaises(AssertionError):history.compare_and_project(block,domain,native,indices)
        block,domain,native,indices=self.fixture(129);indices.pop()
        with self.assertRaisesRegex(AssertionError,'creation receipt'):history.compare_and_project(block,domain,native,indices)

    def test_capacity_and_layout_are_not_dynamic_or_silent(self):
        history.check_layout(ROOT)
        self.assertLessEqual(history.END,history.COORDINATE_OUTPUT_WORDS+136688)
        for capacity,count in ((128,129),(2048,2049),(True,0),(4096,0)):
            with self.subTest(capacity=capacity,count=count),self.assertRaises(ValueError):history.require_capacity(dict(skill_trace=[None]*count),capacity)
        history.require_capacity(dict(skill_trace=[None]*2048))

    def test_exact_source_and_transport_inverse_rejects_unreviewed_bytes(self):
        from portable_skill_history_source_contract import ledger,project_sources,project_backend_source
        data=ledger(ROOT);project_sources(ROOT);project_backend_source(ROOT)
        for name in [*data['added_sources'],'gpu/world_skill_runtime.slang']:
            with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n')
        from portable_coordinate_typed_source_contract import project_sources as legacy
        from portable_arena_transport_source_contract import historical_backend_source
        legacy(ROOT);historical_backend_source(ROOT)

    def test_registered_wire_is_exact_and_legacy_entry_does_not_gain_history(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride(history.SOURCE,history.INPUT_WORDS,history.OUTPUT_WORDS)
        for source,iw,ow in [(history.SOURCE,history.INPUT_WORDS-1,history.OUTPUT_WORDS),(history.SOURCE,history.INPUT_WORDS,history.OUTPUT_WORDS+1),('gpu/world_coordinate_typed_history_unknown.slang',history.INPUT_WORDS,history.OUTPUT_WORDS)]:
            with self.subTest(source=source,iw=iw,ow=ow),self.assertRaises(ValueError):validate_composed_stride(source,iw,ow)
        self.assertNotIn('WORLD_SKILL_TRACE_CAPACITY',(ROOT/'gpu/world_coordinate_typed_owner_entry.slang').read_text())

    def test_sealed_cohort_and_cached_cuda_use_identical_calculation_and_cases(self):
        import nikke_gpu as cli
        base=cli.SUITES['original-catalogue-initial'];cached=cli.SUITES['original-catalogue-initial-cache-only']
        for key in ('source','script','golden','frozen_cases','input_words','output_words','native','inputs'):self.assertEqual(base[key],cached[key])
        self.assertEqual(base['source'],history.SOURCE);self.assertEqual(len(base['frozen_cases']),4)
        self.assertFalse(base['development_only']);self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        self.assertTrue(cli.SUITES['original-catalogue']['development_only'])

    def test_direct_and_already_projected_transport_use_the_same_exact_inverse(self):
        from portable_coordinate_resident_arc_source_contract import ledger,project_backend_source
        row=ledger(ROOT)['sources']['app/portable_backend.py']
        self.assertEqual(project_backend_source(ROOT),row['baseline'])
        self.assertEqual(project_backend_source(ROOT,row['current']),row['baseline'])
        for text in ((ROOT/'app/portable_backend.py').read_text()+'\n',row['current']+'\n'):
            with self.assertRaises(ValueError):project_backend_source(ROOT,text)

if __name__=='__main__':unittest.main()
