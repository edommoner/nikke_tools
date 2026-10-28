"""Page/row diagnostics preserve raw and distinguish references from numbers."""
import copy,hashlib,struct,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_partitioned_wire_index as index
import portable_partitioned_addresses as addresses


class WireIndexTests(unittest.TestCase):
    def fixture(self,root):
        rows=[];global_rows=[]
        for i in range(2):
            row=bytearray(addresses.WORDS*4);struct.pack_into('<I',row,0,64 if i else 0)
            field=addresses.DFS_BASE+530;struct.pack_into('<II',row,field*4,addresses.RECEIPT_BASE,1);struct.pack_into('<I',row,addresses.RECEIPT_BASE*4,1)
            rows.append(row);view=bytearray(row);addresses.logical_row_inplace(view,0,i);global_rows.append(view)
        actual=root/'raw';actual.write_bytes(b''.join(rows));baseline=root/'baseline';baseline.write_bytes(b''.join(global_rows))
        entries=[dict(name=str(i),output_sha256=hashlib.sha256(row).hexdigest()) for i,row in enumerate(global_rows)]
        layout=dict(output_words=addresses.WORDS,input_count=2,batches=[dict(first_case=0,cases=1),dict(first_case=1,cases=1)])
        return actual,baseline,entries,layout

    def test_same_logical_values_different_local_reference_keeps_all_status_and_page_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw,base,entries,layout=self.fixture(Path(tmp));before=raw.read_bytes()
            r=index.scan(raw,layout,hashlib.sha256(before).hexdigest(),entries)
            self.assertEqual(r['mismatching_cases'],[]);self.assertEqual([v['status'] for v in r['rows']],[0,64])
            self.assertNotEqual(r['raw_sha256'],r['logical_sha256']);self.assertEqual(raw.read_bytes(),before)
            flat=dict(layout,batches=[dict(first_case=0,cases=2)])
            ref=index.scan(base,flat,hashlib.sha256(base.read_bytes()).hexdigest(),entries)
            self.assertEqual(r['logical_sha256'],ref['logical_sha256']);self.assertEqual([v['logical_pages'] for v in r['rows']],[v['logical_pages'] for v in ref['rows']])

    def test_numerical_difference_is_localized_without_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw,base,entries,layout=self.fixture(Path(tmp))
            with raw.open('r+b') as f:f.seek(addresses.WORDS*4+7*4);f.write(struct.pack('<I',12345))
            r=index.scan(raw,layout,hashlib.sha256(raw.read_bytes()).hexdigest(),entries)
            ref=index.scan(base,dict(layout,batches=[dict(first_case=0,cases=2)]),hashlib.sha256(base.read_bytes()).hexdigest(),entries)
            self.assertEqual(r['mismatching_cases'],[1])
            self.assertEqual([i for i,(a,b) in enumerate(zip(r['rows'][1]['logical_pages'],ref['rows'][1]['logical_pages'])) if a!=b],[0])
            delta=index.compare(ref,r)
            self.assertEqual(delta['changed_page_count'],1);self.assertEqual(delta['changed_cases'][0]['index'],1)
            self.assertFalse(delta['calculation_verified'])
            with base.open('rb') as f:f.seek(addresses.WORDS*4);page=f.read(index.PAGE_WORDS*4)
            details=dict(block_words=1024,maximum_samples=8,pages=[dict(case_index=1,page_index=0,block_sha256=[hashlib.sha256(page[at:at+4096]).hexdigest() for at in range(0,len(page),4096)])])
            detailed=index.scan(raw,layout,hashlib.sha256(raw.read_bytes()).hexdigest(),entries,details)
            self.assertEqual(len(detailed['detail_different_blocks']),1);self.assertEqual(detailed['detail_samples'][0]['words'][7],12345)
            self.assertLessEqual(sum(len(s['words']) for s in detailed['detail_samples']),8*1024)
            compared=index.compare_samples(ref,detailed,base)
            self.assertEqual(compared['sample_comparisons'][0]['changed_words'],[dict(word=7,reference=0,candidate=12345)])
            self.assertFalse(compared['calculation_verified'])
            for kind in ('tampered_word','duplicate_case','bad_reference','bool_word','changed_raw'):
                bad=copy.deepcopy(detailed)
                if kind=='tampered_word':bad['detail_samples'][0]['words'][7]=1
                elif kind=='duplicate_case':bad['detail_samples']*=2
                elif kind=='bad_reference':bad['detail_samples'][0]['reference_sha256']='0'*64
                elif kind=='bool_word':bad['detail_samples'][0]['words'][7]=True
                else:
                    with base.open('r+b') as f:f.seek(0);f.write(struct.pack('<I',123))
                with self.subTest(kind=kind),self.assertRaises(ValueError):index.compare_samples(ref,bad,base)

    def test_wrong_hash_short_file_and_bad_plan_do_not_return_partial_index(self):
        for kind in ('hash','short','plan'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                raw,_,entries,layout=self.fixture(Path(tmp));sha=hashlib.sha256(raw.read_bytes()).hexdigest()
                if kind=='hash':sha='0'*64
                elif kind=='short':
                    with raw.open('r+b') as f:f.truncate(raw.stat().st_size-4)
                else:layout['batches'][1]['first_case']=0
                with self.assertRaises(ValueError):index.scan(raw,layout,sha,entries)


if __name__=='__main__':unittest.main()
