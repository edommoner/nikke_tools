import engine_worker
"""Selection precedes compilation and cannot drop failed original profiles."""
import array,copy,importlib.util,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_original_catalogue_cases import catalog,selected_rows
spec=importlib.util.spec_from_file_location('catalogue_test_adapter',ROOT/'research/verify-original-catalogue.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class OriginalCatalogue(unittest.TestCase):
    def fake(self):
        a=SimpleNamespace(SELECTED_PREPARATION=True,MAX_SELECTED_CASES=4,suite=SimpleNamespace(INPUT=2),case_catalog=lambda:['good','later'],prepare=Mock(side_effect=AssertionError('Full preparation forbidden')))
        a.prepare_selected=Mock(side_effect=lambda names:([(n,[1,2],dict(name=n)) for n in names],None));return a
    def manifest(self,**kwargs):return dict(suite='catalogue-fixture',purpose='development',selected_cases=['good'],**kwargs)













    def test_prepared_bodies_remain_immutable_when_selecting_variants(self):
        names=['original-catalogue/hp-shield/모더니아/favorite-0/3s','original-catalogue/projectile/모더니아/favorite-0/30s']
        rows=selected_rows(names);before=copy.deepcopy(rows[1]);rows[0]['body']['profile']['chars']['모더니아']['favorite_stage']=99
        self.assertEqual(rows[1],before)

    def test_modernia_witness_requires_original_mode_entry_and_restoration(self):
        from portable_original_catalogue_cases import prepare,verify_original_weapon_change
        case,_=prepare(selected_rows(['original-catalogue/hp-shield/모더니아/favorite-0/30s'])[0])
        def shot(coefficient,skill=False):return dict(owner=0,coefficient=coefficient,weapon_mode_skill=skill)
        normal=case['original_run']['prepared']['chars'][0]['_weapon']['damage_coeff']
        change=next(r['effect'] for r in case['original_run']['prepared']['effects'] if r['owner']=='모더니아' and r['effect']['type']=='weapon_change')
        mode=change['damage_coeff']['10']
        valid=[shot(normal),shot(mode),shot(mode),shot(normal)]
        verify_original_weapon_change(case,valid)
        for rows in ([shot(normal)],valid[1:],valid[:-1],[shot(normal),shot(mode,True),shot(normal)],[shot(normal),shot(mode),shot(normal),shot(mode),shot(normal)]):
            with self.subTest(rows=rows),self.assertRaises(AssertionError):verify_original_weapon_change(case,rows)

    def test_complete_skill_history_capacity_fails_before_gpu_instead_of_truncating(self):
        from portable_original_catalogue_cases import require_skill_history_capacity
        for count in (0,127,128):require_skill_history_capacity(dict(skill_trace=[None]*count))
        for count in (129,2048):
            native=dict(skill_trace=[None]*count)
            with self.assertRaisesRegex(ValueError,f'{count} > 128'):require_skill_history_capacity(native)
            self.assertEqual(len(native['skill_trace']),count)
if __name__=='__main__':unittest.main()
