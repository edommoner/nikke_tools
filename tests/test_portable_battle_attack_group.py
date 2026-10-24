"""Static lowering boundaries before hardware execution."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_battle_attack_group_cases import fixtures
from portable_battle_attack_group_input import compile_battle,INPUT_WORDS
from portable_specs import LIMITS as L,FIELDS as F,shader_schema
class PortableBattleAttackGroupTests(unittest.TestCase):
    def test_original_effects_and_no_native_battle_input(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle input')):
            for c in fixtures():
                p=engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));before=copy.deepcopy(p)
                w,m=compile_battle(p,routing=c['routing'],declared_effects=c.get('declared_effects',[]));self.assertEqual(p,before);self.assertEqual(len(w),INPUT_WORDS)
                source=m['real_prepared_input']['declared_attack_group_policy']['source_effects'];self.assertEqual(source[:len(p['effects'])],p['effects'])
                self.assertTrue(any(w[L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8]==62 for row in range(w[1]) for slot in range(w[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['TRIGGER_COUNT']])))
    def test_policy_and_non_plain_targets_are_rejected(self):
        c=fixtures()[0];p=engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True))
        for value in (None,True,'all_enemies'):
            with self.assertRaises(ValueError):compile_battle(p,routing=value)
        p['enemy']['has_parts']=True
        with self.assertRaises(ValueError):compile_battle(p,routing=c['routing'])
    def test_native_route_is_static_and_old_inputs_are_retained(self):
        import importlib.util
        from portable_battle_native_route_cases import fixtures as native_cases
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle trace input')):
            for case in native_cases():
                p=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True));before=copy.deepcopy(p)
                w,m=compile_battle(p,routing='native',declared_effects=case.get('declared_effects',[]))
                self.assertEqual(p,before);self.assertEqual(w[104401],2)
                self.assertFalse(m['real_prepared_input']['declared_attack_group_policy']['cpu_trace_used_as_gpu_input'])
        spec=importlib.util.spec_from_file_location('native_route_gpu_adapter',ROOT/'research/verify-world-attack-group-native-route-short.py')
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        old,_=adapter.shared.prepare();entries,_=adapter.prepare()
        self.assertEqual(len(entries),53)
        self.assertEqual([(n,w) for n,w,_ in old],[(n,w) for n,w,_ in entries[:32]])
        self.assertEqual(entries[-1][1][104401],3)
    def test_suite_includes_native_audit_document(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('group_cli_config',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        self.assertIn('research/upstream/nikke-calc-master/docs/IMPL-STATUS.md',cli.SUITES['attack-group-battle']['upstream_documents'])
        from portable_battle_attack_group_input import OUTPUT_WORDS
        self.assertEqual(cli.SUITES['attack-group-battle']['output_words'],OUTPUT_WORDS)
    def test_cli_rejects_wrong_output_allocation_before_prepare(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('group_cli_dimension_guard',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with patch.dict(cli.SUITES['attack-group-battle'],output_words=786432):
            with self.assertRaisesRegex(ValueError,'transport allocation'):cli.open_suite(dict(suite='attack-group-battle'))
    def test_native_field_snapshot_survives_boss_finalization(self):
        import importlib.util
        from world_battle_attack_group_native import observe
        spec=importlib.util.spec_from_file_location('group_field_binding_oracle',ROOT/'research/verify-world-attack-group-battle-short.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        n,_=observe(fixtures()[12]);self.assertTrue(all(not a['alive'] for a in n['adds']))
        self.assertEqual(adapter.native_field_bindings(n,{'그리디'}),[('그리디',(0,0,1)),('그리디',(5,0,1)),('그리디',(5,1,1)),('그리디',(5,2,1))])
        n,_=observe(fixtures()[19]);self.assertEqual(adapter.native_field_bindings(n,{'그리디'}),[('그리디',(0,0,1))])
    def test_exact_historical_delta_rejects_unreviewed_edits(self):
        from portable_attack_group_source_contract import project_sources
        projected=project_sources(ROOT)
        self.assertNotIn('deliverAttackGroupShot',projected['gpu/combat_runtime.slang'])
        for name in ('gpu/world_skill_runtime.slang','gpu/event_runtime.slang','gpu/combat_runtime.slang'):
            changed=(ROOT/name).read_text()+'\n// unreviewed delta\n'
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:changed})
    def test_schema_is_generated_and_storage_is_bounded(self):
        from portable_battle_attack_group_input import HEADER,SLOTS,SLOT_WORDS,LOG,LOG_CAPACITY,PACKETS,OUTPUT_WORDS
        self.assertEqual((ROOT/'gpu/portable_schema.slang').read_text(),shader_schema())
        self.assertGreaterEqual(HEADER,L['WORLD_RELOAD_OUTPUT_WORDS']);self.assertLessEqual(SLOTS+32*SLOT_WORDS,LOG);self.assertLessEqual(LOG+LOG_CAPACITY*SLOT_WORDS,PACKETS);self.assertLessEqual(PACKETS+L['LANDINGS'],OUTPUT_WORDS)
if __name__=='__main__':unittest.main()
