"""Shared static descriptors, explicit native gaps and exact source guards."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_skill_hp_basis_specs import validate,MAGIC,OFFSET
from portable_skill_hp_basis_cases import fixtures
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

if __name__=='__main__':unittest.main()
