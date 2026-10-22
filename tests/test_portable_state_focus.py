"""Common admission, original native observations, marker/aim boundaries."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_specs import LIMITS as L,shader_schema
from portable_focus_specs import STAT,MAGIC
from portable_runtime import validate_effect,UnsupportedPortable
from portable_definition_view_contract import verify
from portable_state_focus_source_contract import ledger,baseline_source
from portable_native_query_source_contract import project_sources as project_native
from portable_focus_aim_cases import fixtures,original_fixtures
from world_focus_aim_native import observe,plain_observe
from portable_focus_aim_contracts import verify as verify_aims


def adapter():
    s=importlib.util.spec_from_file_location('state_focus_test',ROOT/'research/verify-world-state-focus-short.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class StateFocusTests(unittest.TestCase):
    def test_static_only_compilation_and_closed_raw_inputs(self):
        def forbidden(*a,**kw):raise AssertionError('Packing must not run battle/GPU')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'execute',forbidden):
            entries,data=adapter().prepare()
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(66,54))
        self.assertEqual(len(data),4+sum(len(w)*4 for _,w,_ in entries))
        self.assertEqual((ROOT/'gpu/portable_schema.slang').read_text(),shader_schema())
        self.assertGreaterEqual(STAT,64)
        self.assertEqual(L['FOCUS_STATE_BASE'],L['REVIVAL_BASE']+L['REVIVAL_WORDS'])
        self.assertLessEqual(L['FOCUS_STATE_BASE']+L['FOCUS_STATE_WORDS'],786416)
        self.assertEqual(entries[46][1][L['WORLD_ACTOR_POOL_DEF_BASE']+12+11],1)
        for name,words,domain in entries[30:54]:
            self.assertIn(words[L['WORLD_META_BASE']+4],(MAGIC,MAGIC|1))
        for name,words,domain in entries[54:]:
            self.assertIsNone(domain);adapter().validate_rejection([64],name)

    def test_aim_observation_does_not_add_live_queries_or_ticks(self):
        original=BuffManager.has_live_stat;tick=timeline.CharState.tick
        for case in fixtures():
            calls=[]
            def live(*a,**kw):calls[-1][0]+=1;return original(*a,**kw)
            def ticking(*a,**kw):calls[-1][1]+=1;return tick(*a,**kw)
            with self.subTest(case=case['name']),patch.object(BuffManager,'has_live_stat',live),patch.object(timeline.CharState,'tick',ticking):
                calls.append([0,0]);plain,trace=plain_observe(case)
                calls.append([0,0]);native,recorded=observe(case);verify_aims(case,native);native.pop('focus_aim')
                self.assertEqual(native,plain);self.assertEqual(recorded,trace);self.assertEqual(calls[0],calls[1])

    def test_presence_runtime_and_aim_faults_are_detected(self):
        for case in fixtures():
            native,_=observe(case);self.assertTrue(verify_aims(case,native)['verified'])
        c=fixtures()[0];native,_=observe(c)
        for key in ('first','last','shots'):
            bad=copy.deepcopy(native)
            if key=='shots':bad['shots'][0]=1
            else:bad['focus_aim'][0 if key=='first' else -1]['aims'][1]=''
            with self.assertRaises(AssertionError):verify_aims(c,bad)

    def test_physical_interrupt_native_gap_is_preserved_and_host_closed(self):
        case=original_fixtures()[0]
        with self.assertRaisesRegex(ValueError,'Unknown world actor'):
            plain_observe(case)
        with self.assertRaisesRegex(UnsupportedPortable,'canonical typed Actor bridge'):
            adapter().suite.compile_case(case)

    def test_host_and_exact_source_delta_guards(self):
        e=fixtures()[0]['effects'][-1];validate_effect(e,combat={},world_frame=True)
        for change,combat,world in [({},None,True),({}, {},False),({'scaling':'max_hp'},{},True),({'tick_interval':.1},{},True)]:
            with self.assertRaises(ValueError):validate_effect(dict(e,**change),combat=combat,world_frame=world)
        data=ledger(ROOT);self.assertEqual(set(verify(ROOT)['reviewed_state_focus_sources']),set(data['sources']))
        projected,_=project_native(ROOT)
        for name,row in data['sources'].items():
            source=projected.get(name,(ROOT/name).read_text())
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    baseline_source(ROOT,name,source.replace(change['current'],change['baseline'],1))


if __name__=='__main__':unittest.main()
