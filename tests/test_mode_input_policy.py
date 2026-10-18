"""Operation policy is separate from owned growth and is a typed wire field."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
import detail_gpu as g
NAMES=['리타','크라운','앨리스','모더니아','N102']

class ModeInputPolicy(unittest.TestCase):
    def test_request_rejects_untyped_flags_before_execution(self):
        for flag in (0,1,'reload',None):
            with self.subTest(flag=flag),self.assertRaises(ValueError):a.evaluate({**body_for(NAMES,1),'weapon_mode_swap':flag})

    def test_operation_does_not_enter_owned_growth(self):
        body=body_for(NAMES,1);body['weapon_mode_swap']=True;original=copy.deepcopy(body['profile'])
        compiled=a.evaluate({**body,'_compile_gpu_detail':True})
        self.assertEqual(body['profile'],original)
        self.assertTrue(all(c['weapon_mode_swap'] for c in compiled['prepared'].squad))
        self.assertTrue(all('weapon_mode_swap' not in c for c in body['profile']['chars'].values()))

    def test_packet_extends_only_the_declared_operation_word(self):
        packets=[]
        for flag in (False,True):
            compiled=a.evaluate({**body_for(NAMES,1),'weapon_mode_swap':flag,'_compile_gpu_detail':True})
            packed=g.weapon_rows(compiled['program']['chars'],compiled['base_stats']);self.assertEqual(len(packed),5*169)
            packets.append([packed[i*169:(i+1)*169] for i in range(5)])
        for off,on in zip(*packets):self.assertEqual(off[:168],on[:168]);self.assertEqual((off[168],on[168]),(0,1))

if __name__=='__main__':unittest.main()
