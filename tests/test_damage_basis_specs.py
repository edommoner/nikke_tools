import copy,sys,unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'app'),str(Path(__file__).resolve().parents[1]/'scripts')]
import engine_worker
import detail_gpu as g
from damage_basis_specs import damage_basis

class DamageBasisSpecTests(unittest.TestCase):
 def test_modes_units_and_invalid_combinations(self):
  for mode,code in (('max_hp_additive',1),('max_hp_replacement',2)):
   self.assertEqual(damage_basis(dict(type='damage',scaling=mode,scaling_hp_pct=10)).mode,code)
   for changes in ({'type':'buff'},{'scaling_hp_pct':True},{'scaling_hp_pct':-1},{'scaling_hp_pct':float('nan')},{'scaling_hp_pct':None},{'scaling_ref':'state'}):
    with self.subTest(mode=mode,changes=changes),self.assertRaises(ValueError):damage_basis(dict(type='damage',scaling=mode,scaling_hp_pct=10,**changes) if not set(changes)&{'type','scaling_hp_pct'} else {**dict(type='damage',scaling=mode,scaling_hp_pct=10),**changes})
  self.assertEqual(damage_basis({'scaling':'stack_count'}).mode,0)
  with self.assertRaises(ValueError):damage_basis(dict(type='damage',scaling_hp_pct=10))
 def fixtures(self):
  names=['리타','크라운','앨리스','모더니아','N102'];chars=[dict(name=n,skill_levels={'1':10},_weapon=engine_worker.META[n]) for n in names]
  e=dict(source='스킬1',name='effect',type='buff',stat='max_ammo_pct',fixed_value=-50,target='all_allies',duration=10,trigger={'timing':['battle_start'],'condition':[]})
  return names,chars,e
 def test_group_identity_and_activation_predicates(self):
  names,chars,e=self.fixtures();a={**e,'_quant_group':'shared'};b={**a,'name':'other','max_ammo_reduction_exclusive':True}
  p=g.compile_effects(chars,[(a,names[0]),(b,names[0])]);self.assertNotEqual(p['effects'][0][45],p['effects'][1][45]);self.assertEqual(p['effects'][1][55],1)
  for condition,code in (('self_undying',38),('no_broken_cover_ally',39)):
   effect={**e,'stat':'atk_pct','trigger':{'timing':['burst_cast'],'condition':[condition]}}
   self.assertEqual(g.compile_effects(chars,[(effect,names[0])])['effects'][0][15],code)
   effect['trigger']['timing']=['passive']
   with self.assertRaises(g.UnsupportedDetail):g.compile_effects(chars,[(effect,names[0])])
  for changes in ({'stat':'atk_pct'},{'type':'instant'},{'max_ammo_reduction_exclusive':1},{'target':'target'}):
   with self.subTest(changes=changes),self.assertRaises(g.UnsupportedDetail):g.compile_effects(chars,[({**b,**changes},names[0])])
 def test_forged_instruction_fields_are_rejected_before_cuda(self):
  names,chars,e=self.fixtures();program=g.compile_effects(chars,[(e,names[0])])
  for changes in ({53:3},{53:1,54:10},{54:10},{55:2},{45:g.NE}):
   forged=copy.deepcopy(program)
   for field,value in changes.items():forged['effects'][0][field]=value
   with self.subTest(changes=changes),self.assertRaises(ValueError):g.run(None,[forged],[[0,2,0,0,-1,0,0,0]],[[0,0]],[{}])

if __name__=='__main__':unittest.main()
