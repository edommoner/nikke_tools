"""Group bindings preserve source definitions and reject ambiguous lowering."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_group_binding import lower
class GroupBindingTests(unittest.TestCase):
    def prepared(self):return dict(chars=[dict(name='A'),dict(name='B')],effects=[dict(owner='B',effect=dict(name='child',type='damage',stat='bonus_damage',target='target',trigger=dict(timing=['multi_hit:4'],condition=[])))])
    def test_threshold_and_owner_are_preserved_without_mutation(self):
        p=self.prepared();before=copy.deepcopy(p);q,original,owners=lower(p)
        self.assertEqual(p,before);self.assertEqual(original,p['effects']);self.assertEqual(owners,2)
        self.assertEqual(q['effects'][0]['effect']['trigger']['timing'],['event:__portable_attack_group_4'])
    def test_invalid_threshold_reserved_namespace_and_nonliteral_child_fail(self):
        for timing in ['multi_hit:0','multi_hit:129','multi_hit:04','event:__portable_attack_group_4']:
            p=self.prepared();p['effects'][0]['effect']['trigger']['timing']=[timing]
            with self.assertRaises(ValueError):lower(p)
        p=self.prepared();p['effects'][0]['effect']['tick_interval']=1
        with self.assertRaises(ValueError):lower(p)
if __name__=='__main__':unittest.main()
