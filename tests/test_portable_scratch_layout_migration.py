"""Byte conservation rejects changed math/state even with updated raw hashes."""
import array,hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_scratch_layout_migration import compare_captures
from portable_scratch_layout_source_contract import ledger


class ScratchMigrationTests(unittest.TestCase):
    def fixture(self, root):
        a=array.array('I',[0])*786432;a[12]=123
        a[770982]=0x46414331;a[770984]=1;a[773055]=17
        a[773056]=0x4e515231;a[773058]=64
        for i in range(64):a[773088+i*136+4]=1;a[773088+i*136+135]=i+1
        a[781792]=0x4f485331;a[781855]=99
        b=array.array('I',a);b[770976:781856]=array.array('I',[0])*(781856-770976)
        b[258576:260656]=a[770976:773056];b[785440:785472]=a[773056:773088]
        b[248600:252952]=a[773088:777440];b[518336:522688]=a[777440:781792]
        b[785472:785536]=a[781792:781856]
        sources=ledger(ROOT)['sources'];empty=hashlib.sha256(b'').hexdigest()
        for label,block in (('before',a),('after',b)):
            p=root/label;p.mkdir();data=array.array('I',[1]+[0]*104400).tobytes();(p/'input.bin').write_bytes(data)
            source={n:r['baseline_sha256' if label=='before' else 'current_sha256'] for n,r in sources.items() if label!='before' or r['baseline_sha256']!=empty}
            (p/'evidence.json').write_text(json.dumps(dict(source_sha256=source)))
            raw=block.tobytes();(p/'readback.bin').write_bytes(raw)
            row=dict(name='fixture',input_sha256=hashlib.sha256(data[4:]).hexdigest(),native_sha256=hashlib.sha256(b'native').hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest())
            (p/'comparison.json').write_text(json.dumps(dict(calculation_verified=True,entries=[row],input_sha256=hashlib.sha256(data).hexdigest(),output_sha256=row['output_sha256'])))
        return root/'before',root/'after'

    def test_maximum64_cell_relocation_preserves_every_live_dictionary(self):
        with tempfile.TemporaryDirectory() as folder:
            old,new=self.fixture(Path(folder));r=compare_captures(ROOT,old,new)
            self.assertTrue(r['passed']);self.assertEqual((r['cases'],r['full_live_dictionary_cells_verified']),(1,64))

    def test_changed_body_cache_header_history_or_unallocated_word_is_rejected(self):
        for at in (12,258576+2079,785440+5,518336+4351,785472+63,253951):
            with self.subTest(at=at),tempfile.TemporaryDirectory() as folder:
                old,new=self.fixture(Path(folder));b=array.array('I');b.frombytes((new/'readback.bin').read_bytes());b[at]^=1
                raw=b.tobytes();(new/'readback.bin').write_bytes(raw);c=json.loads((new/'comparison.json').read_text())
                c['output_sha256']=c['entries'][0]['output_sha256']=hashlib.sha256(raw).hexdigest();(new/'comparison.json').write_text(json.dumps(c))
                with self.assertRaises(AssertionError):compare_captures(ROOT,old,new)

    def test_source_or_input_changes_cannot_be_labelled_a_layout_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            old,new=self.fixture(Path(folder));c=json.loads((new/'evidence.json').read_text());c['source_sha256']['unreviewed.slang']='0'*64
            (new/'evidence.json').write_text(json.dumps(c))
            with self.assertRaises(ValueError):compare_captures(ROOT,old,new)
        with tempfile.TemporaryDirectory() as folder:
            old,new=self.fixture(Path(folder));raw=bytearray((new/'input.bin').read_bytes());raw[4]^=1;(new/'input.bin').write_bytes(raw)
            with self.assertRaises(AssertionError):compare_captures(ROOT,old,new)


if __name__=='__main__':unittest.main()
