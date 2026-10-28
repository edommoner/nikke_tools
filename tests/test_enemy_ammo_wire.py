"""Resource ownership, original effect lowering and guarded source contracts."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator.boss_pattern import BossScript,validate
from portable_specs import LIMITS as L
from portable_coordinate_original_cases import prepare_case
from portable_enemy_ammo_cases import fixtures
from portable_enemy_ammo_wire import LAYOUT as E,compile_enemy_ammo,pack,check_schema
from portable_enemy_ammo_source_contract import project_sources


class EnemyAmmoWireTests(unittest.TestCase):
    def test_literal_lowering_keeps_all76_effects_owners_and_never_ticks(self):
        for c in fixtures():
            _,p=prepare_case(c);before=copy.deepcopy(p)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU state in wire')):
                w,m,b,s=compile_enemy_ammo(p,c['logical_geometry'],c['enemy_ammo'])
            self.assertEqual(p,before);self.assertEqual(len(p['effects']),76);self.assertEqual(len(w),117632)
            self.assertEqual(w[E['BASE']:E['BASE']+4],[0x45414d31,1,len(c['enemy_ammo']),len(b)])
            self.assertEqual(w[L['RECIPIENT_BASE']+8:L['RECIPIENT_BASE']+16],[4,0,0,0,0,0,1,0])
            self.assertFalse(m['enemy_ammo_declarations']['CPU_state_or_schedule_as_input'])
            from portable_coordinate_kind_admission import KindAdmission
            self.assertEqual(KindAdmission(ROOT,'gpu/world_enemy_ammo_entry.slang').inspect(w)['unsupported'],[])
            self.assertEqual({r['kind'] for r in KindAdmission(ROOT,'gpu/world_add_attack_battle_entry.slang').inspect(w)['unsupported']},{11})

    def test_declared_order_is_preserved_without_replacing_enemy_selection_order(self):
        c=fixtures()[0];_,p=prepare_case(c);rules=list(reversed(c['enemy_ammo']))
        _,_,b,_=compile_enemy_ammo(p,c['logical_geometry'],rules)
        bank=pack(rules,validate(c['patterns'],coord=True),b)
        lookup={r.label:i+1 for i,r in enumerate(b)}
        self.assertEqual(bank[E['ORDER_BASE']:E['ORDER_BASE']+len(rules)],[lookup[r['label']] for r in rules])

    def test_default_admission_and_other_enemy_ammo_operators_stay_closed(self):
        import portable_runtime
        effect=dict(type='instant',stat='ammo_charge_pct',target='all_enemies')
        with self.assertRaises(portable_runtime.UnsupportedPortable):portable_runtime.validate_effect(effect,combat={},world_frame=True)
        from enemy_ammo_model import validate_enemy_effects
        for stat in ('max_ammo_pct','ammo_charge_flat','force_reload','infinite_ammo'):
            with self.subTest(stat=stat),self.assertRaises(ValueError):validate_enemy_effects([(dict(effect,stat=stat),'caster')],['caster'])

    def test_every_actual_attack_needs_its_declared_resource_owner(self):
        c=fixtures()[0];_,p=prepare_case(c)
        with self.assertRaisesRegex(ValueError,'Every attacking ADD'):compile_enemy_ammo(p,c['logical_geometry'],c['enemy_ammo'][:1])

    def test_exact_inverse_composes_with_old_add_and_healing_audits(self):
        ledger=json.loads((ROOT/'tests/fixtures/portable-enemy-ammo-source-delta.json').read_text());old=project_sources(ROOT)
        for name,row in ledger['files'].items():self.assertEqual(old[name],row['before'])
        for name in [*ledger['files'],*ledger['added_sources']]:
            with self.subTest(path=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
        from portable_logical_geometry_source_contract import project_sources as logical
        self.assertIn('gpu/ammo_instant_runtime.slang',logical(ROOT))

    def test_resource_arena_starts_after_add_map_and_fits_the_old_output(self):
        from portable_add_attack_battle_wire import LAYOUT as A
        from portable_backend import validate_composed_stride
        check_schema(ROOT)
        self.assertEqual(E['OUTPUT_BASE'],A['OUTPUT_BASE']+A['MAP_BASE']+A['MAP_ROWS']*2)
        self.assertEqual(E['HISTORY_BASE'],E['STATE_BASE']+E['ROWS']*E['STATE_WORDS'])
        self.assertEqual(E['EVENT_BASE'],E['HISTORY_BASE']+E['HISTORIES']*E['HISTORY_WORDS'])
        self.assertLessEqual(E['OUTPUT_BASE']+E['EVENT_BASE']+E['EVENTS']*E['EVENT_WORDS'],E['OUTPUT_WORDS'])
        self.assertEqual(E['RESOURCE_BASE'],E['EVENT_BASE']+E['EVENTS']*E['EVENT_WORDS'])
        self.assertLessEqual(E['OUTPUT_BASE']+E['RESOURCE_BASE']+(E['RESOURCE_CAPACITY']-128)*8,E['OUTPUT_WORDS'])
        validate_composed_stride('gpu/world_enemy_ammo_entry.slang',117632,2032000)
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_add_attack_battle_entry.slang',117632,2032000)

    def test_enemy_and_allied_consumers_use_identical_numeric_functions(self):
        s=(ROOT/'gpu/enemy_ammo_runtime.slang').read_text()
        self.assertIn('prepareAmmoInstant(13,d.value,flat,fraction)',s)
        self.assertIn('ammoInstantResult(13,capacity,int(before),flat,fraction,after)',s)
        self.assertNotIn('f64ToI64',s)

    def test_resource_history_crosses_prefix_without_losing_or_ignoring_receipts(self):
        from portable_enemy_ammo_readback import compare_resources
        block=[0]*E['OUTPUT_WORDS'];count=129;header=L['RESOURCE_HEADER_BASE'];tail=E['OUTPUT_BASE']+E['RESOURCE_BASE']
        block[header:header+2]=[count,count];expected=[]
        for i in range(count):
            at=L['RESOURCE_TRACE_BASE']+i*8 if i<128 else tail+(i-128)*8
            block[at:at+4]=[26,0,0,0];expected.append(dict(event=26,owner=0,resource='g',time=0.0,boundary=0.0))
        domain=(dict(names=['caster'],effects=[]),dict(resource_names=['g'],binding_source_indices=[]))
        native=dict(original_resources=dict(ordered_notifications=expected,final={},dispatches=[]))
        projected=compare_resources(block,domain,native)
        self.assertEqual(projected[header:header+2],[128,129]);self.assertFalse(any(projected[tail:tail+8]))
        for at in (tail,tail+8):
            with self.subTest(corrupt_word=at),self.assertRaises(AssertionError):
                broken=block.copy();broken[at]=99;compare_resources(broken,domain,native)

    def test_historical_metal_evidence_retains_exact_reviewed_source_inverse(self):
        from portable_readiness_semantics import enemy_ammo_prerequisites
        from portable_backend import source_hashes
        r=enemy_ammo_prerequisites()['declared_enemy_ammo_validation'];raw=(ROOT/r['evidence']).read_bytes();proof=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['evidence_sha256'])
        golden=json.loads((ROOT/'research/portable-enemy-ammo-v1-expected.json').read_text())
        # Final-shot hooks changed the shared source closure after this proof.
        # Preserve the historical golden; only the reviewed exact inverse may
        # establish retention, without claiming a current-source recertification.
        from portable_add_self_destruct_source_contract import project_sources as before_self
        previous=before_self(ROOT)
        actual=source_hashes(r['source'])
        projected={name:hashlib.sha256(previous[name].encode()).hexdigest() if name in previous else digest for name,digest in actual.items()}
        self.assertEqual(projected,golden['source_sha256'])
        self.assertEqual(proof['output_sha256'],golden['output_sha256']);self.assertTrue(proof['calculation_verified'])
        self.assertEqual((proof['input_count'],proof['native_cases'],proof['gpu_calls']),(20,6,0))
        self.assertFalse(r['cuda_verified']);self.assertFalse(r['default_producer_installed'])


if __name__=='__main__':unittest.main()
