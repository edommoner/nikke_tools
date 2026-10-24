import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('packet_integer_adapter',ROOT/'research/verify-packet-integer-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_packet_integer_specs import check_schema,LAYOUT
from portable_normal_spread_specs import check_schema as check_spread

class PacketIntegerTests(unittest.TestCase):
    def test_exact_sum_and_round_once_before_any_float_product(self):
        cases={n:(v,m) for n,v,m in a.fixtures()}
        values,m=cases['lost-units'];exact=sum(map(int,values))*m
        running=0.
        for v in values:running+=v
        self.assertNotEqual(running,float(exact))
        values,m=cases['multiply-before-round']
        self.assertNotEqual(float(sum(map(int,values)))*m,float(sum(map(int,values))*m))

    def test_schema_bounds_and_python_integer_cancellation(self):
        check_schema(ROOT);check_spread(ROOT)
        self.assertEqual(LAYOUT['TERMS'],128)
        for name,values,m in a.fixtures():
            total=sum(map(int,values))*m
            self.assertLess(total,2**80)
            for muzzles in [1,2,3,8]:self.assertEqual((total*muzzles)/muzzles,float(total),name)

    def test_oracle_compares_all_words_and_rejects_inactive_tail(self):
        rows,raw=a.prepare();self.assertEqual(len(rows),305)
        self.assertEqual(sum(d is not None for _,_,d in rows),294)
        self.assertEqual(len(raw),4+len(rows)*a.INPUT_WORDS*4)
        for name,w,d in rows:
            if d is None:continue
            e=a.native_reference(d);n=int(e['exact_integer'])
            block=[0,LAYOUT['MAGIC'],n&0xffffffff,(n>>32)&0xffffffff,(n>>64)&0xffffffff,(n>>96)&0xffffffff,*e['rounded_bits']]
            a.compare(block,d)
            for at in range(8):
                changed=list(block);changed[at]^=1
                with self.assertRaises(AssertionError):a.compare(changed,d)

    def test_reviewed_quantity_inverse_rejects_every_unregistered_source_edit(self):
        import json
        from portable_coordinate_quantity_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-coordinate-quantity-source-delta.json').read_text())
        projected=project_sources(ROOT)
        for name,row in data['sources'].items():self.assertEqual(projected[name],row['baseline'])
        for name in [*data['sources'],*data['added_sources']]:
            with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed edit\n'})

if __name__=='__main__':unittest.main()
