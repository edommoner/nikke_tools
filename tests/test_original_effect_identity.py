"""Equal display labels never choose the last registered damage definition."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from world_effect_identity import row,event_row
class IdentityTests(unittest.TestCase):
    def case(self):return dict(names=['A','B'],owners=[0,1],effects=[dict(name='same',type='damage'),dict(name='same',type='damage')],source_effect_identity=True)
    def test_source_row_and_owner_disambiguate_labels(self):
        c=self.case()
        self.assertEqual(row(c,dict(name='same',_portable_observer_row=0),'A'),0)
        self.assertEqual(row(c,dict(name='same',_portable_observer_row=1),'B'),1)
    def test_missing_forged_or_wrong_owner_identity_is_rejected(self):
        c=self.case()
        for index in [None,True,-1,2]:
            with self.assertRaises(ValueError):row(c,dict(name='same',_portable_observer_row=index),'A')
        with self.assertRaises(ValueError):row(c,dict(name='same',_portable_observer_row=0),'B')
        with self.assertRaises(ValueError):row(c,dict(name='wrong',_portable_observer_row=0),'A')
    def test_event_fallback_is_owner_aware_but_rejects_same_owner_ambiguity(self):
        c=self.case();ev=SimpleNamespace(skill_name='same',caster='B')
        self.assertEqual(event_row(c,ev),1)
        c['owners']=[1,1]
        with self.assertRaises(ValueError):event_row(c,ev)
if __name__=='__main__':unittest.main()
