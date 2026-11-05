"""Composition regressions from the six exact optimizer requests."""
import array,copy,json,hashlib,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_detail as product
from portable_specs import LIMITS as L,FIELDS as F
from portable_enemy_ammo_wire import LAYOUT as E
from portable_product_resource_budget import output_words,SUPPLY_OUTPUT_WORDS
from portable_optimizer_six_source_contract import preimages,historical_bytes,ledger

class OptimizerSixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.requests=json.loads((ROOT/'tests/fixtures/optimizer-six-v1.json').read_text())

    def test_six_compositions_preserve_definitions_without_cpu_battle_input(self):
        for body in self.requests:
            with self.subTest(squad=body['squad']),patch.object(product.engine_worker.sim,'execute',side_effect=AssertionError('CPU must not prepare GPU input')):
                prepared,_=product.prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
                from portable_backend import validate_composed_stride,validate_product_ammo_versions
                validate_composed_stride(source,iw,ow)
                self.assertEqual(prepared,original);self.assertEqual(len(words),iw)
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                if '벨벳' in body['squad']:
                    self.assertEqual(ow,SUPPLY_OUTPUT_WORDS);self.assertEqual(words[E['BASE']+1],3)
                    self.assertIsNone(meta['product_enemy_ammo']['notification_supply_bound'])
                    validate_product_ammo_versions(source,struct.pack('<'+'I'*(iw+1),1,*words),iw,ow,1)
                elif '스노우 화이트 : 헤비암즈' in body['squad']:
                    for i in meta['product_ordinary_lock']['projectile_return_indices']:
                        row=meta['binding_source_indices'].index(i);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                        self.assertEqual(words[at+F['DAMAGE_FLAGS']],1048576|524288)
                elif '페퍼' in body['squad']:
                    self.assertEqual((source,iw,ow),('gpu/product_named_carriers_fixed_group_battle_entry.slang',104408,1048576))
                    for i in meta['product_named_carriers']['source_indices']:
                        row=meta['binding_source_indices'].index(i);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                        self.assertIn(words[at+F['STAT']],(93,94));self.assertEqual(words[at+F['KIND']],0)
                else:
                    rows=[row for row,i in enumerate(meta['binding_source_indices']) if prepared['effects'][i]['effect'].get('land_in_full_burst')]
                    self.assertEqual(len(rows),2)
                    for row in rows:self.assertEqual(words[L['MODE_BASE']+row*L['MODE_WORDS']+17],0x46424c31)

    def test_unknown_mixed_supply_raises_capacity_only_for_ammo_notification_producer(self):
        prepared={'effects':[{'effect':{'stat':'gauge_charge','type':'instant','target':'self','fixed_value':1,'trigger':{'timing':['on_attack']}}}]}
        self.assertEqual(output_words(prepared,2064786),(2064786,None))
        prepared['effects'].append({'effect':{'stat':'gauge_consume_as_ammo','fixed_value':100}})
        self.assertEqual(output_words(prepared,2064786),(SUPPLY_OUTPUT_WORDS,None))

    def test_native_stack_union_preserves_its_descriptor_and_padding_guards(self):
        import portable_native
        if not portable_native.availability(ROOT)['available']:self.skipTest('Native compiler unavailable')
        from portable_backend import execute
        body=copy.deepcopy(next(b for b in self.requests if '크라운' in b['squad']));body['duration']=3
        prepared,_=product.prepare(body);source,iw,ow,words,meta=product.compile_product(prepared)
        row=next(row for row,i in enumerate(meta['binding_source_indices']) if prepared['effects'][i]['effect'].get('land_in_full_burst'))
        at=L['MODE_BASE']+row*L['MODE_WORDS'];cases=[words]
        for offset in (17,18,6):
            bad=list(words);bad[at+offset]=1;cases.append(bad)
        packed=array.array('I',[len(cases),*(word for case in cases for word in case)]).tobytes()
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'readback.bin'
            _,evidence=execute(source,'portableEvents',packed,iw,ow,'native',readback_path=output)
            raw=array.array('I');raw.frombytes(output.read_bytes())
        self.assertTrue(evidence['native_execution_verified'])
        self.assertEqual([raw[i*ow] for i in range(len(cases))],[0,64,64,64])

    def test_exact_source_history_inverse_and_fail_closed_mutation(self):
        data=ledger(ROOT);old=preimages(ROOT)
        for name in data['files']:
            from portable_removed_sources import REMOVED_SOURCES
            if name in REMOVED_SOURCES:continue
            text=old[name]
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),data['files'][name]['before_sha256'])
            with self.assertRaisesRegex(ValueError,'Unreviewed Unit 6'):historical_bytes(ROOT,name,(ROOT/name).read_bytes()+b' ')
        for name,digest in data['added_sources'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'tests/fixtures';dest.mkdir(parents=True);(dest/'portable-optimizer-six-source-delta.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'ledger changed'):ledger(tmp)

if __name__=='__main__':unittest.main()
