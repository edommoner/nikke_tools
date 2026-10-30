"""Independent cover declarations and full receipt checks; no device dispatch."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
import portable_cover_defense_wire as wire
from portable_specs import LIMITS as L,FIELDS as F

class CoverWire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=importlib.util.spec_from_file_location('cover_adapter_test',ROOT/'research/verify-cover-defense-battle.py');cls.adapter=importlib.util.module_from_spec(s);s.loader.exec_module(cls.adapter)
        cls.rows,cls.data=cls.adapter.prepare()
    def test_exact_wire_and_declaration_roundtrip(self):
        wire.check_schema(ROOT)
        self.assertEqual((len(self.rows),len(self.data)),(11,4+11*wire.INPUT*4))
        self.assertEqual(wire.LAYOUT['OUTPUT_BASE']+wire.LAYOUT['RECEIPT_BASE']+512*32,wire.OUTPUT)
        for _,w,d in self.rows[:4]:
            c=d[0];declared=c['cover_defense_case'];bank=w[wire.LAYOUT['BASE']:]
            self.assertEqual(wire.validate(bank,c['names']),declared['cover_defense'])
            self.assertEqual(wire.pack(declared['cover_defense'],c['names']),bank)
            for i in d[1]['cover_defense_declarations']['definition_indices']:
                at=L['DEFINITION_BASE']+i*32
                self.assertEqual((w[at+F['KIND']],w[at+F['STAT']]),(0,wire.STAT))
                self.assertEqual(struct.unpack('<d',struct.pack('<II',*w[at+6:at+8]))[0],128.57)
    def test_wire_negatives_and_complete_backend_registration(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride(wire.SOURCE,wire.INPUT,wire.OUTPUT)
        for source,iw,ow in [(wire.SOURCE,wire.INPUT-1,wire.OUTPUT),(wire.SOURCE,wire.INPUT,wire.OUTPUT-1),('gpu/unknown_cover_entry.slang',wire.INPUT,wire.OUTPUT)]:
            with self.assertRaises(ValueError):validate_composed_stride(source,iw,ow)
        for _,w,_ in self.rows[4:]:
            with self.assertRaises(ValueError):wire.validate(w[wire.LAYOUT['BASE']:],self.rows[0][2][0]['names'])
    def test_default_validation_and_legacy_alias_restore(self):
        import portable_runtime,portable_element_specs
        original=(portable_runtime.validate_effect,portable_element_specs.legacy_effect)
        effect=dict(type='buff',stat='cover_def_pct',fixed_value=10.,target='self',trigger=dict(timing=['battle_start'],condition=[]))
        with self.assertRaises(portable_runtime.UnsupportedPortable):portable_runtime.validate_effect(effect,combat={},world_frame=True)
        with self.assertRaisesRegex(RuntimeError,'intentional'):
            with wire.compiler_policy():
                portable_runtime.validate_effect(effect,combat={},world_frame=True)
                self.assertEqual(portable_element_specs.legacy_effect(effect)['stat'],'')
                for change in (dict(scaling='stack_count'),dict(type='instant'),dict(tick_interval=1.)):
                    with self.assertRaises(ValueError):portable_runtime.validate_effect(dict(effect,**change),combat={},world_frame=True)
                with self.assertRaises(ValueError):portable_runtime.validate_effect(effect,combat=None,world_frame=False)
                raise RuntimeError('intentional')
        self.assertEqual(original,(portable_runtime.validate_effect,portable_element_specs.legacy_effect))
        self.assertEqual(effect['stat'],'cover_def_pct')
    def test_every_receipt_word_snapshot_and_unused_tail_is_checked(self):
        import json
        saved=json.loads((ROOT/'tests/fixtures/cover-defense-battle-cpu-v1.json').read_text())['cases'][0]
        n=saved['native'];block=[0]*wire.OUTPUT;h=wire.LAYOUT['OUTPUT_BASE'];block[h:h+2]=[wire.MAGIC,len(n['cover_defense']['receipts'])]
        names=saved['case']['contract']['names'];domain=({'names':names},)
        for i,r in enumerate(n['cover_defense']['receipts']):
            at=h+wire.LAYOUT['RECEIPT_BASE']+i*32;block[at:at+2]=[names.index(r['name']),r['divisor']]
            for offset,key in [(2,'time'),(4,'attack'),(6,'coefficient'),(8,'received_snapshot'),(10,'base_defense'),(12,'effective_defense'),(14,'quantity'),(16,'shared_quantity'),(18,'hp_before'),(20,'applied'),(22,'hp_after')]:block[at+offset:at+offset+2]=struct.unpack('<II',struct.pack('<d',r[key]))
        self.adapter.compare_receipts(block,domain,n)
        for offset in (0,2,16,527,528,529,530,534,540,548,552,len(block)-h-1):
            block[h+offset]^=1
            with self.subTest(offset=offset),self.assertRaises(AssertionError):self.adapter.compare_receipts(block,domain,n)
            block[h+offset]^=1
    def test_registered_profile_keeps_same_inputs_and_bounded_cached_cuda_route(self):
        import nikke_gpu
        config=nikke_gpu.SUITES['cover-defense-battle']
        self.assertFalse(config['development_only']);self.assertEqual(config['native'],4);self.assertEqual(config['inputs'],11)
        self.assertEqual((config['input_words'],config['output_words']),(wire.INPUT,wire.OUTPUT))
        cached=nikke_gpu.SUITES['cover-defense-battle-cache-only']
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1');self.assertTrue(cached['require_paired_generation'])
        for key in ('source','script','golden','inputs','native','input_words','output_words'):self.assertEqual(cached[key],config[key])

    def test_exact_source_inverse_keeps_earlier_guards(self):
        import hashlib,json
        from portable_cover_defense_source_contract import project_sources,LEDGER_SHA256
        path=ROOT/'tests/fixtures/portable-cover-defense-source-delta.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),LEDGER_SHA256)
        ledger=json.loads(path.read_text());result=project_sources(ROOT)
        for name,row in ledger['files'].items():self.assertEqual(hashlib.sha256(result[name].encode()).hexdigest(),row['before_sha256'])
        from portable_recipient_order_source_contract import project_sources as prior,BEFORE_BACKEND_SHA256
        self.assertEqual(hashlib.sha256(prior(ROOT)['app/portable_backend.py'].encode()).hexdigest(),BEFORE_BACKEND_SHA256)

    def test_snapshot_input_reader_fault_fails_before_native_or_device_work(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'gpu').mkdir()
            (root/'gpu/cover_defense_layout.slang').write_text(wire.shader_schema())
            source=(ROOT/'gpu/cover_defense_runtime.slang').read_text()
            for operand in ('snapshot','snapshot+2','snapshot+4'):
                bad=source.replace('protectionNumber('+operand+')','loadNumber('+operand+')')
                self.assertNotEqual(bad,source)
                (root/'gpu/cover_defense_runtime.slang').write_text(bad)
                with self.assertRaisesRegex(ValueError,'output-resource reads'):wire.check_schema(root)

if __name__=='__main__':unittest.main()
