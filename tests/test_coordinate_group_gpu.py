"""Full coordinate/group ownership and static mixed packing, before dispatch."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
spec=importlib.util.spec_from_file_location('group_adapter',ROOT/'research/verify-coordinate-group-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class CoordinateGroupTests(unittest.TestCase):
    def test_all_old206_inputs_and_native_domains_are_retained_without_oracle_packing(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No simulation in wire')):
            new,raw=a.prepare();old,_=a.parent.prepare()
        self.assertEqual(new[:206],old);self.assertEqual((len(new),sum(d is not None for _,_,d in new)),(225,199));self.assertEqual(len(raw),4+225*a.INPUT_WORDS*4)
    def test_mixed_descriptors_use_real_actor_slots_including_interrupt_after_add(self):
        from portable_specs import LIMITS as L
        from portable_coordinate_scene_specs import LAYOUT as C
        for c in a.fixtures():
            words,m,bindings,desc=a.compile_case(c)
            for i,row in enumerate(desc['rows']):
                slot=row['slot'];binding=bindings[slot]
                self.assertEqual((int(binding.kind),binding.identity),(row['kind'],row['identity']))
                self.assertEqual(words[104408+C['ROW_BASE']+i*C['ROW_WORDS']+5],slot)
    def test_full_capacity_arena_and_both_transport_stride_guards(self):
        from portable_coordinate_group_wire import check_schema,COMPACT_WORDS
        from portable_backend import validate_composed_stride
        plan=check_schema(ROOT);self.assertTrue(plan['address_plan_verified']);self.assertEqual(COMPACT_WORDS,186528)
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        for source,inp,out in [(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS),(a.SOURCE,a.INPUT_WORDS,1310720),('gpu/world_coordinate_control_entry.slang',a.INPUT_WORDS,a.OUTPUT_WORDS)]:
            with self.assertRaises(ValueError):validate_composed_stride(source,inp,out)
    def test_saved_readback_index_accepts_full_group_stride_and_rejects_nearby_size(self):
        import hashlib,tempfile
        from portable_readback_blocks import scan
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'readback.bin';data=bytes(a.OUTPUT_WORDS*4);path.write_bytes(data)
            result=scan(path,hashlib.sha256(data).hexdigest(),case_words=a.OUTPUT_WORDS)
            self.assertEqual(result['cases'],1)
            with self.assertRaises(ValueError):scan(path,hashlib.sha256(data).hexdigest(),case_words=a.OUTPUT_WORDS+1)
    def test_storage_decoder_maps_active_expanded_rows_to_original_source(self):
        decoder=a.physical.codec.storage
        meta=dict(binding_source_indices=[0,0,1],binding_owners=[0,0,3])
        case=dict(effects=[dict(stat='atk_pct'),dict(stat='heal_overcharge_store')],owners=[0,3])
        carriers=[dict(definition=1,active=True),dict(definition=2,active=True,activated=0.,end=1.)]
        with patch('portable_runtime.decode',return_value=dict(carriers=carriers)):
            rows=decoder.decoded_storage([],meta,case)
        self.assertEqual(len(rows),1);self.assertEqual((rows[0]['row'],rows[0]['owner']),(1,3))
    def test_exact_inverse_rejects_runtime_snippet_and_stride_mutation(self):
        from portable_coordinate_group_source_contract import project_sources,project_backend_source
        project_sources(ROOT)
        for name in ['gpu/coordinate_physical_runtime.slang','gpu/attack_group_open.slang','gpu/attack_group_seal.slang','gpu/world_coordinate_group_entry.slang']:
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text().replace('1507328','1507329',1))

if __name__=='__main__':unittest.main()
