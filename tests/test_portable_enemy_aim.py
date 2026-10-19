"""Admission of automatic add aim and preservation of existing command identities."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('aim_verifier',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from portable_specs import LIMITS as L

class EnemyAimAdmissionTests(unittest.TestCase):
    def template(self):return copy.deepcopy(next(c for c in v.fixtures() if c['name']=='enemy-auto-aim-initial-policy'))
    def test_policy_requires_one_boolean_per_squad_member(self):
        c=self.template()
        for malformed in [True,1,[],[True]*4,[True]*6,[1,False,False,False,False],(True,False,False,False,False)]:
            c['combat']['automatic_add_aim']=malformed
            with self.subTest(policy=malformed),self.assertRaisesRegex(ValueError,'five boolean'):v.compile_case(c)
        c['combat']['automatic_add_aim']=[True]*5
        words,_=v.compile_case(c);self.assertEqual(words[L['AIM_POLICY_BASE']],31)
    def test_policy_command_is_combat_owned_and_discrete(self):
        c=self.template()
        for owner,arg in [(5,1),(-1,1),(0,2),(0,-1),(True,1),(0,True)]:
            c['script']=[[0,27,0,owner,arg,-1,0,0]]
            with self.subTest(owner=owner,arg=arg),self.assertRaises(ValueError):v.compile_case(c)
        c['script']=[[0,27,0,0,1,-1,0,0]];c.pop('combat');c['effects']=c['effects'][:1];c['owners']=[0]
        with self.assertRaisesRegex(ValueError,'Combat command'):v.compile_case(c)
    def test_new_command_does_not_replace_cover_damage(self):
        c=self.template();c['script']=[[0,26,0,0,1,-1,25,0],[0,27,0,0,1,-1,0,0]]
        words,_=v.compile_case(c);self.assertEqual(words[L['COMMAND_BASE']],26);self.assertEqual(words[L['COMMAND_BASE']+8],27)

if __name__=='__main__':unittest.main()
