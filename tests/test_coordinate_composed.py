"""Composition is a shared battle entry with independent legacy and group proofs."""
import hashlib,importlib.util,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from calculator import timeline
from calculator.boss_pattern import BossScript
spec=importlib.util.spec_from_file_location('composed_test',ROOT/'research/verify-coordinate-composed-short.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)


class CoordinateComposedTests(unittest.TestCase):
    def test_static_lowering_retains_all88_world_scene_and_area_bytes_without_battles(self):
        with patch.object(suite,'native_reference',side_effect=AssertionError('No native packing')),patch.object(timeline,'simulate',side_effect=AssertionError('No battle packing')),patch.object(BossScript,'hit_target',side_effect=AssertionError('No landing packing')):
            entries,_=suite.prepare();old,_=suite.parent.prepare()
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(97,81))
        for (name,words,_),(oldname,before,_) in zip(entries[:88],old,strict=True):
            self.assertEqual(name,oldname)
            self.assertEqual(words[:104400]+words[104408:],before)

    def test_native_body_groups_and_coordinate_packets_share_a_frame(self):
        for case in suite.fixtures():
            words,meta,bindings,desc=suite.compile_case(case)
            native=suite.native_reference(('coexist',(case,meta,bindings,desc)))
            self.assertGreaterEqual(len(native['groups']),3)
            self.assertEqual({row['packets'] for row in native['group_shots']},{case['combat']['weapons'][case['group_owner']]['pellets']*case['combat']['weapons'][case['group_owner']]['muzzles']})
            self.assertTrue(set(row['time'] for row in native['groups']) & set(row['time'] for row in native['coordinate_packets']))

    def test_enlarged_transport_requires_registered_source_and_exact_input_stride(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride(suite.SOURCE,108648,1310720)
        for source,words in [('gpu/world_attack_group_entry.slang',108648),(suite.SOURCE,108640)]:
            with self.subTest(source=source,words=words),self.assertRaises(ValueError):validate_composed_stride(source,words,1310720)
        with self.assertRaises(ValueError):validate_composed_stride(suite.SOURCE,108648,1048576)

    def test_only_composed_coordinate_include_graph_owns_resident_runtime(self):
        import re
        from portable_slang_generation import source_hashes
        pattern=rb'^\s*#define\s+PORTABLE_RESIDENT_RUNTIME(?:\s|$)'
        for source,wanted in [(suite.SOURCE,True),(suite.parent.SOURCE,False)]:
            actual=any(re.search(pattern,(ROOT/name).read_bytes(),re.M) for name in source_hashes(ROOT,source))
            self.assertEqual(actual,wanted)

    def test_saved_readback_index_accepts_full_composed_shape_without_executing_gpu(self):
        from portable_readback_blocks import scan,validate
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'raw.bin';raw=bytes(1310720*4);path.write_bytes(raw)
            row=scan(path,hashlib.sha256(raw).hexdigest(),case_words=1310720,include_case_hashes=True)
            validate(row);self.assertEqual(row['cases'],1);self.assertEqual(len(row['case_sha256']),1)


if __name__=='__main__':unittest.main()
