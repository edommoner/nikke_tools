"""Caster-owned stages, exact descriptors, all-definition real preparation."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_squad_stage_cases import fixtures
from portable_squad_stage_contracts import verify
from portable_squad_stage_source_contract import project_sources,ledger
from portable_trigger_specs import validate_input,UnsupportedTrigger
from world_ally_burst_native import observe
from world_projectile_native import observe as plain
from portable_specs import LIMITS as L
from portable_real_burst_policy import configured


def module(name):
    s=importlib.util.spec_from_file_location('stage_test_'+name,ROOT/('research/verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class SquadStageTests(unittest.TestCase):
    def test_all16_preserve_native_battle_trace_and_semantic_reads(self):
        for case in fixtures():
            def measured(run):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=run(case);return result,[get.call_count,live.call_count,sample.call_count]
            with self.subTest(case=case['name']):
                (native,trace),reads=measured(observe);verify(case,native);native.pop('ally_burst_events')
                (baseline,original_trace),other=measured(plain);self.assertEqual(native,baseline);self.assertEqual(trace,original_trace);self.assertEqual(reads,other)

    def test_private_stage_syntax_and_raw_wire(self):
        for stage in (1,2,3):
            eff=dict(type='buff',stat='atk_pct',target='self',trigger=dict(timing=['squad_burst_cast:'+str(stage)],condition=[]));validate_input(eff,world_frame=True)
            with self.assertRaises(UnsupportedTrigger):validate_input(eff,world_frame=False)
        for text in ('0','4','01','-1','1.0','+1','{0}','1:2',''):
            eff=dict(trigger=dict(timing=['squad_burst_cast:'+text],condition=[]))
            with self.subTest(text=text),self.assertRaises(UnsupportedTrigger):validate_input(eff,world_frame=True)
        entries,_=module('squad-stage').prepare();self.assertEqual(len(entries),30)
        self.assertTrue(all(words!=entries[2][1] for _,words,domain in entries[16:]))
        for _,words,domain in entries[:16]:
            count=0
            for row in range(len(domain[0]['effects'])):
                for slot in range(8):
                    at=L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8
                    if words[at]==41:self.assertIn(words[at+7],(1,2,3));self.assertEqual(words[at+3:at+7],[0,0xffffffff,0,0]);count+=1
            self.assertGreater(count,0)

    def test_source_delta_rejects_omission_wrong_order_stage_and_ownership(self):
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            text=(ROOT/name).read_text()
            for change in row['changes']:
                bad=text.replace(change['current'],change['baseline'],1);self.assertNotEqual(text,bad)
                with self.assertRaises(AssertionError):project_sources(ROOT,{name:bad})
        name='gpu/combat_runtime.slang';text=(ROOT/name).read_text();bad=text.replace('dispatch(s,0,41,picked,int(stage)','dispatch(s,0,41,4,int(stage)')
        self.assertNotEqual(text,bad)
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:bad})

    def test_full_real_roster_has_all81_definitions_without_battle_or_gpu(self):
        def forbidden(*a,**k):raise AssertionError('Static preparation executed a battle/GPU')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'execute',forbidden):rows,data=module('squad-stage-rosters').prepare()
        self.assertEqual(len(rows),7)
        for _,_,(case,p,w,m) in rows:
            expected=81+len(case.get('live_overrides',()))
            self.assertEqual((len(p['effects']),len(m['effects'])),(expected,expected));self.assertEqual(sorted(m['binding_source_indices']),list(range(expected)))
            with configured(case['body'],case.get('burst_stages',{})):
                original=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
            self.assertEqual(p['effects'][:81],original['effects']);self.assertEqual(p['chars'],original['chars'])
            self.assertEqual(w[L['WEAPON_BASE']+3],0x404 if case.get('burst_stages') else 0x304)


    def test_automatic_selection_stage_keeps_logical_stage_and_explicit_override(self):
        from portable_weapon_input import normalize_static_weapon
        m=module('squad-stage-rosters');rows,_=m.prepare();case,p,w,meta=rows[0][2]
        automatic=normalize_static_weapon(p['chars'][0],p['base_atk'][0],p['enemy'])
        self.assertEqual((automatic['stage'],automatic['automatic_burst_stage']),(4,3))
        explicit=normalize_static_weapon(dict(p['chars'][0],burst_stage='A'),p['base_atk'][0],p['enemy'])
        self.assertEqual(explicit['stage'],4);self.assertNotIn('automatic_burst_stage',explicit);self.assertIs(explicit['explicit_burst_stage'],True)
        c=copy.deepcopy(fixtures()[0]);c['combat']['weapons'][0].update(stage=1,automatic_burst_stage=3)
        with self.assertRaisesRegex(ValueError,'logical all-stage'):module('squad-stage').suite.compile_case(c)
        c['combat']['weapons'][0].update(stage=4,automatic_burst_stage=3,explicit_burst_stage=True)
        with self.assertRaisesRegex(ValueError,'Explicit stage'):module('squad-stage').suite.compile_case(c)
        c['combat']['weapons'][0].pop('explicit_burst_stage')
        for value in (True,-1,4,'3'):
            c['combat']['weapons'][0].update(stage=4,automatic_burst_stage=value)
            with self.assertRaisesRegex(ValueError,'logical all-stage'):module('squad-stage').suite.compile_case(c)

    def test_native_owner_and_notification_order_faults_detected(self):
        case=fixtures()[0];native,_=observe(case)
        for fault in ('owner','stage','order','hp'):
            bad=copy.deepcopy(native)
            if fault=='owner':next(x for x in bad['ally_burst_events'] if x['kind']=='activate')['owner']=4
            elif fault=='stage':next(x for x in bad['ally_burst_events'] if x.get('event','').startswith('squad_burst_cast'))['event']='squad_burst_cast:4'
            elif fault=='order':bad['ally_burst_events'][1],bad['ally_burst_events'][2]=bad['ally_burst_events'][2],bad['ally_burst_events'][1]
            else:bad['allies'][0]['hp']+=100
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,bad)


if __name__=='__main__':unittest.main()
