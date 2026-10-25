"""Complete ordered proof retains clocks, raw capacity and bounded ownership."""
import array,hashlib,json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_coordinate_packet_history as h
def fixture(count):
    rows=[[i%5,0,0,1,*struct.unpack('<II',struct.pack('<d',i/60)),*struct.unpack('<II',struct.pack('<d',float(12345+i))),0,0,0,0] for i in range(count)]
    flat=[v for row in rows for v in row];digest=list(struct.unpack('>8I',hashlib.sha256(struct.pack('<'+'I'*len(flat),*flat)).digest()));pending=len(flat)%16
    pad=[int.from_bytes(v.to_bytes(4,'little'),'big') for v in flat[len(flat)-pending:]] if pending else []
    pad+=[0x80000000];pad+=[0]*(14-len(pad));pad.extend([0,count*384])
    state=[h.MAGIC,1,count,4096,12,1048576,1,pending,*digest,*pad,*digest,*(rows[-1] if count>4096 else [0]*12),*[0]*12]
    block=array.array('I',[0])*(h.HEAD+h.WORDS);retained=min(count,4096);block[h.CP['BASE']+2]=retained;block[h.CP['TRACE']:h.CP['TRACE']+retained*12]=array.array('I',flat[:retained*12]);block[h.HEAD:]=array.array('I',state)
    return block,rows
class PacketHistoryTests(unittest.TestCase):
    def test_complete_stream_empty_and_raw_boundary(self):
        for count in (0,1,4096,4097):
            with self.subTest(count=count):
                block,rows=fixture(count);r=h.verify(block,rows);self.assertEqual(r['records'],count);self.assertEqual(r['streamed_records'],max(0,count-4096))
        self.assertEqual(h.expected([])[2],'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    def test_tampered_prefix_full_hash_clock_and_metadata_are_rejected(self):
        block,rows=fixture(4097)
        for at in (h.CP['BASE']+2,h.CP['TRACE']+4,h.HEAD+2,h.HEAD+5,h.HEAD+32,h.HEAD+52):
            bad=array.array('I',block);bad[at]^=1
            with self.subTest(at=at),self.assertRaises(ValueError):h.verify(bad,rows)
        rows[-1][4]^=1
        with self.assertRaises(ValueError):h.verify(block,rows)
        with self.assertRaises(ValueError):h.expected([rows[0]]*(h.MAX_RECORDS+1))
    def test_clear_tail_ownership_schema_and_exact_legacy_inverse(self):
        self.assertEqual(h.audit_arena()['raw_prefix_capacity'],4096);self.assertLessEqual(h.HEAD+h.WORDS,1310720)
        self.assertEqual((ROOT/'gpu/coordinate_packet_history_layout.slang').read_text(),h.schema())
        from portable_coordinate_original_packet_history_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-packet-history-source-delta.json').read_text());out=project_sources(ROOT)
        for name,row in data['sources'].items():self.assertEqual(out[name],row['baseline'])
        for name in data['added_sources']:self.assertNotIn(name,out)
        name='gpu/coordinate_skill_runtime.slang'
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
if __name__=='__main__':unittest.main()
