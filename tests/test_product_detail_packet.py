"""Product packet admission and full response comparison without GPU calls."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('product_packet',ROOT/'research/verify-product-detail.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

from historical_engine_reference import historical_compiler

class ProductPacket(unittest.TestCase):
    def test_typed_skill_decoder_uses_exact_static_coefficient_without_research_imports(self):
        import builtins,struct
        from portable_world_result import read_typed_battle
        block=[0]*1048576;block[786432]=0x44425431;block[786433]=1
        block[789250]=1;block[789251]=1;block[789252]=1
        at=790000;block[at:at+4]=[1,0,0,1];block[at+10]=1
        for offset,value in [(4,1.),(6,3.),(8,7.),(22,2.)]:
            block[at+offset:at+offset+2]=struct.unpack('<II',struct.pack('<d',value))
        block[at+16:at+22]=[0,2,10,1,1,0]
        case=dict(typed_bindings=[{}],max_attacks=128,effects=[dict(target='all_projectiles')],owners=[0])
        meta=dict(binding_source_indices=[0]);original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name in ('world_frame_native','world_authored_roster'):
                raise ImportError('Research module deliberately unavailable')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=guarded):
            result=read_typed_battle(block,(case,meta,()),sampled_coefficients=[3.])
            with self.assertRaises(AssertionError):
                read_typed_battle(block,(case,meta,()),sampled_coefficients=[4.])
        self.assertEqual(result['attacks'][0]['damage'],7.)
        self.assertEqual(result['attacks'][0]['receipts'][0]['took'],2.)

    def test_weapon_only_typed_decoder_has_no_research_import_dependency(self):
        import builtins,struct
        from portable_world_result import read_typed_battle
        block=[0]*1048576;block[786432]=0x44425431
        block[789250]=1;block[789251]=1;block[789252]=1
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name in ('world_frame_native','world_authored_roster','destructible_skill_specs'):
                raise ImportError('Research module deliberately unavailable')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=guarded):
            result=read_typed_battle(block,(dict(typed_bindings=[],max_attacks=128),{},()))
        self.assertEqual(result,dict(time=0.,finished=True,state=[],attacks=[]))

    def test_stationary_world_clock_must_survive_gpu_readback(self):
        from portable_detail import validate_world_frame_readback
        from portable_specs import LIMITS as L
        from portable_runtime import UnsupportedPortable
        base=L['WORLD_FRAME_OUTPUT_BASE'];block=[0]*(base+788)
        meta={'product_world_frame_contract':{'nodes':2}}
        with self.assertRaisesRegex(UnsupportedPortable,'clock readback'):
            validate_world_frame_readback(block,meta)
        block[base+1]=1;block[base+784]=32;validate_world_frame_readback(block,meta)
        block[base+16]=1
        with self.assertRaisesRegex(UnsupportedPortable,'clock readback'):
            validate_world_frame_readback(block,meta)

    def test_generated_mutation_snapshot_guard_rejects_the_saved_cuda_failure(self):
        from portable_slang_generation import validate_counter_snapshots
        for field in ('removalCount','carrierCount'):
            for op in ('>','<','>=','<='):
                with self.subTest(field=field,op=op),self.assertRaisesRegex(ValueError,'reflexive'):
                    validate_counter_snapshots('if((_S9502->'+field+'_0) '+op+' (_S9502->'+field+'_0)) {}')
        validate_counter_snapshots('if((_S9502->removalCount_0) > begin_4) {}')
        validate_counter_snapshots('if((_S9502->removalCount_0) > (_S9000->removalCount_0)) {}')



    def test_same_original_static_input_and_source_without_battle(self):
        with patch.object(adapter.product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in preparation')):
            rows,raw=adapter.prepare()
        self.assertEqual(len(rows),1)
        self.assertEqual(len(raw),4*(1+adapter.suite.INPUT))
        self.assertFalse(rows[0][2][1]['cpu_battle_executed'])
        self.assertEqual(adapter.SOURCE,'gpu/product_battle_entry.slang')
        golden=json.loads((ROOT/'research/portable-product-detail-v1-expected.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),golden['input_sha256'])
    def test_full_comparison_includes_provenance_and_all_product_fields(self):
        for field in ('total_damage','warnings','burst_timeline','evaluator'):
            expected={field:1};actual={field:2}
            with patch.object(adapter,'native_reference',return_value=expected),patch.object(adapter.product,'decode_payload',return_value=actual):
                with self.assertRaisesRegex(ValueError,field):adapter.compare([0]*adapter.suite.OUTPUT,({},None,None,None))
        with patch.object(adapter,'native_reference') as native:
            with self.assertRaisesRegex(ValueError,'Complete'):adapter.compare([],None)
            native.assert_not_called()
        for expected,actual in [({'control':None},{}),({}, {'control':None})]:
            with patch.object(adapter,'native_reference',return_value=expected),patch.object(adapter.product,'decode_payload',return_value=actual):
                with self.assertRaisesRegex(ValueError,'control'):adapter.compare([0]*adapter.suite.OUTPUT,({},None,None,None))
    def test_persistent_hash_ignores_only_environment_vcs_stamp(self):
        a={'evaluator':{'commit':'a'},'total_damage':42,'warnings':['original']}
        b=copy.deepcopy(a);b['evaluator']['commit']='unpacked'
        self.assertEqual(adapter.fingerprint(a),adapter.fingerprint(b))
        for field,value in [('total_damage',43),('warnings',[])]:
            b=copy.deepcopy(a);b[field]=value
            self.assertNotEqual(adapter.fingerprint(a),adapter.fingerprint(b))

if __name__=='__main__':unittest.main()
