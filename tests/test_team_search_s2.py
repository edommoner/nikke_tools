"""Exact S1 fallback compositions; real native guards and existing model wiring."""
import array,copy,json,struct,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_detail as product
from portable_specs import LIMITS as L,FIELDS as F
from portable_backend import validate_composed_stride,validate_product_ammo_versions
from portable_product_resource_budget import SUPPLY_OUTPUT_WORDS

class TeamSearchS2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=json.loads((ROOT/'tests/fixtures/team-search-s2-v1.json').read_text())
        cls.base=fixture['base'];cls.cases={c['id']:c for c in fixture['cases']}

    def compile(self,id,duration=None):
        body=dict(self.base,squad=self.cases[id]['squad'])
        if duration is not None:body['duration']=duration
        pr,_=product.prepare(body);original=copy.deepcopy(pr)
        result=product.compile_product(pr);self.assertEqual(pr,original)
        source,iw,ow,words,meta=result
        self.assertEqual(len(words),iw)
        self.assertEqual(set(meta['binding_source_indices']),set(range(len(pr['effects']))))
        validate_composed_stride(source,iw,ow)
        return pr,result

    def test_all_54_compositions_preserve_complete_definitions_and_checked_wires(self):
        for id in self.cases:
            with self.subTest(id=id):
                pr,(source,iw,ow,words,meta)=self.compile(id)
                if 'product_enemy_ammo' in meta:
                    validate_product_ammo_versions(source,array.array('I',[1,*words]).tobytes(),iw,ow,1)
                if id in (234,273,530):self.assertEqual(ow,SUPPLY_OUTPUT_WORDS)
                if 'product_ordinary_lock' in meta:
                    for index in meta['product_ordinary_lock']['projectile_return_indices']:
                        row=meta['binding_source_indices'].index(index)
                        self.assertTrue(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']]&1048576)

    def test_ammo_weighted_bank_ownership_and_version_fail_closed(self):
        from portable_weighted_battle_wire import AMMO_BASE,AMMO_INPUT,LAYOUT as W
        from portable_enemy_ammo_wire import LAYOUT as E
        _,(source,iw,ow,words,meta)=self.compile(530)
        self.assertEqual(iw,AMMO_INPUT);self.assertEqual(AMMO_BASE,E['INPUT_WORDS'])
        self.assertEqual(words[AMMO_BASE],0x57425431)
        self.assertEqual(words[E['BASE']+1],3)
        self.assertTrue(meta['product_weighted_incoming']['unspecified_quantities'])
        with self.assertRaises(ValueError):validate_composed_stride(source,iw-16,ow)
        bad=list(words);bad[E['BASE']+1]=1
        with self.assertRaises(ValueError):validate_product_ammo_versions(source,array.array('I',[1,*bad]).tobytes(),iw,ow,1)
        self.assertEqual((W['OUTPUT']-W['OUTPUT_BASE'])%8,0)

    def test_resource_continuation_skips_weighted_receipts_and_rejects_overflow(self):
        from portable_resource_decode import resource_readback
        from portable_weighted_battle_wire import LAYOUT as W
        from portable_enemy_ammo_wire import LAYOUT as E
        words=array.array('I',[0])*SUPPLY_OUTPUT_WORDS
        gap=W['OUTPUT']-W['OUTPUT_BASE']
        boundary=128+(W['OUTPUT_BASE']-E['OUTPUT_BASE']-E['RESOURCE_BASE'])//8
        count=boundary+1;head=L['RESOURCE_HEADER_BASE']
        words[head]=words[head+1]=count
        for index in range(count):
            at=L['RESOURCE_TRACE_BASE']+index*8 if index<128 else E['OUTPUT_BASE']+E['RESOURCE_BASE']+(index-128)*8
            if index>=boundary:at+=gap
            words[at]=26
        words[W['OUTPUT_BASE']]=0x57425431
        meta=dict(resource_names=['ammo'],product_enemy_ammo=dict(output_words=SUPPLY_OUTPUT_WORDS),product_ammo_weighted=True)
        result=resource_readback(words,meta,L,lambda at:struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0])
        self.assertEqual(len(result['resource_trace']),count)
        capacity=128+(SUPPLY_OUTPUT_WORDS-E['OUTPUT_BASE']-E['RESOURCE_BASE']-gap)//8
        words[head]=words[head+1]=capacity+1
        with self.assertRaisesRegex(RuntimeError,'complete product resource history'):
            resource_readback(words,meta,L,lambda at:0.)

    def test_sugar_secondary_compiler_keeps_existing_element_code_tag(self):
        from portable_element_specs import STAT
        for id in (875,2121):
            pr,(_,_,_,words,meta)=self.compile(id)
            index=next(i for i,r in enumerate(pr['effects']) if r['effect'].get('stat')=='element_code_override')
            row=meta['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
            self.assertEqual(words[at+F['STAT']],STAT)
            self.assertIn('작열',meta['states'])

    def test_real_staged_chain_and_projectile_named_flags_keep_other_guards(self):
        from portable_backend import execute
        import portable_native
        if not portable_native.availability(ROOT)['available']:self.skipTest('Native compiler unavailable')
        for id in (401,2043):
            pr,(source,iw,ow,words,meta)=self.compile(id,3)
            if id==401:
                row=next(row for row,i in enumerate(meta['binding_source_indices']) if pr['effects'][i]['effect'].get('ramp_interval'))
            else:
                index=meta['product_ordinary_lock']['projectile_return_indices'][0];row=meta['binding_source_indices'].index(index)
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']
            bad=list(words);bad[at]|=0x80000000
            packed=array.array('I',[2,*words,*bad]).tobytes()
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'readback.bin';execute(source,'portableEvents',packed,iw,ow,'native',readback_path=path)
                raw=array.array('I');raw.frombytes(path.read_bytes())
            self.assertEqual([raw[0],raw[ow]],[0,64])

if __name__=='__main__':unittest.main()
