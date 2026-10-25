"""Original definitions remain intact across packing and native observation."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_test_adapter',ROOT/'research/verify-coordinate-original-short.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class OriginalTests(unittest.TestCase):
    def test_existing_complete_input_bytes_are_unchanged(self):
        import engine_worker
        from portable_projectile_roster_input import compile_projectile_battle
        rows=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-legacy-inputs.json').read_text())
        for row in rows:
            p=engine_worker.evaluate(dict(row['body'],_portable_static_inputs=True))
            words,meta=compile_projectile_battle(p)
            raw=array.array('I',words)
            if sys.byteorder!='little':raw.byteswap()
            self.assertEqual(hashlib.sha256(raw.tobytes()).hexdigest(),row['input_sha256'])
            self.assertEqual(len(meta['effects']),row['bound'])

    def test_all_original_definitions_are_packed_without_simulation(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in input')):
            for row in a.fixtures():
                case,p=a.prepare_case(row);before=copy.deepcopy(p)
                words,meta,_,_=a.compile_coordinate_battle(p)
                self.assertEqual(p,before)
                self.assertEqual(len(words),a.INPUT_WORDS)
                self.assertEqual(words[5],1,'Full skill history is required for original battle comparison')
                self.assertEqual(set(meta['binding_source_indices']),set(range(len(p['effects']))))
                self.assertFalse(meta['coordinate_original_input']['cpu_battle_executed'])

    def test_native_observer_is_local_and_restores_profile_and_definitions(self):
        row=a.fixtures()[0];case,p=a.prepare_case(row);before=copy.deepcopy(p)
        words,meta,b,d=a.compile_coordinate_battle(p);previous=sys.getprofile()
        n=a.native_reference((case,meta,b,d))
        self.assertIs(sys.getprofile(),previous)
        self.assertEqual(p,before)
        _,after=a.prepare_case(row)
        self.assertEqual(after,before,'Observer labels must never enter shared parsed definitions')
        self.assertEqual(n['original_input_identity']['definitions'],len(p['effects']))
        self.assertFalse(n['original_input_identity']['authored_delays_overrides'])
        self.assertFalse(n['original_input_identity']['authored_metadata_overrides'])
        self.assertTrue(n['landed_packets'])

    def test_native_rejects_changed_original_seed_before_simulating(self):
        case,p=a.prepare_case(a.fixtures()[0]);_,m,b,d=a.compile_coordinate_battle(p)
        case['original_run']['prepared']['policies']['seed']+=1
        from calculator import timeline
        forbidden=Mock(side_effect=AssertionError('Changed original must not run'))
        forbidden.__code__=timeline.simulate.__code__
        with patch.object(timeline,'simulate',new=forbidden):
            with self.assertRaisesRegex(ValueError,'Original input identity changed: seed'):
                a.native_reference((case,m,b,d))

    def test_ambiguous_damage_labels_fail_closed(self):
        _,p=a.prepare_case(a.fixtures()[0]);damage=next(e for e in p['effects'] if e['effect'].get('type')=='damage')
        p['effects'].append(copy.deepcopy(damage))
        with self.assertRaisesRegex(ValueError,'owner-aware'):
            a.compile_coordinate_battle(p)

if __name__=='__main__':unittest.main()
