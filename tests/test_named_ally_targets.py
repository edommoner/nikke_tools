"""Exact catalog names are names even when punctuation resembles selector syntax."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a
import detail_gpu as g

TARGET='아니스 : 스타'
BASE=['리타','크라운','앨리스','모더니아','N102']

def characters(names):return [dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in names]
def effect(target,value=25,event='battle_start',duration=.2):
    return dict(name='named ally '+event,source='스킬1',type='buff',stat='atk_pct',fixed_value=value,target=target,duration=duration,trigger=dict(timing=[event],condition=[]))

class NamedAllyTargets(unittest.TestCase):
    def test_exact_known_name_at_each_slot_and_absent(self):
        from calculator.buff_manager import BuffManager
        for target in (TARGET,'리타'):
            for slot in (*range(5),None):
                names=[n for n in BASE if n!=target]
                if slot is not None:names.insert(slot,target)
                names=(names+['도라'])[:5];chars=characters(names)
                with self.subTest(target=target,slot=slot):
                    row=g.compile_effects(chars,[(effect(target),names[0])])['effects'][0]
                    self.assertEqual(row[4],8);self.assertEqual(row[48],0 if slot is None else 1<<slot)
                    bm=BuffManager.__new__(BuffManager);bm.squad_names=names;bm.state={}
                    self.assertEqual(bm._resolve_target(target,names[0]),[] if slot is None else [target])

    def test_unknown_names_and_malformed_selector_strings_stay_rejected(self):
        for target in ('unknown','unknown : ally','allies_random:7','아니스:스타'):
            with self.subTest(target=target),self.assertRaises(g.UnsupportedDetail):g.compile_effects(characters(BASE),[(effect(target),BASE[0])])

if __name__=='__main__':unittest.main()
