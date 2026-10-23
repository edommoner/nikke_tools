"""State-store contracts, separate from complete battle GPU admission."""
import array,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('damage_core_adapter',ROOT/'research/verify-damage-accum-core-short.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
class CoreTests(unittest.TestCase):
    def test_native_overlay_diagnostic_survives_cp932_default(self):
        spec=importlib.util.spec_from_file_location('overlay_encoding_contract',ROOT/'research/characterize-world-overlays.py')
        overlay=importlib.util.module_from_spec(spec);spec.loader.exec_module(overlay)
        original=Path.write_text
        with tempfile.TemporaryDirectory() as directory:
            saved=Path(directory)/'diagnostic.json'
            def write(path,data,*args,**kwargs):
                if path.name=='overlay-native-full-before-assert.json':
                    # Simulate the Windows default and preserve real Unicode
                    # witness data; dropping/ASCII-escaping it is not the fix.
                    return original(saved,data,*args,**dict({'encoding':'cp932'},**kwargs))
                return original(path,data,*args,**kwargs)
            with patch.object(Path,'write_text',write):rows=overlay.full_simulations()
            self.assertEqual(len(rows),7);self.assertTrue(all(r['passed'] for r in rows))
            text=saved.read_text(encoding='utf-8');self.assertIn('수냉',text)
            self.assertEqual(json.loads(text),rows)

    def test_native_methods_cover_fixed_state_contracts(self):
        rows,_=adapter.prepare();answers={c['name'].split('/')[-1]:adapter.native_reference(c) for _,_,c in rows if c is not None}
        def take(name):return [v for v in answers[name]['operations'] if v['op']==3]
        self.assertEqual(take('split-truncation')[0]['integer'],1126)
        self.assertEqual(take('first-active-done-shadows')[1]['integer'],0)
        self.assertEqual(take('negative-split-packet')[0]['integer'],-450)
        self.assertEqual(take('lost-hp41')[0]['integer'],369)
        self.assertEqual(take('live-lost-hp')[0]['integer'],369)
        self.assertEqual(take('ordered-cancellation')[0]['integer'],9)
        self.assertEqual(take('separate-rate-groups')[0]['integer'],9)
        self.assertEqual(answers['dealt-before-received']['operations'][2]['full'],[[2,0],[1,0]])
        self.assertEqual(answers['dealt-before-received']['operations'][2]['done'],3)
        self.assertEqual(take('refresh-clears')[0]['integer'],0)
        self.assertEqual(take('archived')[0]['integer'],900)
        self.assertEqual(take('epsilon-inside')[0]['integer'],900)
        self.assertFalse(any(v.get('full') for v in answers['epsilon-outside']['operations']))
    def test_packing_is_static_and_bounded(self):
        import portable_backend
        with patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')),patch.object(adapter,'native_reference',side_effect=AssertionError('No runtime values in inputs')):
            rows,data=adapter.prepare()
        self.assertEqual(len(rows),41);self.assertEqual(sum(c is not None for _,_,c in rows),34);self.assertEqual(len(data),4+41*512*4)
    def test_saved_metal_blocks_and_fault_injection(self):
        fixture=json.loads((ROOT/'tests/fixtures/portable-damage-accum-core-raw.json').read_text())
        from portable_backend import source_hashes
        self.assertEqual(fixture['source_sha256'],source_hashes('gpu/damage_accum_probe.slang'))
        entries,_=adapter.prepare()
        for row in fixture['records']:
            block=array.array('I',[0])*786432
            for i,value in row['nonzero']:block[i]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),row['output_sha256'])
            name,_,domain=entries[row['index']];self.assertEqual(name,row['name'])
            if domain is None:
                adapter.validate_rejection(block,name);block[2]^=1
                with self.assertRaises(AssertionError):adapter.validate_rejection(block,name)
                continue
            adapter.compare(block,domain)
            amount=next(16+i*24 for i in range(domain['capacity']) if block[16+i*24+22]&255 in (13,14,16))
            faults=[('quantity',amount)]
            if row['index']==16:faults.append(('notice',1024+2*32+6))
            if row['index']==25:faults.append(('emission',1024+3*32+24))
            if block[8]:faults.append(('cycle',16+(block[8]-1)*24+7))
            for fault,offset in faults:
                corrupt=array.array('I',block)
                if fault=='cycle':corrupt[offset]=block[8]
                else:corrupt[offset]^=1
                with self.subTest(case=name,fault=fault),self.assertRaises(AssertionError):adapter.compare(corrupt,domain)
    def test_new_battle_family_requires_private_world(self):
        from portable_damage_accum_cases import fixtures
        from portable_runtime import validate_effect
        c=fixtures()[0]
        for effect in c['effects'][1:]:
            with self.assertRaises(ValueError):validate_effect(effect,combat=c['combat'],world_frame=False)
if __name__=='__main__':unittest.main()
