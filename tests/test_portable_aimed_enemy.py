"""Physical interrupt identity must not leak into canonical enemy effect scope."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_aimed_enemy_cases import fixtures
from portable_aimed_enemy_contracts import verify
from world_aimed_area_native import observe
from portable_aimed_enemy_source_contract import project_sources,ledger


class AimedEnemyTests(unittest.TestCase):
    def test_all6_native_logical_effects_and_captured_damage(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                native,_=observe(case);self.assertTrue(verify(case,native)['verified'])
        direct,_=observe(fixtures()[0]);self.assertEqual([x['packets'][0]['damage'] for x in direct['physical_packet_sets'] if x['owner']==0],[9000,9000,6000])
        self.assertEqual(direct['parts_skill_accounting']['interrupt_damage'][:2],[24000,21000])

    def test_source_delta_is_exact_and_old_scope_cannot_return(self):
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            original=(ROOT/name).read_text()
            for change in row['changes']:
                changed=original.replace(change['current'],change['baseline'],1);self.assertNotEqual(changed,original)
                with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:changed})

    def test_native_packet_and_accounting_faults_rejected(self):
        case=fixtures()[0];native,_=observe(case)
        for key in ('physical_packet_sets','parts_skill_accounting'):
            bad=copy.deepcopy(native)
            if key=='physical_packet_sets':bad[key][-2]['packets'][0]['damage']=9000
            else:bad[key]['interrupt_damage'][0]+=3000
            with self.subTest(key=key),self.assertRaises(AssertionError):verify(case,bad)


if __name__=='__main__':unittest.main()
