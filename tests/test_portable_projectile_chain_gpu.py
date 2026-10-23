"""Static policies, full case preservation and strict retained source delta."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_projectile_chain_specs import compiler_effect,ordinary
from portable_projectile_chain_cases import fixtures
from portable_specs import LIMITS as L,FIELDS as F
class ChainGPUTests(unittest.TestCase):
    def test_projection_keeps_names_and_nontrigger_fields(self):
        e=next(e for c in fixtures() for e in c['effects'] if ordinary(e));before=copy.deepcopy(e);out=compiler_effect(e);self.assertEqual(e,before);self.assertEqual(out['stat'],'');self.assertEqual(out['name'],e['name']);self.assertEqual(out['trigger']['timing'],['event:source']);self.assertEqual(out['max_stack'],-1)
    def test_discharge_ignores_authored_coefficient_without_mutating_definition(self):
        c=next(c for c in fixtures() if c['contract']['kind']=='empty-accumulation-early-return');e=c['effects'][1];before=copy.deepcopy(e);out=compiler_effect(e);self.assertEqual(e,before);self.assertNotIn('fixed_value',out);self.assertEqual(out['stat'],'accum_split_damage')
    def test_all_native_cases_or_explicit_model_gaps_are_preserved(self):
        s=importlib.util.spec_from_file_location('chain_gpu_test',ROOT/'research/verify-world-projectile-chain-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,_=m.prepare();self.assertEqual(len(rows),32);self.assertEqual(sum(d is not None for _,_,d in rows),24)
        first=rows[0][1];event=L['EVENT_BASE']+2*L['EVENT_WORDS'];self.assertEqual(first[event],51);self.assertEqual(first[event+7],0)
        c,w,d=next(r for r in rows if r[0].endswith('buff-kind-enemy-carrier'));self.assertIn(92,[w[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+F['STAT']] for i in range(w[1])])
    def test_exact_inverse_rejects_unreviewed_shader_mutation(self):
        from portable_projectile_chain_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-projectile-chain-source-delta.json').read_text());project_sources(ROOT)
        for name,row in data['sources'].items():
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})
if __name__=='__main__':unittest.main()
