"""Static packing is auditable without admitting or executing a GPU battle."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research'),str(ROOT/'scripts')]
import engine_worker
import portable_original_entry_inventory as inventory
from nikke_gpu import write,forbid_gpu
class EntryInventoryTests(unittest.TestCase):
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
