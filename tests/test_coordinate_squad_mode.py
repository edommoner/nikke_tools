"""Mode-effect lifetime and native CharState lifetime are different contracts."""
import importlib.util,sys,unittest,copy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from portable_coordinate_squad_mode_cases import fixtures
from portable_squad_mode_specs import INPUT_BASE,MAGIC
from world_coordinate_manual_native import observe
s=importlib.util.spec_from_file_location('squad_mode_test',ROOT/'research/verify-coordinate-squad-mode-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class SquadModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();before=copy.deepcopy(cls.cases);cls.native={c['name'].split('/')[-1]:observe(c)[0] for c in cls.cases};assert cls.cases==before
    def entered(self,label):return {e['owner'] for e in self.native[label]['manual_actions']['events'] if e['kind']=='_enter_cover' and e['cover_all']}
    def test_native_boundary_witnesses(self):
        for label in ['finite-exact','charge-exact','bullet-next-pump','toggle-exact','stunned-exit','revive-mode','entry-wait-exact']:
            with self.subTest(skip=label):self.assertNotIn(0,self.entered(label))
        for label in ['finite-next-frame','finite-later','charge-after','bullet-next-base','toggle-after','stunned-after','revive-base']:
            with self.subTest(enter=label):self.assertIn(0,self.entered(label))
        self.assertNotIn(1,self.entered('two-mode-owners'));self.assertNotIn(4,self.entered('owner4-exact'))
        self.assertFalse(self.entered('no-squad-actions'))
        self.assertTrue(self.native['end-in-mode']['squad_mode_state']['flags'][0])
        self.assertTrue(any(p['mask']&1 for p in self.native['reload-activated']['squad_mode_state']['pumps']))
        shots=[x for x in self.native['reload-activated']['sampled_live_shots'] if x['owner']==0 and x['mode']]
        covers=[x for x in self.native['reload-activated']['manual_actions']['events'] if x['owner']==0 and x['kind']=='_enter_cover']
        self.assertTrue(any(e['time']<shot['time']<e['until'] for e in covers for shot in shots))
        waiting=self.native['reload-activated-entry-wait']
        first_mode=next(s for s in waiting['sampled_live_shots'] if s['owner']==0 and s['mode'])
        reload_end=next(e for e in waiting['manual_actions']['events'] if e['owner']==0 and e['kind']=='_finish_reload')
        self.assertGreater(first_mode['time'],reload_end['time'])
        for label,bound in [('cover-policy-expiry',.6),('cover-policy-expiry-stunned',.8)]:
            entered=[e for e in self.native[label]['manual_actions']['events'] if e['owner']==0 and e['kind']=='_enter_cover']
            self.assertTrue(entered);self.assertGreater(entered[0]['time'],bound)
        forced=self.native['cover-policy-expiry-forced'];entered=next(e for e in forced['manual_actions']['events'] if e['owner']==0 and e['kind']=='_enter_cover')
        self.assertLess(entered['time'],.62);self.assertTrue(next(p['mask'] for p in forced['squad_mode_state']['pumps'] if p['time']==entered['time'])&1)

    def test_pure_versioned_literals_and_complete_wire(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with patch.object(timeline,'simulate',side_effect=AssertionError('No runtime state packing')):
            for c in self.cases:
                w,_,_,_=a.compile_case(c);self.assertEqual(len(w),109792);self.assertEqual(w[INPUT_BASE+1],2);self.assertEqual(w[INPUT_BASE+5],MAGIC)
        for c in self.cases:
            self.assertEqual(len(self.native[c['name'].split('/')[-1]]['squad_mode_state']['flags']),5)
    def test_source_inverse_keeps_old_squad_and_policy_contracts(self):
        from portable_coordinate_squad_source_contract import project_sources,project_backend_source
        self.assertIn('gpu/weapon_frame_phases.slang',project_sources(ROOT));project_backend_source(ROOT)
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/weapon_frame_phases.slang':(ROOT/'gpu/weapon_frame_phases.slang').read_text()+'\n'})
