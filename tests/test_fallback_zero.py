"""Ordinary canonical semantics, complete resource history, and device-free packing."""
import array,copy,json,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_detail as product,portable_backend,engine_worker
from portable_enemy_ammo_wire import LAYOUT as E
from portable_product_resource_budget import notification_bound,SUPPLY_OUTPUT_WORDS
from portable_specs import LIMITS as L
from portable_resource_decode import resource_readback

class FallbackZeroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.requests=json.loads((ROOT/'tests/fixtures/fallback-zero-ordinary-v1.json').read_text())

    def test_original_four_pack_before_cpu_or_device_and_preserve_every_definition(self):
        for request in self.requests:
            body=copy.deepcopy(request['body']);before=copy.deepcopy(body)
            with self.subTest(name=request['name']),patch.object(engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle input')),patch.object(portable_backend,'execute',side_effect=AssertionError('No device')):
                prepared,_=product.prepare(body);original=copy.deepcopy(prepared)
                source,iw,ow,words,meta=product.compile_product(prepared)
                portable_backend.validate_composed_stride(source,iw,ow)
                self.assertEqual(len(words),iw);self.assertEqual(body,before);self.assertEqual(prepared,original)
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(prepared['effects']))))
                if 'product_named_carriers' in meta:
                    self.assertFalse(meta['product_named_carriers']['no_matching_definition_names'])
                    self.assertEqual(len(meta['product_named_carriers']['source_indices']),2)
                elif 'product_cover_defense' in meta:
                    self.assertEqual(words[115680:115684],[0x43444231,1,5,2])
                    self.assertTrue(meta['product_cover_defense']['ordinary_body_quantity'])
                    self.assertEqual(meta['product_cover_defense']['declarations'],{})
                else:
                    self.assertEqual((ow,words[E['BASE']+1]),(SUPPLY_OUTPUT_WORDS,3))
                    self.assertEqual(meta['product_enemy_ammo']['notification_supply_bound'],774000)
                    self.assertGreaterEqual(128+(ow-E['OUTPUT_BASE']-E['RESOURCE_BASE'])//8,774000)
                    packed=array.array('I',[1]+words).tobytes()
                    portable_backend.validate_product_ammo_versions(source,packed,iw,ow,1)
                    for width in (E['OUTPUT_WORDS'],2064786,ow-1):
                        with self.assertRaises(ValueError):portable_backend.validate_product_ammo_versions(source,packed,iw,width,1)

    def test_supply_bound_accepts_only_proven_integral_sources_and_consumers(self):
        prepared,_=product.prepare(self.requests[2]['body']);self.assertEqual(notification_bound(prepared),774000)
        charge=next(i for i,r in enumerate(prepared['effects']) if r['effect'].get('stat')=='gauge_charge')
        consume=next(i for i,r in enumerate(prepared['effects']) if r['effect'].get('stat')=='gauge_consume_as_ammo')
        for index,changes in ((charge,{'fixed_value':.5}),(charge,{'values':{'1':6000}}),(charge,{'tick_interval':1.}),(charge,{'trigger':{'timing':['on_attack']}}),(consume,{'fixed_value':-2}),(consume,{'scaling':'stack_count'})):
            bad=copy.deepcopy(prepared);bad['effects'][index]['effect'].update(changes)
            with self.subTest(changes=changes):self.assertIsNone(notification_bound(bad))
        bad=copy.deepcopy(prepared);bad['effects'][charge]['effect']['trigger']['timing']=['every_stack:bag:1']
        self.assertIsNone(notification_bound(bad))
        bad=copy.deepcopy(prepared);bad['effects'].append(dict(owner='any',effect=dict(stat='force_skill_use')))
        self.assertIsNone(notification_bound(bad))

    def test_resource_tail_decodes_past_failed_capture_and_still_rejects_overflow(self):
        words=array.array('I',[0])*SUPPLY_OUTPUT_WORDS;count=19223;h=L['RESOURCE_HEADER_BASE']
        words[h]=words[h+1]=count
        for i in range(count):
            at=L['RESOURCE_TRACE_BASE']+i*8 if i<128 else E['OUTPUT_BASE']+E['RESOURCE_BASE']+(i-128)*8
            words[at]=26;words[at+4:at+6]=array.array('I',struct.unpack('<II',struct.pack('<d',i/120)))
        meta=dict(resource_names=['bag'],product_enemy_ammo=dict(output_words=SUPPLY_OUTPUT_WORDS))
        number=lambda at:struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
        result=resource_readback(words,meta,L,number)
        self.assertEqual(result['resource_trace_total'],count);self.assertEqual(len(result['resource_trace']),count)
        self.assertEqual(result['resource_trace'][-1]['time'],(count-1)/120)
        words[h]=words[h+1]=129+(SUPPLY_OUTPUT_WORDS-E['OUTPUT_BASE']-E['RESOURCE_BASE'])//8
        with self.assertRaisesRegex(RuntimeError,'complete product resource history'):resource_readback(words,meta,L,number)
        self.assertIn('s.error = 8; return;', (ROOT/'gpu/resource_runtime.slang').read_text())

    def test_declared_cover_quantity_is_still_required_with_attacks(self):
        body=copy.deepcopy(self.requests[1]['body'])
        body['reference_models']={'enemy_ammo':[]}
        # The cover compiler must reject an absent independent base even before
        # validating another declared consumer's wire.
        prepared,_=product.prepare(self.requests[1]['body']);prepared['reference_models']=body['reference_models']
        from portable_product_cover import compile_product
        with self.assertRaisesRegex(product.UnsupportedPortable,'explicit reference_models.cover_defense'):
            compile_product(prepared,lambda p:self.fail('Refusal must precede lowering'))
        # Mode1 remains unavailable even if a forged input reaches a landing;
        # only the new ordinary mode2 bypasses the independent quantity reader.
        source=(ROOT/'gpu/cover_defense_runtime.slang').read_text()
        self.assertIn('if(commands[s.inputBase+PORTABLE_COVER_DEFENSE_INPUT_BASE+3]!=0){s.error=64;return 0;}',source)
        source=(ROOT/'gpu/protection_runtime.slang').read_text()
        self.assertIn('if(commands[s.inputBase+PORTABLE_COVER_DEFENSE_INPUT_BASE+3]==2)',source)

if __name__=='__main__':unittest.main()
