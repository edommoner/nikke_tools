"""Retain statement order and reject broken callback/early-return boundaries."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_weapon_phase_contract import verify,verify_land_macros

class WeaponPhaseTests(unittest.TestCase):
    def test_original_statements_and_snapshot_exit_contract_are_retained(self):
        result=verify(ROOT);self.assertTrue(result['verified']);self.assertEqual(len(result['phases']),5)
    def test_changed_math_is_rejected(self):
        source=(ROOT/'gpu/weapon_frame_phases.slang').read_text().replace('s.shots[who]+1','s.shots[who]+2')
        with self.assertRaisesRegex(AssertionError,'statements'):verify(ROOT,phase_source=source)
    def test_lost_early_return_propagation_is_rejected(self):
        wrapper=(ROOT/'gpu/combat_runtime.slang').read_text().replace('if(!ready) return;','',1)
        with self.assertRaisesRegex(AssertionError,'exit contract'):verify(ROOT,wrapper_source=wrapper)
    def test_lost_shared_state_reference_is_rejected(self):
        source=(ROOT/'gpu/weapon_frame_phases.slang').read_text().replace('inout Runtime s','Runtime s',1)
        with self.assertRaisesRegex(AssertionError,'signature'):verify(ROOT,phase_source=source)
    def test_reviewed_parent_quantity_formula_is_not_an_unchecked_exception(self):
        source=(ROOT/'gpu/weapon_frame_phases.slang').read_text()
        changed=source.replace('f64Mul(landedAmount,f64FromI64(w.pellets))','f64Mul(landedAmount,f64FromI64(1))')
        self.assertNotEqual(changed,source)
        with self.assertRaisesRegex(AssertionError,'statements'):verify(ROOT,phase_source=changed)
    def test_macro_early_return_is_rejected_in_any_definition_branch(self):
        text=(ROOT/'gpu/event_runtime.slang').read_text()
        changed=text.replace('notifyWorldTeam(s,who,when,output);','return;',1)
        with self.assertRaisesRegex(AssertionError,'macro escape'):verify_land_macros(ROOT,event_source=changed)
    def test_indirect_macro_escape_is_also_rejected(self):
        text=(ROOT/'gpu/event_runtime.slang').read_text()
        changed=text.replace('notifyWorldTeam(s,who,when,output);','ESCAPE_LAND;',1)+'\n#define ESCAPE_LAND return;\n'
        with self.assertRaisesRegex(AssertionError,'macro escape'):verify_land_macros(ROOT,event_source=changed)
    def test_wrong_snapshot_argument_is_rejected(self):
        wrapper=(ROOT/'gpu/combat_runtime.slang').read_text().replace('when,output,target,modeShots,mode,epoch','when,output,target,s.modeShots[who],mode,epoch')
        with self.assertRaisesRegex(AssertionError,'exit contract'):verify(ROOT,wrapper_source=wrapper)

if __name__=='__main__':unittest.main()
