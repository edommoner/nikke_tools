"""Physical entry wiring and full-battle packet comparisons, before GPU proof."""
import importlib.util,sys,unittest,struct
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('physical_gpu_adapter',ROOT/'research/verify-coordinate-physical-short.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
from portable_coordinate_physical_specs import LAYOUT,check_schema,audit_arena

class PhysicalTests(unittest.TestCase):
    def test_shared_integrator_only_changes_input_address_space(self):
        check_schema(ROOT);plan=audit_arena(ROOT)
        self.assertTrue(plan['requires_disabled_attack_group_owner_mask'])
        self.assertLessEqual(plan['scratch_end'],1048576)
        source=(ROOT/'gpu/coordinate_landing_v1.slang').read_text()
        generated=(ROOT/'gpu/coordinate_landing_resident_v1.slang').read_text().split('\n',1)[1]
        self.assertEqual(generated,source.replace('commands[','results['))

    def test_packing_contains_only_literal_shapes_not_probabilities_or_packets(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No CPU oracle during packing')), \
             patch('coordinate_landing_reference.landing',side_effect=AssertionError('No CPU landing during packing')):
            rows,raw=a.prepare()
        self.assertEqual(len(rows),23)
        self.assertEqual(len(raw),4+len(rows)*a.INPUT_WORDS*4)
        self.assertEqual(sum(d is not None for _,_,d in rows),17)
        self.assertTrue(all(w[104402]==0 for _,w,d in rows if d is not None))

    def test_backend_admission_binds_the_complete_private_wire(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        for source,inputs,outputs in [(a.SOURCE,a.INPUT_WORDS-8,a.OUTPUT_WORDS),
                                      ('gpu/arbitrary_entry.slang',a.INPUT_WORDS,a.OUTPUT_WORDS)]:
            with self.assertRaises(ValueError):validate_composed_stride(source,inputs,outputs)

    def test_historical_projection_does_not_ignore_any_source_edit(self):
        from portable_coordinate_physical_source_contract import project_sources
        import json
        data=json.loads((ROOT/'tests/fixtures/portable-coordinate-physical-source-delta.json').read_text())
        projected=project_sources(ROOT)
        for name,row in data['sources'].items():self.assertEqual(projected[name],row['baseline'])
        for name in [*data['sources'],*data['added_sources']]:
            with self.subTest(name=name),self.assertRaises(AssertionError):
                project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed edit\n'})

    def test_packet_comparison_rejects_damage_extra_and_unused_tail(self):
        rows,_=a.prepare();_,_,domain=rows[1];expected=a.native_reference(domain)
        block=[0]*a.OUTPUT_WORDS;cp=a.CP
        block[cp['BASE']]=0x43534b31;block[cp['BASE']+1]=1;block[cp['BASE']+2]=1
        desc=domain[3]['rows'][0];packet=expected['physical_pellets'][0]['packets'][0]
        block[cp['TRACE']:cp['TRACE']+12]=[0,desc['slot'],desc['kind'],1,0,0,
             *struct.unpack('<II',struct.pack('<d',float(packet['damage']))),0,0,0,0]
        with patch.object(a.codec,'compare_expected',return_value=None):
            a.compare(block,domain)
            for at in [cp['BASE']+2,cp['TRACE']+6,cp['TRACE']+8,cp['TRACE']+12]:
                changed=list(block);changed[at]^=1
                with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(changed,domain)

if __name__=='__main__':unittest.main()
