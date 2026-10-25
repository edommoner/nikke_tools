"""Original force-reload admission, preserved public controls and strict readers."""
import importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_reload_test',ROOT/'research/verify-coordinate-original-reload-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class OriginalReloadTests(unittest.TestCase):
    def test_complete_definitions_and_literal_public_control_policy(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedules in GPU input')):rows,_=a.prepare()
        self.assertEqual(len(rows),4);old=KindAdmission(ROOT,'gpu/world_coordinate_original_slot_entry.slang');current=KindAdmission(ROOT,a.SOURCE)
        self.assertEqual([len(d[0]['effects']) for _,_,d in rows],[81,81,80,78])
        for _,words,domain in rows:
            c,m,_,_=domain;self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))));self.assertEqual({r['kind'] for r in old.inspect(words)['unsupported']},{23});self.assertEqual(current.inspect(words)['unsupported'],[]);self.assertIs(provider(a,domain)[2],a.native_reference)
        character=rows[1][2][0];self.assertTrue(character['controls'][0]['hold']);self.assertEqual(character['original_run']['body']['shooting_policy'],'character');self.assertNotIn('control',character['original_run']['body']['profile']['chars'][character['names'][0]])

    def test_shared_observer_restores_even_when_native_raises(self):
        from calculator import timeline
        from calculator.buff_manager import BuffManager
        from world_original_reload_native import capture
        before=[timeline.CharState.__init__,timeline.CharState._start_reload,timeline.CharState._finish_reload,BuffManager.register_instant_handler]
        c,_=a.prepare_case(a.fixtures()[0])
        with self.assertRaisesRegex(RuntimeError,'failed native'):
            with capture(c):raise RuntimeError('failed native')
        self.assertEqual(before,[timeline.CharState.__init__,timeline.CharState._start_reload,timeline.CharState._finish_reload,BuffManager.register_instant_handler])

    def test_shared_reload_reader_keeps_reserved_words_strict(self):
        from portable_specs import LIMITS as L
        from portable_reload_observation import readback
        words=[0]*(L['WORLD_RELOAD_TRACE_BASE']+L['WORLD_RELOAD_TRACE_COUNT']*16);h=L['WORLD_RELOAD_HEAD_BASE'];words[h]=0x57524c31
        self.assertEqual(readback(words,{'states':{}})['reload_events'],[])
        words[h+2]=1
        with self.assertRaises(AssertionError):readback(words,{'states':{}})

    def test_exact_source_and_transport_inverse(self):
        from portable_coordinate_original_reload_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_cleanse_source_contract import project_sources as ancestor
        from portable_backend import validate_composed_stride
        fixture=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-reload-source-delta.json').read_text());sources=project_sources(ROOT)
        for name,row in fixture['sources'].items():self.assertEqual(sources[name],row['baseline'])
        self.assertEqual(project_backend_source(ROOT),fixture['transport']['baseline']);self.assertNotIn('gpu/world_coordinate_original_reload_entry.slang',ancestor(ROOT))
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS-1)
if __name__=='__main__':unittest.main()
