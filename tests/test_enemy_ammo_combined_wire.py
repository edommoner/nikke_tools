"""Disjoint ownership, unchanged originals and strict opt-in composition."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator.boss_pattern import BossScript,validate
from portable_coordinate_original_cases import prepare_case
from portable_enemy_ammo_self_destruct_cases import fixtures
from portable_enemy_ammo_self_destruct_wire import LAYOUT,compile_battle,check_schema
from portable_enemy_ammo_wire import LAYOUT as E,pack


class CombinedWireTests(unittest.TestCase):
    def test_all_originals_lower_without_runtime_state_and_old_packer_stays_closed(self):
        from portable_coordinate_kind_admission import KindAdmission
        for case in fixtures():
            _,prepared=prepare_case(case);before=copy.deepcopy(prepared)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU schedule in input')):
                words,meta,bindings,_=compile_battle(prepared,case['logical_geometry'],case['enemy_ammo'])
            self.assertEqual(before,prepared);self.assertEqual(len(words),117632);self.assertEqual(len(prepared['effects']),76)
            self.assertFalse(meta['enemy_ammo_declarations']['CPU_state_or_schedule_as_input'])
            self.assertEqual(KindAdmission(ROOT,'gpu/world_enemy_ammo_self_destruct_entry.slang').inspect(words)['unsupported'],[])
            with self.assertRaisesRegex(ValueError,'Self-destruct'):pack(case['enemy_ammo'],validate(case['patterns'],coord=True),bindings)

    def test_ownership_and_stride_are_shared_without_overlap(self):
        from portable_backend import validate_composed_stride
        check_schema(ROOT)
        self.assertEqual(LAYOUT['OUTPUT_BASE'],E['OUTPUT_BASE']+E['RESOURCE_BASE']+(E['RESOURCE_CAPACITY']-128)*8)
        self.assertLessEqual(LAYOUT['OUTPUT_BASE']+LAYOUT['HEADER']+LAYOUT['ROWS']*LAYOUT['ROW_WORDS'],E['OUTPUT_WORDS'])
        validate_composed_stride('gpu/world_enemy_ammo_self_destruct_entry.slang',117632,2032000)
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_enemy_ammo_self_destruct_entry.slang',116464,2032000)

    def test_strict_inverse_composes_and_rejects_every_dependency_mutation(self):
        from portable_enemy_ammo_combined_source_contract import project_sources
        ledger=json.loads((ROOT/'tests/fixtures/portable-enemy-ammo-combined-source-delta.json').read_text())
        old=project_sources(ROOT)
        for name,row in ledger['files'].items():self.assertEqual(old[name],row['before'])
        for name in [*ledger['files'],*ledger['added_sources']]:
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
        from portable_enemy_ammo_source_contract import project_sources as historical
        self.assertIn('gpu/ammo_instant_runtime.slang',historical(ROOT))

    def test_full_case_and_raw_rejection_inventory(self):
        spec=importlib.util.spec_from_file_location('combined_wire_verifier',ROOT/'research/verify-enemy-ammo-self-destruct.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);rows,raw=m.prepare()
        self.assertEqual((len(rows),len(raw)),(16,4+16*117632*4))
        self.assertEqual(len({name for name,_,_ in rows}),16)
        for name,words,domain in rows[:8]:
            with self.subTest(case=name):self.assertEqual(len(domain[0]['effects']),76)
        self.assertTrue(all(domain is None for _,_,domain in rows[8:]))

    def test_independent_receipt_golden_certificate_and_declared_scope(self):
        from portable_readiness_semantics import enemy_ammo_prerequisites
        r=enemy_ammo_prerequisites()['declared_enemy_ammo_self_destruct_validation']
        raw=(ROOT/r['evidence']).read_bytes();receipt=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['evidence_sha256'])
        golden=json.loads((ROOT/'research/portable-enemy-ammo-self-destruct-v1-expected.json').read_text())
        certificate=json.loads((ROOT/'research/portable-compiler-full--enemy-ammo-self-destruct-source-certificate.json').read_text())
        for key in ('source_sha256','generated_normalized'):self.assertEqual(certificate[key],golden[key])
        self.assertEqual(certificate['baseline_golden_sha256'],hashlib.sha256((ROOT/'research/portable-enemy-ammo-self-destruct-v1-expected.json').read_bytes()).hexdigest())
        self.assertEqual(certificate['proof_kind'],'compiler-source-only')
        self.assertFalse(certificate['calculation_verified']);self.assertIsNone(certificate['input_sha256'])
        self.assertTrue(receipt['calculation_verified']);self.assertEqual((receipt['input_count'],receipt['native_cases'],receipt['gpu_calls']),(16,8,0))
        self.assertFalse(receipt['live_parent_receipt_present'])
        self.assertEqual(receipt['input_sha256'],golden['input_sha256']);self.assertEqual(receipt['output_sha256'],golden['output_sha256'])
        spec=importlib.util.spec_from_file_location('combined_proof_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        from portable_source_baseline import check
        self.assertTrue(check(ROOT,cli,'enemy-ammo-self-destruct')['verified'])
        self.assertTrue(r['metal_verified']);self.assertFalse(r['cuda_verified']);self.assertFalse(r['default_producer_installed'])


if __name__=='__main__':unittest.main()
