"""Shared static descriptors, explicit native gaps and exact source guards."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_skill_hp_basis_specs import validate,MAGIC,OFFSET
from portable_skill_hp_basis_cases import fixtures
from portable_skill_hp_basis_source_contract import verify_sources
from portable_definition_view_contract import verify
from portable_specs import LIMITS as L

class SkillHPBasisTests(unittest.TestCase):
    def adapter(self):
        s=importlib.util.spec_from_file_location('skill_hp_basis_tests',ROOT/'research/verify-world-skill-hp-basis-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    def test_uses_shared_definition_and_rejects_malformed_or_unowned_basis(self):
        effect=fixtures()[1]['effects'][-1]
        self.assertEqual(validate(effect,combat={},world_frame=True).mode,1)
        for field,value in [('scaling_hp_pct',v) for v in (None,True,'1',-1,float('nan'),float('inf'),1000001,2**10000)]+[('type','buff'),('scaling_ref','x')]:
            with self.subTest(field=field,type=type(value).__name__),self.assertRaises(ValueError):validate(dict(effect,**{field:value}),combat={},world_frame=True)
        for combat,world in ((None,True),({},False)):
            with self.assertRaisesRegex(ValueError,'private combat world'):validate(effect,combat=combat,world_frame=world)
        with self.assertRaises(ValueError):validate(dict(effect,scaling='unknown'),combat={},world_frame=True)
    def test_static_modes_pack_without_case_mutation_and_deferred_gap_is_rejected(self):
        m=self.adapter();cases=fixtures();before=copy.deepcopy(cases)
        for case in cases:
            if case['contract'].get('reference_model_gap'):
                with self.assertRaisesRegex(ValueError,'reference_model_gap'):m.suite.compile_case(case)
                continue
            words,_,_=m.suite.compile_case(case)
            if case['name'].endswith('-half-max'):
                self.assertEqual(words[L['HP_UNCLAMP_POLICY']],1)
            for row,effect in enumerate(case['effects']):
                at=L['MODE_BASE']+row*L['MODE_WORDS']+OFFSET
                descriptor=words[at:at+4]
                if 'scaling_hp_pct' not in effect:self.assertEqual(descriptor,[0]*4);continue
                self.assertEqual(descriptor[:2],[MAGIC,1 if effect['scaling']=='max_hp_additive' else 2])
                self.assertEqual(struct.unpack('<d',struct.pack('<II',*descriptor[2:]))[0],effect['scaling_hp_pct'])
        self.assertEqual(cases,before)
        entries,data=m.prepare();self.assertEqual(len(entries),37);self.assertEqual(sum(e[2] is not None for e in entries),26)
        self.assertEqual(len(data),4+37*m.suite.INPUT*4)
    def test_source_guards_reject_arithmetic_order_identity_and_admission_faults(self):
        self.assertEqual(len(verify_sources(ROOT)),8)
        self.assertEqual(len(verify(ROOT)['reviewed_skill_hp_basis_sources']),8)
        edits=[('gpu/skill_hp_basis_runtime.slang','f64Div(f64Mul(nativeAttackMaxHP(s,who,when),pct),HUNDRED)','f64Mul(nativeAttackMaxHP(s,who,when),f64Div(pct,HUNDRED))'),('gpu/skill_hp_basis_runtime.slang','flat=f64Add(flat,hp)','base=f64Add(base,hp)'),('gpu/skill_hp_basis_runtime.slang','d.damagePending!=0','false'),('gpu/damage_runtime.slang','who,basisRow,when','who,who,when'),('gpu/world_skill_runtime.slang','false,d._wireRow','false,d.owner'),('gpu/dispatch_phases.slang','false,damage._wireRow','false,damage.owner'),('gpu/program_phases.slang','!validSkillHPBasis(s)','false'),('gpu/stack_runtime.slang','field>=20&&field<24','field>=20&&field<32')]
        for name,old,new in edits:
            source=(ROOT/name).read_text();self.assertIn(old,source);changed=source.replace(old,new,1)
            with self.subTest(name=name,old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:changed})
        for name,old,new in [('gpu/protection_runtime.slang','(d.stat==S_max_hp_only_pct || d.stat==S_hp_only_caster_based_pct)','(d.stat==S_atk_pct)'),('gpu/event_runtime.slang','d.kind==27||d.kind==31||d.kind==33','d.kind==33')]:
            source=(ROOT/name).read_text();self.assertIn(old,source)
            with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

if __name__=='__main__':unittest.main()
