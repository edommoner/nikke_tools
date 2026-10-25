"""Squad literals and native recipient selection remain distinct from packing."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from portable_squad_control_specs import pack,normalize,empty,INPUT_WORDS
from portable_coordinate_squad_cases import fixtures
from world_frame_native import roster_names
from world_coordinate_manual_native import observe

class SquadLiteralTests(unittest.TestCase):
    def test_pure_packing_stable_equal_time_order_and_no_battle(self):
        c=fixtures()[0];names=roster_names(c)
        seq=[dict(t=.4,action='cover_all',duration=.2),dict(t=.2,action='focus',target=names[1]),dict(t=.2,action='cover_all')]
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle in packing')):
            rows=normalize(seq,names);wire=pack(seq,names)
        self.assertEqual([r['kind'] for r in rows],[1,2,2]);self.assertEqual(len(wire),INPUT_WORDS);self.assertEqual(len(empty()),INPUT_WORDS)
    def test_strict_wire_and_historical_projection(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride('gpu/world_coordinate_squad_entry.slang',109792,1769856)
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_coordinate_squad_entry.slang',109656,1769856)
        from portable_coordinate_policy_source_contract import project_sources,project_backend_source
        self.assertIn('gpu/world_charge_control_runtime.slang',project_sources(ROOT))
        self.assertIn('MAX_OUTPUT_WORDS=1769472',project_backend_source(ROOT))
    def test_policy_composition_uses_shared_state_validator_without_legacy_repacking(self):
        import importlib.util,array
        spec=importlib.util.spec_from_file_location('squad_comparison_test',ROOT/'research/verify-coordinate-squad-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
        c=next(c for c in fixtures() if c['name'].endswith('/policy-composition'));domain=(c,{},None,{})
        block=array.array('I',[0])*a.OUTPUT_WORDS;h=a.SQUAD_BASE;block[h:h+4]=array.array('I',[a.MAGIC,1,1,1])
        native=dict(manual_actions=dict(characters=[dict(cover_all=False) for _ in range(5)]),squad_control=dict(sequence_index=1,last_keep=0,forced_owner=0))
        words=[0]*a.INPUT_WORDS;words[109530]=1
        with patch.object(a,'compile_case',return_value=(words,None,None,None)),patch.object(a.parent.parent,'compare',return_value=native) as manual,patch.object(a.parent,'compare_policy_state') as policy,patch.object(a.parent,'compile_case',side_effect=AssertionError('Legacy packing cannot parse squad actions')):
            self.assertIs(a.compare(block,domain),native)
            self.assertIs(manual.call_args.args[1],domain);self.assertIs(policy.call_args.args[1],native);self.assertEqual(policy.call_args.args[2],1)
    def test_invalid_literals_rejected(self):
        names=roster_names(fixtures()[0])
        for seq in [[dict(action='cover_all',duration=-1)],[dict(action='cover_all',duration=float('nan'))],[dict(action='focus',target='unknown')],[dict(action='fire')],[dict(action='cover_all',recipients=31)],[dict(t=True,action='cover_all')],[dict(action='cover_all')]*17]:
            with self.subTest(seq=seq),self.assertRaises(ValueError):pack(seq,names)
    def test_canonical_cover_all_excludes_live_or_forced_owner_without_camera_request(self):
        names=['no-owner','forced-owner','live-owner','cover-before-focus','focus-before-cover','release-focus','blocked']
        expected={'no-owner':[0,1,2,3,4],'forced-owner':[0,1,3,4],'live-owner':[0,2,3,4],'cover-before-focus':[0,1,2,3,4],'focus-before-cover':[0,1,3,4],'release-focus':[0,1,3,4],'blocked':[0,2,3,4]}
        for c in fixtures():
            label=c['name'].split('/')[-1]
            if label not in names:continue
            with self.subTest(case=label):
                n,_=observe(c);events=n['manual_actions']['events']
                entered=[e['owner'] for e in events if e['kind']=='_enter_cover' and e['time']>=.2 and e['cover_all']]
                self.assertEqual(entered,expected[label])
                # A non-owner squad cover never independently requests a camera.
                self.assertEqual([r['owner'] for r in n['manual_actions']['characters']],[0,1,2,3,4])
                if label in ('no-owner','blocked'):self.assertEqual(set(r['owner'] for r in n['squad_control']['pumps']),{-1})
                self.assertEqual(n['squad_control']['sequence_index'],len(c['sequence']))
