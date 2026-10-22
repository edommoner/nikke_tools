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
        def changed(*args):
            result=original(*args);self.path.write_bytes(bytes([1])+self.raw[1:]);return result
        with patch.object(blocks,'scan',side_effect=changed),self.assertRaisesRegex(ValueError,'changed while sampling'):blocks.compare(self.path,self.sha,self.index)
    def test_index_anchor_and_existing_output_are_not_overwritten(self):
        index=self.root/'index.json';blocks.write(index,self.index);out=self.root/'result.json'
        with self.assertRaisesRegex(ValueError,'index SHA'):blocks.main(['compare','--readback',str(self.path),'--sha256',self.sha,'--index',str(index),'--index-sha256','0'*64,'--out',str(out)])
        self.assertFalse(out.exists());out.write_text('original')
        with self.assertRaises(FileExistsError):blocks.write(out,{})
        self.assertEqual(out.read_text(),'original')


if __name__=='__main__':unittest.main()
