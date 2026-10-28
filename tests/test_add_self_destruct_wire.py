"""Private final-shot declarations preserve original inputs and shared owners."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator.boss_pattern import BossScript
from portable_coordinate_original_cases import prepare_case
from portable_add_self_destruct_cases import fixtures
from portable_add_self_destruct_wire import compile_battle,check_schema,LAYOUT as S
from portable_add_attack_battle_wire import LAYOUT as A
from portable_add_self_destruct_source_contract import project_sources


class AddSelfDestructWireTests(unittest.TestCase):
    def test_original_definitions_owners_and_literal_delays_pack_without_cpu_state(self):
        from portable_coordinate_kind_admission import KindAdmission
        for c in fixtures():
            _,p=prepare_case(c);before=copy.deepcopy(p)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU scheduler in input')):
                words,meta,bindings,_=compile_battle(p,c['logical_geometry'])
            self.assertEqual(p,before);self.assertEqual(len(words),S['INPUT_WORDS'])
            self.assertEqual(len(p['effects']),76 if c['contract']['scenario'].startswith('EH-') else 70)
            self.assertFalse(meta['add_self_destruct']['CPU_schedule_as_input'])
            self.assertEqual(KindAdmission(ROOT,'gpu/world_add_self_destruct_entry.slang').inspect(words)['unsupported'],[])
            for node,row in enumerate(c['patterns']):
                if row['kind']!='summon':continue
                at=A['BASE']+A['ROW_BASE']+node*24
                self.assertEqual(words[at+4],1)
                import struct
                self.assertEqual(struct.unpack('<d',struct.pack('<II',*words[at+5:at+7]))[0],row['spec']['attack_at'])

    def test_default_add_and_graph_compilers_still_reject_self_destruct(self):
        from portable_add_attack_battle_wire import compile_battle as old
        c=fixtures()[0];_,p=prepare_case(c)
        with self.assertRaises(ValueError):old(p,c['logical_geometry'])

    def test_finite_shots_required_and_readback_arena_is_disjoint(self):
        from portable_backend import validate_composed_stride
        c=fixtures()[0];c['body']['enemy']['patterns'][0]['spec']['attack']['hits']=0
        c['patterns'][0]['spec']['attack']['hits']=0
        with self.assertRaises(ValueError):
            _,p=prepare_case(c);compile_battle(p,c['logical_geometry'])
        check_schema(ROOT);self.assertEqual(S['OUTPUT_BASE'],A['OUTPUT_BASE']+A['MAP_BASE']+A['MAP_ROWS']*2)
        self.assertLessEqual(S['OUTPUT_BASE']+S['HEADER']+S['ROWS']*S['ROW_WORDS'],S['OUTPUT_WORDS'])
        validate_composed_stride('gpu/world_add_self_destruct_entry.slang',S['INPUT_WORDS'],S['OUTPUT_WORDS'])
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_add_self_destruct_entry.slang',S['INPUT_WORDS']+1,S['OUTPUT_WORDS'])

    def test_every_exact_inverse_and_added_dependency_rejects_tampering(self):
        ledger=json.loads((ROOT/'tests/fixtures/portable-add-self-destruct-source-delta.json').read_text());old=project_sources(ROOT)
        for name,row in ledger['files'].items():self.assertEqual(old[name],row['before'])
        for name in [*ledger['files'],*ledger['added_sources']]:
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
        from portable_logical_geometry_source_contract import project_sources as historical
        self.assertIn('gpu/world_frame_runtime.slang',historical(ROOT))

    def test_common_cursor_comparer_checks_unshot_generations(self):
        spec=importlib.util.spec_from_file_location('self_cursor_compare',ROOT/'research/verify-add-attack-battle.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        block=[0]*S['OUTPUT_WORDS'];block[A['OUTPUT_BASE']]=0x41444231
        state=A['OUTPUT_BASE']+A['STATE_BASE'];block[state:state+2]=[2,0]
        domain=({}, {},[SimpleNamespace(kind=5)])
        n=dict(queued_add_attacks=[],firing_cursors=[[2,0]])
        with patch.object(m.base,'compare_observed',return_value=n):
            self.assertEqual(m.compare_observed(block,domain,n,[]),n)
            block[state+1]=1
            with self.assertRaises(AssertionError):m.compare_observed(block,domain,n,[])

    def test_owned_receipts_accept_real_uint32_arrays_and_reject_corruption(self):
        import array
        from portable_specs import LIMITS as L
        from portable_add_self_destruct_wire import MAGIC
        spec=importlib.util.spec_from_file_location('self_receipt_compare',ROOT/'research/verify-add-self-destruct.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        block=array.array('I',[0])*S['OUTPUT_WORDS'];h=S['OUTPUT_BASE'];at=h+S['HEADER'];frame=L['WORLD_FRAME_OUTPUT_BASE'];record=frame+2832
        block[h:h+3]=array.array('I',[MAGIC,1,1]);block[at:at+8]=array.array('I',[0,1,1,1,0,0,0,1])
        block[frame+2]=1;block[record:record+3]=array.array('I',[5,0,1])
        native=dict(self_destruct=[dict(time=0.,node=0,slot=1,generation=1,fired=1)])
        for words in (block,list(block)):
            clean=m.compare_retirements(words,native);self.assertEqual(clean[h:h+3],[0,0,0]);self.assertEqual(clean[record:record+3],[5,0,1])
        for offset in (record,h+2,at+12):
            with self.subTest(offset=offset),self.assertRaises(AssertionError):
                broken=array.array('I',block);broken[offset]=99;m.compare_retirements(broken,native)

    def test_current_proof_and_cache_profile_share_one_calculation(self):
        from portable_readiness_semantics import enemy_ammo_prerequisites
        from portable_backend import source_hashes
        r=enemy_ammo_prerequisites()['declared_add_self_destruct_validation'];raw=(ROOT/r['evidence']).read_bytes();proof=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['evidence_sha256']);self.assertTrue(proof['calculation_verified'])
        self.assertEqual((proof['input_count'],proof['native_cases'],proof['gpu_calls']),(14,8,0))
        golden_raw=(ROOT/'research/portable-add-self-destruct-v1-expected.json').read_bytes();golden=json.loads(golden_raw)
        self.assertEqual(golden['source_sha256'],source_hashes(r['source']));self.assertEqual(golden['output_sha256'],proof['output_sha256'])
        cert=json.loads((ROOT/'research/portable-compiler-full--add-self-destruct-source-certificate.json').read_text())
        self.assertEqual(cert['baseline_golden_sha256'],hashlib.sha256(golden_raw).hexdigest())
        sys.path.insert(0,str(ROOT/'scripts'));import nikke_gpu
        normal=nikke_gpu.SUITES['add-self-destruct'];cached=nikke_gpu.SUITES['add-self-destruct-cache-only']
        for key in ('script','source','golden','inputs','native','input_words','output_words'):self.assertEqual(normal[key],cached[key])
        self.assertTrue(cached['require_paired_generation']);self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        self.assertFalse(r['ammo_connected']);self.assertFalse(r['cuda_verified']);self.assertFalse(r['default_producer_installed'])

    def test_source_audit_keeps_utf8_under_a_cp932_default_locale(self):
        read=Path.read_text
        def cp932_default(path,*args,**kwargs):
            kwargs.setdefault('encoding','cp932');return read(path,*args,**kwargs)
        with patch.object(Path,'read_text',cp932_default):restored=project_sources(ROOT)
        self.assertIn('gpu/world_frame_runtime.slang',restored)


if __name__=='__main__':unittest.main()
