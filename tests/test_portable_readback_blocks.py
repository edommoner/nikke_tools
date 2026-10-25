"""Saved buffers only; fixed anchors and bounded samples preserve original files."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_readback_blocks as blocks


class ReadbackBlockTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.raw=bytes(blocks.CASE_WORDS*4);self.path=self.root/'raw';self.path.write_bytes(self.raw);self.sha=blocks.digest(self.raw);self.index=blocks.scan(self.path,self.sha)
    def test_equal_bytes_and_fixed_case_shape(self):
        r=blocks.compare(self.path,self.sha,self.index);self.assertTrue(r['all_blocks_equal']);self.assertEqual(r['blocks'],768);self.assertFalse(r['calculation_verified']);self.assertEqual(self.path.read_bytes(),self.raw)
    def test_differing_blocks_keep_exact_locations_and_bounded_samples(self):
        raw=bytearray(self.raw)
        for i in range(10):raw[i*4096+8]=17
        self.path.write_bytes(raw);r=blocks.compare(self.path,blocks.digest(raw),self.index)
        self.assertEqual(r['changed_blocks'],list(range(10)));self.assertEqual(len(r['samples']),8);self.assertEqual(r['samples'][0]['words'][2],17);self.assertEqual(self.path.read_bytes(),raw)
    def test_wrong_hash_short_file_or_changed_index_is_rejected(self):
        with self.assertRaises(ValueError):blocks.scan(self.path,'0'*64)
        self.path.write_bytes(b'x')
        with self.assertRaises(ValueError):blocks.scan(self.path,blocks.digest(b'x'))
        self.index['block_words']=32
        with self.assertRaises(ValueError):blocks.compare(self.path,'0'*64,self.index)
    def test_sampling_rejects_changed_file_after_first_pass(self):
        original=blocks.scan
        def changed(*args,**kwargs):
            result=original(*args,**kwargs);self.path.write_bytes(bytes([1])+self.raw[1:]);return result
        with patch.object(blocks,'scan',side_effect=changed),self.assertRaisesRegex(ValueError,'changed while sampling'):blocks.compare(self.path,self.sha,self.index)
    def test_index_anchor_and_existing_output_are_not_overwritten(self):
        index=self.root/'index.json';blocks.write(index,self.index);out=self.root/'result.json'
        with self.assertRaisesRegex(ValueError,'index SHA'):blocks.main(['compare','--readback',str(self.path),'--sha256',self.sha,'--index',str(index),'--index-sha256','0'*64,'--out',str(out)])
        self.assertFalse(out.exists());out.write_text('original')
        with self.assertRaises(FileExistsError):blocks.write(out,{})
        self.assertEqual(out.read_text(),'original')

    def test_extended_shape_has_correct_second_case_offsets(self):
        raw=bytes(1048576*4*2);self.path.write_bytes(raw);index=blocks.scan(self.path,blocks.digest(raw),case_words=1048576)
        changed=bytearray(raw);changed[1048576*4+16]=9;self.path.write_bytes(changed)
        r=blocks.compare(self.path,blocks.digest(changed),index)
        self.assertEqual(r['changed_blocks'],[1024]);self.assertEqual((r['samples'][0]['case_index'],r['samples'][0]['case_word_offset']),(1,0));self.assertEqual(r['samples'][0]['words'][4],9)

    def test_ambiguous_file_shape_requires_the_declared_stride(self):
        raw=bytes(3*1048576*4);self.path.write_bytes(raw);h=blocks.digest(raw)
        self.assertEqual(blocks.scan(self.path,h)['cases'],4)
        self.assertEqual(blocks.scan(self.path,h,case_words=1048576)['cases'],3)
        for size in (True,786433,1048577):
            with self.assertRaises(ValueError):blocks.scan(self.path,h,case_words=size)

    def capture(self,name,rows,*,words=1048576):
        folder=self.root/name;folder.mkdir();raw=b''.join(bytes([value])+bytes(words*4-1) for _,value in rows);(folder/'readback.bin').write_bytes(raw)
        entries=[dict(name=n,input_sha256=blocks.digest(('input:'+n).encode()),native_sha256=blocks.digest(('native:'+n).encode()),output_sha256=blocks.digest(bytes([value])+bytes(words*4-1))) for n,value in rows]
        report=dict(calculation_verified=True,mismatches=[],input_count=len(rows),output_sha256=blocks.digest(raw),entries=entries)
        (folder/'comparison.json').write_text(json.dumps(report));return folder,blocks.digest((folder/'comparison.json').read_bytes())

    def test_retention_rehashes_reordered_cases_and_new_cases(self):
        old,old_sha=self.capture('old',[('first',0),('last',2)])
        new,new_sha=self.capture('new',[('last',2),('additional',3),('first',0)])
        r=blocks.retain(old,old_sha,new,new_sha,case_words=1048576)
        self.assertTrue(r['all_reference_cases_retained']);self.assertEqual(r['retained_cases'],2);self.assertEqual(r['retained_output_bytes'],2*1048576*4);self.assertEqual(r['added'],['additional']);self.assertEqual(r['gpu_calls'],0);self.assertFalse(r['calculation_verified'])

    def test_retention_reports_changed_and_missing_cases(self):
        old,old_sha=self.capture('old',[('first',0),('last',2)])
        new,new_sha=self.capture('new',[('first',1)])
        r=blocks.retain(old,old_sha,new,new_sha,case_words=1048576)
        self.assertFalse(r['all_reference_cases_retained']);self.assertEqual(r['missing'],['last']);self.assertEqual(r['changed'],[dict(name='first',fields=['output_sha256'])]);self.assertEqual(r['retained_cases'],0)

    def test_retention_rejects_anchors_forged_case_hashes_and_duplicate_names(self):
        folder,h=self.capture('capture',[('first',0),('last',2)])
        with self.assertRaisesRegex(ValueError,'anchor SHA'):blocks.capture_fingerprints(folder,'0'*64,1048576)
        path=folder/'comparison.json';report=json.loads(path.read_text());report['entries'][0]['output_sha256']='0'*64;path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError,'actual readback'):blocks.capture_fingerprints(folder,blocks.digest(path.read_bytes()),1048576)
        report['entries'][1]['name']='first';path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError,'duplicate'):blocks.capture_fingerprints(folder,blocks.digest(path.read_bytes()),1048576)

    def test_retention_cli_fails_closed_after_preserving_differences(self):
        old,old_sha=self.capture('old',[('first',0)])
        new,new_sha=self.capture('new',[('first',1)]);out=self.root/'retention.json'
        with patch('builtins.print'),self.assertRaises(SystemExit) as failed:
            blocks.main(['retain','--reference-capture',str(old),'--reference-comparison-sha256',old_sha,'--candidate-capture',str(new),'--candidate-comparison-sha256',new_sha,'--case-words','1048576','--out',str(out)])
        self.assertEqual(failed.exception.code,2);self.assertFalse(json.loads(out.read_text())['all_reference_cases_retained'])
        self.assertEqual((old/'readback.bin').read_bytes()[0],0);self.assertEqual((new/'readback.bin').read_bytes()[0],1)


    def test_expanded_stride_retains_exact_prefix_and_requires_zero_extra_words(self):
        old,old_sha=self.capture('prefix-old',[('first',7)],words=1507328)
        new,new_sha=self.capture('prefix-new',[('first',7)],words=1769472)
        r=blocks.retain(old,old_sha,new,new_sha,case_words=1769472,reference_case_words=1507328)
        self.assertTrue(r['all_reference_cases_retained']);self.assertEqual(r['retained_output_bytes'],1507328*4);self.assertTrue(r['appended_tail_required_zero'])
        for offset,field in [(1769472*4-1,'nonzero_appended_tail'),(16,'output_prefix_sha256')]:
            raw=bytearray((new/'readback.bin').read_bytes());raw[offset]=1;(new/'readback.bin').write_bytes(raw)
            report=json.loads((new/'comparison.json').read_text());report['output_sha256']=blocks.digest(raw);report['entries'][0]['output_sha256']=blocks.digest(raw);(new/'comparison.json').write_text(json.dumps(report));h=blocks.digest((new/'comparison.json').read_bytes())
            diff=blocks.retain(old,old_sha,new,h,case_words=1769472,reference_case_words=1507328)
            self.assertFalse(diff['all_reference_cases_retained']);self.assertIn(field,diff['changed'][0]['fields'])
            raw[offset]=0;(new/'readback.bin').write_bytes(raw)
    def test_expanded_stride_rejects_wrong_full_anchor_and_reverse_prefix(self):
        old,old_sha=self.capture('small',[('first',0)],words=1507328);new,new_sha=self.capture('large',[('first',0)],words=1769472)
        with self.assertRaises(ValueError):blocks.retain(old,old_sha,new,'0'*64,case_words=1769472,reference_case_words=1507328)
        with self.assertRaises(ValueError):blocks.retain(new,new_sha,old,old_sha,case_words=1507328,reference_case_words=1769472)
if __name__=='__main__':unittest.main()
