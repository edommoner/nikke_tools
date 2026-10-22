"""ATK/DEF-only shared flag admission, static identity and finite source fault guards."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_lost_hp_attack_cases import fixtures
from portable_runtime import validate_effect,UnsupportedPortable
from portable_definition_view_contract import verify
from portable_specs import LIMITS as L,FIELDS as F

class LostHPAttackTests(unittest.TestCase):
    def adapter(self):
        s=importlib.util.spec_from_file_location('lost_hp_attack_tests',ROOT/'research/verify-world-lost-hp-attack-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    def test_admission_has_structured_reasons_and_keeps_other_combinations_closed(self):
        effect=fixtures()[0]['effects'][0]
        for stat in ('atk_pct','def_pct'):validate_effect(dict(effect,stat=stat),combat={})
        for changed,reason,combat in [({'stat':'max_hp_pct'},'scaling',{}),({'stat':'atk_caster_based_pct'},'scaling',{}),({'target':'all_allies'},'recipient',{}),({},'scaling',None)]:
            with self.subTest(changed=changed),self.assertRaises(UnsupportedPortable) as caught:validate_effect(dict(effect,**changed),combat=combat)
            self.assertEqual(caught.exception.reason,reason)
    def test_pack_preserves_live_flag_and_values_without_case_mutation(self):
        cases=fixtures();before=copy.deepcopy(cases);m=self.adapter()
        for case in cases:
            words,_,_=m.suite.compile_case(case)
            for i,e in enumerate(case['effects']):
                at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS'];self.assertEqual(bool(words[at+F['FLAGS']]&128),e.get('scaling')=='lost_hp_pct')
        self.assertEqual(cases,before)
        entries,data=m.prepare();self.assertEqual(len(entries),29);self.assertEqual(sum(e[2] is not None for e in entries),21);self.assertEqual(len(data),4+29*m.suite.INPUT*4)
        seed=entries[0][1]
        for name,words,domain in entries[-8:]:self.assertIsNone(domain);self.assertEqual(sum(a!=b for a,b in zip(seed,words)),1,name)
    def test_source_guard_rejects_broader_stats_recipient_flags_and_scalar_math_drift(self):
        self.assertEqual(verify(ROOT)['reviewed_lost_hp_attack_sources'],['gpu/reference_runtime.slang'])
        name='gpu/reference_runtime.slang';source=(ROOT/name).read_text()
        for old,new in [('d.stat==S_atk_pct && d.alliedFlags==0','d.stat==S_atk_pct'),('commands[s.inputBase+P_RECIPIENT_BASE+row*8]!=0','false'),('s.combat==0 || scale!=0','false || scale!=0'),('capacityKey>s.resourceCount','false')]:
            self.assertIn(old,source)
            with self.subTest(old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})
        name='gpu/quantity_runtime.slang';source=(ROOT/name).read_text();old='f64Mul(value,larger(0,f64Add(HUNDRED,s.hpPct[d.owner] ^ F64_SIGN)))';self.assertIn(old,source)
        with self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,'f64Mul(value,f64FromI64(stack))',1)})

if __name__=='__main__':unittest.main()
