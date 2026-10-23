"""Native actor-weapon semantics and narrow annotation admission, both backends."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,portable_backend,detail_gpu
from calculator.buff_manager import BuffManager
from calculator import timeline
from portable_skill_weapon_cases import fixtures
from portable_skill_weapon_contracts import verify
from world_skill_weapon_native import observe
from world_projectile_native import observe as plain
from portable_skill_weapon_specs import declaration,validate_binding
from portable_skill_weapon_contract import verify as source_contract

def adapter():
    s=importlib.util.spec_from_file_location('skill_weapon_test',ROOT/'research/verify-world-skill-weapon-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class SkillWeaponTests(unittest.TestCase):
    def test14_native_contracts_preserve_inputs_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases);gaps=0
        def no(*a,**k):raise AssertionError('Compilation/GPU forbidden')
        with patch.object(portable_runtime,'compile_program',no),patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no),patch.object(detail_gpu,'compile_effects',no):
            for c in cases:
                with self.subTest(case=c['name']):n,_=observe(c);gaps+=verify(c,n)['reference_model_gap']
        self.assertEqual(gaps,6);self.assertEqual(cases,before)
    def test_observation_preserves_complete_battle_trace_and_semantic_read_counts(self):
        for c in fixtures():
            def measured(fn):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'_get_value',autospec=True,side_effect=BuffManager._get_value) as value,patch.object(timeline,'calc_damage',side_effect=timeline.calc_damage) as calc,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=fn(c);return result,(get.call_count,value.call_count,calc.call_count,sample.call_count)
            with self.subTest(case=c['name']):
                (n,t),reads=measured(observe);n.pop('skill_weapon_calls');(old,trace),counts=measured(plain);self.assertEqual((n,t),(old,trace));self.assertEqual(reads,counts)
    def test_native_conflicting_declarations_are_ignored_but_not_gpu_admitted(self):
        by={}
        for c in fixtures()[:12]:
            n,t=observe(c);n.pop('skill_weapon_calls');key=c['contract']['base']
            if key not in by:by[key]=(n,t)
            self.assertEqual((n,t),by[key])
            e=c['effects'][-1];metadata=dict(weapon_type=key)
            if c['contract']['reference_model_gap']:
                with self.assertRaises(ValueError):validate_binding(e,metadata)
            else:validate_binding(e,metadata)
    def test_known_matching_metadata_does_not_change_packed_words(self):
        m=adapter()
        for c in fixtures():
            if c['contract']['reference_model_gap']:continue
            before=copy.deepcopy(c);w,_,_=m.suite.compile_case(c);omitted=copy.deepcopy(c);omitted['effects'][-1].pop('weapon_type',None);other,_,_=m.suite.compile_case(omitted)
            with self.subTest(case=c['name']):self.assertEqual(w,other);self.assertEqual(c,before)
    def test_unknown_type_wrong_family_formula_and_nonworld_fail_closed(self):
        e=fixtures()[1]['effects'][-1]
        for value in (None,False,1,'','LASER',[],{}):
            with self.subTest(value=value),self.assertRaises(ValueError):declaration(dict(e,weapon_type=value))
        for changes in (dict(stat='projectile_explosion_damage'),dict(type='buff'),dict(damage_formula='skill')):
            with self.assertRaises(portable_runtime.UnsupportedPortable):portable_runtime.validate_effect(dict(e,**changes),combat={},world_frame=True)
        for combat,world in ((None,True),({},False)):
            with self.assertRaises(portable_runtime.UnsupportedPortable):portable_runtime.validate_effect(e,combat=combat,world_frame=world)
    def test_pinned_native_handler_rejects_added_effect_reader_or_weapon_override(self):
        r=source_contract(ROOT);self.assertEqual(r['weapon_type_readers'],['cs.weapon']);self.assertFalse(r['effect_local_weapon_override'])
        text=(ROOT/'research/upstream/nikke-calc-master/calculator/timeline.py').read_text()
        for old,new in [('weapon_type = cs.weapon.get("weapon_type", "")','weapon_type = eff.get("weapon_type", "")'),('is_normal and cs.base_weapon_type == "RL"','is_normal and eff.get("weapon_type") == "RL"')]:
            self.assertIn(old,text)
            with self.assertRaises(ValueError):source_contract(ROOT,text.replace(old,new,1))
    def test_native_contract_rejects_wrong_weapon_owner_coefficient_and_false_mode_witness(self):
        c=fixtures()[-1];n,_=observe(c)
        for key,value in [('owner',4),('current','SR'),('base','AR'),('declared','SR'),('explosion',False),('normal',False),('coeff',101),('damage',6000),('mode_active',False)]:
            bad=copy.deepcopy(n);bad['skill_weapon_calls'][1][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):verify(c,bad)
    def test10_wire_cases_keep_original_full_profile_definitions(self):
        m=adapter();rows,data=m.prepare();self.assertEqual(len(rows),10);self.assertEqual(len(data),4+10*104400*4);self.assertTrue(all(d is not None for _,_,d in rows))
        for name,w,d in rows[-2:]:
            prepared=d[2];self.assertEqual(len(prepared['effects']),83)
            annotations=[item['effect'] for item in prepared['effects'] if item['effect'].get('stat')=='auto_damage'];self.assertEqual(len(annotations),1);self.assertEqual(annotations[0]['weapon_type'],'RL')
    def test_runtime_admission_blocker_is_separate_from_static_packing(self):
        from portable_readiness_semantics import reference_readiness
        for descriptor in ('has_burst1_ally','no_burst1_ally'):
            r=reference_readiness(dict(phase='gpu-admission',category='trigger',operator=dict(domain='condition',descriptor=descriptor)))
            self.assertEqual(r['lane'],'native_contract_extension');self.assertEqual(r['recorded_cases'],12);self.assertEqual(r['reference_suites'],['burst1-ally']);self.assertFalse(r['gpu_supported']);self.assertFalse(r['runtime_validation_performed'])
        self.assertEqual(reference_readiness(dict(phase='effect',category='trigger',operator=dict(domain='condition',descriptor='no_burst1_ally')))['lane'],'reference_review')

    def test_remaining_contradictions_are_model_questions_not_calculation_support(self):
        from portable_readiness_semantics import reference_readiness
        r=reference_readiness(dict(phase='effect',category='fields',kind='damage',stat='auto_damage',fields=['weapon_type']))
        self.assertEqual(r['lane'],'reference_model_gap');self.assertEqual(r['recorded_cases'],16);self.assertEqual(r['reference_model_gap_cases'],6);self.assertFalse(r['gpu_supported'])

if __name__=='__main__':unittest.main()
