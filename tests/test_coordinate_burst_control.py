"""Full native battle witnesses, strict wire and historical source retention."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('burst_control_test',ROOT/'research/verify-coordinate-burst-control-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_burst_control_specs import INPUT_BASE,STATE_BASE,empty
from world_coordinate_manual_native import observe

class BurstControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=a.fixtures();cls.native={c['name'].split('/')[-1]:observe(c)[0] for c in cls.cases}
    def ticks(self,name):return self.native[name]['burst_controls']['ticks']
    def test_real_controller_state_and_wait_contract(self):
        delay=self.ticks('delay-first')
        self.assertTrue(any(t['words'][2]==1 and t['words'][14]==0 for t in delay))
        self.assertTrue(any(t['cycles']>=1 for t in delay))
        wait=self.ticks('wait-for-owner')
        self.assertTrue(any(t['cycles']==1 and t['words'][14]==1 for t in wait))
        self.assertFalse(any(t['words'][14] for t in self.ticks('delay-ready-stage2') if t['cycles']==0))
        self.assertTrue(any(t['words'][3] for t in self.ticks('reentry')))
        self.assertTrue(all(t['cycles']==0 for t in self.ticks('explicit-missing-stage')))
        self.assertTrue(all(t['words'][2]==1 and t['words'][14]==0 for t in self.ticks('explicit-empty-cycle')))
        self.assertIn(4,self.ticks('A-stage')[0]['stages'])
        self.assertGreater(max(t['cycles'] for t in self.ticks('explicit-expired')),0)
        for name in ('reduce-cooldown-wait','reduce-delay-wait','reload-into-next-fb','full-end-stage-override'):
            self.assertGreater(max(t['cycles'] for t in self.ticks(name)),0)
        log=self.native['cover-down-all']['battle']['boss_log']
        events=[x['event'] for x in log if x['pattern']=='all-covers' and x['event'] in ('cover_break','down')]
        self.assertEqual(events,['cover_break','down']*5)
        self.assertFalse(any(x['event']=='down' for x in self.native['cover-break-only-all']['battle']['boss_log']))
        last=[x['event'] for x in self.native['cover-down-last']['battle']['boss_log'] if x['pattern']=='all-covers' and x['event'] in ('cover_break','down')]
        self.assertEqual(last,['cover_break','down','down','down','down','cover_break','down'])
    def test_static_literal_bridge_never_calls_simulate_or_native_policy(self):
        from calculator import timeline
        from portable_backend import validate_composed_stride
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,109792,a.OUTPUT_WORDS)
        original=copy.deepcopy(self.cases)
        with patch.object(timeline,'simulate',side_effect=AssertionError('No computed battle input')):
            for c in self.cases:
                w,_,_,_=a.compile_case(c);self.assertEqual(len(w),109968);self.assertEqual(w[INPUT_BASE+2],1)
        self.assertEqual(self.cases,original)
        old=a.parent.fixtures()[0];w,_,_,_=a.compile_case(old);self.assertEqual(w[INPUT_BASE:],empty())
        for key,value in [('burst_delay',{'unknown':1}),('burst_sequence',[{}]*17),('burst_pattern',{a.roster_names(old)[0]:[513]})]:
            c=copy.deepcopy(self.cases[0]);c['burst_config']={key:value}
            with self.assertRaises(ValueError):a.compile_case(c)
    def test_passive_observer_and_exact_historic_source_projection(self):
        from portable_coordinate_squad_source_contract import project_sources,project_backend_source
        project_sources(ROOT);project_backend_source(ROOT)
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/combat_runtime.slang':(ROOT/'gpu/combat_runtime.slang').read_text()+'\n'})
        previous=sys.getprofile();bad=copy.deepcopy(self.cases[0]);bad['burst_config']={'burst_delay':{'unknown':1}}
        with self.assertRaises(ValueError):observe(bad)
        self.assertIs(sys.getprofile(),previous)
        for n in self.native.values():
            self.assertTrue(n['burst_controls']['ticks']);self.assertTrue(all(len(t['words'])==25 for t in n['burst_controls']['ticks']))
    def test_log_ordinals_preserve_cover_down_interleaving_and_reject_missing_deaths(self):
        s=importlib.util.spec_from_file_location('burst_log_decode',ROOT/'research/verify-world-frame.py');decoder=importlib.util.module_from_spec(s);s.loader.exec_module(decoder)
        cover=lambda i:dict(time=1.,pattern='attack',event='cover_break',outcome='',after_downs=i)
        death=dict(time=1.,pattern='attack',event='down',outcome='')
        actual=decoder.order_squad_logs([0,cover(0),cover(1)],{0:[death,death]})
        self.assertEqual([x['event'] for x in actual],['cover_break','down','cover_break','down'])
        self.assertEqual(decoder.order_squad_logs([0,cover(0)],{0:[]})[0]['event'],'cover_break')
        with self.assertRaises(AssertionError):decoder.order_squad_logs([0,cover(2)],{0:[death]})

if __name__=='__main__':unittest.main()
