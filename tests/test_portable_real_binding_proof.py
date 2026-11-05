"""Validation binding projection cannot copy quantities from GPU observations."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from world_real_binding_proof import binding_view
class BindingProof(unittest.TestCase):
 def data(self):
  p=dict(chars=[dict(name='n'+str(i)) for i in range(5)],effects=[dict(effect=dict(name='mode',type='weapon_change'),owner='n0'),dict(effect=dict(name='buff',type='buff'),owner='n1')],base_atk=[10,20,30,40,50])
  n=dict(active_weapon_modes=[dict(owner=3,definition=0,name='mode',shots=7)],query=dict(damage=[100,20,30,40,50]))
  m=dict(binding_source_indices=[0,0,0,0,0,1],binding_owners=[0,1,2,3,4,1]);return p,n,m
 def test_owner_and_source_identity_only_quantities_and_originals_preserved(self):
  p,n,m=self.data();before=copy.deepcopy((p,n,m));q,cpu=binding_view(p,n,m)
  self.assertEqual(cpu['active_weapon_modes'][0]['definition'],3);self.assertEqual(cpu['query'],n['query']);self.assertEqual(q['base_atk'],p['base_atk']);self.assertEqual(q['effects'][3]['owner'],'n3');self.assertEqual((p,n,m),before)
 def test_ambiguous_or_missing_native_binding_is_error(self):
  for sources,owners in [([0,0],[3,3]),([1],[3])]:
   p,n,m=self.data();m.update(binding_source_indices=sources,binding_owners=owners)
   with self.assertRaises(ValueError):binding_view(p,n,m)
 def test_malformed_dimensions_rejected(self):
  p,n,m=self.data();m['binding_owners']=[]
  with self.assertRaises(ValueError):binding_view(p,n,m)
if __name__=='__main__':unittest.main()
