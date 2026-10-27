"""Static packing is auditable without admitting or executing a GPU battle."""
import copy,contextlib,importlib.util,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research'),str(ROOT/'scripts')]
import engine_worker
import portable_original_entry_inventory as inventory
from nikke_gpu import write,forbid_gpu
class EntryInventoryTests(unittest.TestCase):
    def prepared(self,name):
        spec=importlib.util.spec_from_file_location('entry_inventory_test_roster',ROOT/'research/audit-world-roster-input.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
        from detail_coverage import body_for
        return engine_worker.evaluate(dict(body_for(policy.roster_for(name),30),burst_gauge_mode='accumulate',_portable_static_inputs=True))

    def test_typed_modes_keep_originals_and_record_actual_group_lowering_and_modifier_axes(self):
        profiles=[(name,0,self.prepared(name)) for name in ('아스카','벨로타','니힐리스타','일레그')]
        before=copy.deepcopy(profiles)
        for mode,kind in [('body-owned-projectile-v1',2),('body-owned-hp-shield-v1',3)]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'typed.json'
                with patch.object(inventory,'prepared_profiles',return_value=iter(profiles)):
                    result=inventory.run(output,write=write,forbid_gpu=forbid_gpu,source=inventory.TYPED_SOURCE,input_policy=mode)
                report=json.loads(output.read_text());self.assertEqual(result['forbidden_calls'],dict(cpu_battle=0,gpu=0))
                self.assertEqual(report['input_policy'],mode);self.assertEqual(report['declared_typed_world']['kind'],kind)
                self.assertFalse(report['declared_typed_world']['extra_damage_probe']);self.assertFalse(result['gpu_admission_verified'])
                rows={r['character']:r for r in report['profiles']}
                for name in ('아스카','벨로타','니힐리스타'):
                    row=rows[name];self.assertTrue(row['input_packed']);self.assertEqual(row['input_words'],115680);self.assertEqual(row['kind_admission']['unsupported'],[])
                self.assertTrue(rows['아스카']['typed_modifier_bindings']);self.assertEqual({r['axis'] for r in rows['아스카']['typed_modifier_bindings']},{3})
                for name,count in [('벨로타',2),('니힐리스타',1)]:
                    self.assertEqual(len(rows[name]['original_multi_hit_sources']),count);self.assertEqual(rows[name]['group_producer_owner_mask'],1)
                self.assertFalse(rows['일레그']['input_packed']);self.assertIn('program_issue',rows['일레그']);self.assertTrue(report['packing_priorities'])
                blockers=rows['일레그']['effect_blockers'];self.assertTrue(blockers)
                self.assertNotIn('projectile_dmg_pct',{e['issue'].get('stat') for e in blockers})
                self.assertIn('target_and_nearby:2',{e['issue'].get('target') for e in blockers})
        self.assertEqual(profiles,before)

    def test_input_policy_and_source_pair_fail_before_preparing_profiles(self):
        for mode,source in [('unknown',None),('body-owned-projectile-v1','gpu/world_coordinate_original_entry.slang'),('original-coordinate-v1',inventory.TYPED_SOURCE)]:
            with tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'failed.json'
                with patch.object(inventory,'prepared_profiles',side_effect=AssertionError('No profile work before policy validation')):
                    with self.assertRaises(ValueError):inventory.run(output,write=write,forbid_gpu=forbid_gpu,input_policy=mode,source=source)
                report=json.loads(output.read_text());self.assertFalse(report['passed']);self.assertEqual(report['forbidden_calls'],dict(cpu_battle=0,gpu=0))

    def test_invalid_axis_provenance_aborts_instead_of_becoming_a_packing_gap(self):
        p=self.prepared('아스카');original=inventory.compile_inventory_world
        def corrupt(*args):
            w,m,b,d=original(*args);m['coordinate_typed_input']['axis_rows']=[];return w,m,b,d
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'failed.json'
            with patch.object(inventory,'prepared_profiles',return_value=iter([('아스카',0,p)])),patch.object(inventory,'compile_inventory_world',corrupt):
                with self.assertRaisesRegex(ValueError,'axis provenance'):inventory.run(output,write=write,forbid_gpu=forbid_gpu,input_policy='body-owned-hp-shield-v1')
            self.assertFalse(json.loads(output.read_text())['passed'])

    def test_typed_packing_cannot_execute_a_cpu_battle(self):
        from calculator import timeline
        p=self.prepared('아스카')
        def bad(*args,**kwargs):return timeline.simulate([])
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'failed.json'
            with patch.object(inventory,'prepared_profiles',return_value=iter([('아스카',0,p)])),patch('portable_coordinate_typed_input.compile_coordinate_typed',bad):
                with self.assertRaisesRegex(AssertionError,'forbids cpu_battle'):inventory.run(output,write=write,forbid_gpu=forbid_gpu,input_policy='body-owned-hp-shield-v1')
            report=json.loads(output.read_text());self.assertFalse(report['passed']);self.assertEqual(report['forbidden_calls']['cpu_battle'],1)

    def test_cli_routes_each_suite_to_its_real_input_policy(self):
        import nikke_gpu
        for name,policy in [('coordinate-original','original-coordinate-v1'),('original-projectile-weapons','body-owned-projectile-v1'),('original-shield-weapons','body-owned-hp-shield-v1')]:
            with patch.object(inventory,'run',return_value={'passed':True}) as run,contextlib.redirect_stdout(io.StringIO()):
                nikke_gpu.main(['entry-inventory','--suite',name,'--out','/tmp/not-written-entry-inventory.json'])
            self.assertEqual(run.call_args.kwargs['input_policy'],policy)
            self.assertEqual(run.call_args.kwargs['source'],nikke_gpu.SUITES[name]['source'])
    def test_rejections_bind_original_sources_and_keep_distinct_operators(self):
        from portable_specs import LIMITS as L,FIELDS as F
        words=[0]*(L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']);words[1]=2
        for index,kind in enumerate((33,1)):words[L['DEFINITION_BASE']+index*L['DEFINITION_WORDS']+F['KIND']]=kind
        effects=[dict(owner='owner-a',effect=dict(name='scoped removal',type='instant',stat='remove_named_buff',target='all_allies',target_effect='mark',remove_scope='target',trigger=dict(timing=['on_attack'],condition=[]))),
                 dict(owner='owner-b',effect=dict(name='force skill',type='instant',stat='force_skill_use',target_skill='스킬1',trigger=dict(timing=['battle_start'],condition=['self_hp_below:50'])))]
        rows=inventory.rejected_effects(words,dict(binding_source_indices=[1,0]),dict(effects=effects),[dict(row=0,kind=33),dict(row=1,kind=1)])
        self.assertEqual([(row['source_row'],row['owner']) for row in rows],[(1,'owner-b'),(0,'owner-a')])
        self.assertEqual(rows[0]['operator']['references'],dict(target_skill='스킬1'))
        self.assertEqual(rows[0]['operator']['conditions'],['self_hp_below:50'])
        self.assertEqual(rows[1]['operator']['references'],dict(target_effect='mark',remove_scope='target'))
        before=rows[1]['operator']['references'].copy();effects[0]['effect']['target_effect']='changed';self.assertEqual(rows[1]['operator']['references'],before)
        with self.assertRaisesRegex(ValueError,'actual wire'):inventory.rejected_effects(words,dict(binding_source_indices=[1,0]),dict(effects=effects),[dict(row=0,kind=15)])
        with self.assertRaisesRegex(ValueError,'original rejection source'):inventory.rejected_effects(words,dict(binding_source_indices=[False,0]),dict(effects=effects),[dict(row=0,kind=33)])

    def test_priorities_distinguish_profiles_sources_and_compiled_instances(self):
        operator=dict(kind=33,effect_type='instant',stat='force_skill_use',target='self',timing=['battle_start'],conditions=[],references=dict(target_skill='스킬1'),fields=['type','stat'])
        first=dict(compiled_row=0,source_row=0,owner='owner',name='first',operator=operator,effect_sha256='a')
        duplicate=dict(first,compiled_row=1)
        other=dict(first,compiled_row=2,operator=dict(operator,references=dict(target_skill='스킬2')))
        result=inventory.operator_priorities([dict(character='character',favorite_stage=0,rejected_effects=[first,duplicate,other]),dict(character='character',favorite_stage=1,rejected_effects=[first])])
        self.assertEqual(len(result),2)
        self.assertEqual((result[0]['profile_count'],result[0]['original_definition_count'],result[0]['compiled_definition_count']),(2,2,3))
        self.assertEqual(result[1]['operator']['references'],dict(target_skill='스킬2'))

    def test_full_inventory_separates_packing_from_gpu_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.json';result=inventory.run(path,write=write,forbid_gpu=forbid_gpu);report=json.loads(path.read_text())
        self.assertTrue(result['passed']);self.assertEqual(result['profile_count'],266);self.assertEqual(result['packed_profiles'],247)
        self.assertEqual(result['forbidden_calls'],dict(cpu_battle=0,gpu=0))
        self.assertFalse(result['gpu_admission_verified']);self.assertFalse(result['calculation_verified'])
        gauge_profiles=report['definition_kind_profiles']['9']
        self.assertEqual(len(gauge_profiles),15)
        self.assertTrue(all(not row['gpu_admission_verified'] for row in report['profiles']))
        rejected={(row['character'],row['favorite_stage']) for row in report['profiles'] if row.get('kind_admission',{}).get('unsupported')}
        classified={(row['character'],row['favorite_stage']) for category in report['operator_priorities'] for row in category['profiles']}
        self.assertEqual(classified,rejected)
        dependencies={(row['character'],row['favorite_stage']) for category in report['kind_dependencies'] for row in category['profiles']}
        self.assertEqual(dependencies,rejected)
        self.assertEqual(sum(row['profile_count'] for row in report['kind_dependencies']),len(rejected))
        self.assertEqual(sum(row['compiled_definition_count'] for row in report['operator_priorities']),sum(len(row.get('rejected_effects',[])) for row in report['profiles']))
        self.assertEqual(len(report['packing_failures'])+report['packed_profiles'],report['profile_count'])

    def test_provenance_failure_is_not_reported_as_a_normal_packing_gap(self):
        from portable_coordinate_original_revival_cases import fixtures
        from portable_coordinate_original_cases import prepare_case
        _,prepared=prepare_case(fixtures()[0])
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'bad-provenance.json'
            with patch.object(inventory,'prepared_profiles',return_value=iter([('마나',0,prepared)])),patch.object(inventory,'rejected_effects',side_effect=ValueError('bad original mapping')):
                with self.assertRaisesRegex(ValueError,'bad original mapping'):inventory.run(output,write=write,forbid_gpu=forbid_gpu)
            report=json.loads(output.read_text());self.assertFalse(report['passed']);self.assertIn('bad original mapping',report['error'])

    def test_battle_attempt_preserves_failed_report_and_refuses_overwrite(self):
        from calculator import timeline
        from portable_coordinate_original_revival_cases import fixtures
        from portable_coordinate_original_cases import prepare_case
        _,prepared=prepare_case(fixtures()[0])
        def bad(*args):return timeline.simulate([])
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'failed.json'
            with patch.object(inventory,'prepared_profiles',return_value=iter([('마나',0,prepared)])),patch('portable_coordinate_roster_input.compile_coordinate_battle',bad):
                with self.assertRaisesRegex(AssertionError,'forbids cpu_battle'):inventory.run(output,write=write,forbid_gpu=forbid_gpu)
            report=json.loads(output.read_text());self.assertFalse(report['passed']);self.assertEqual(report['forbidden_calls']['cpu_battle'],1)
            before=output.read_bytes()
            with self.assertRaises(FileExistsError):inventory.run(output,write=write,forbid_gpu=forbid_gpu)
            self.assertEqual(output.read_bytes(),before)

    def test_shared_identity_catalog_remains_nonpacking(self):
        from portable_original_identity_inventory import inspect
        import portable_runtime
        with patch.object(portable_runtime,'compile_program',side_effect=AssertionError('Identity catalog cannot pack')):result=inspect()
        self.assertEqual(result['profiles'],266);self.assertEqual(result['nonperiodic_duplicate_groups'],[])
if __name__=='__main__':unittest.main()
