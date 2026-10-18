import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from quantity_specs import validate_quantity

class QuantitySourceTests(unittest.TestCase):
    def test_sources_are_independent_of_character_names(self):
        self.assertEqual(validate_quantity(dict(type='buff',stat='charge_dmg_pct',scaling='max_ammo_count')),(True,False))
        self.assertEqual(validate_quantity(dict(type='damage',stat='dealt_fixed_damage',target='target_body')),(False,True))
    def test_ambiguous_sources_fail_closed(self):
        for extra in ({'scaling':'stack_count'},{'tick_interval':1},{'hits_parts':False},{'target':'all_allies'},{'hit_count_gauge_ref':'count'}):
            with self.subTest(extra=extra),self.assertRaises(ValueError):validate_quantity(dict(dict(type='damage',stat='dealt_fixed_damage',target='target_body'),**extra))
        for extra in ({'type':'damage'},{'scaling_ref':'count'}):
            with self.subTest(extra=extra),self.assertRaises(ValueError):validate_quantity(dict(dict(type='buff',stat='charge_dmg_pct',scaling='max_ammo_count'),**extra))
    def test_compiled_quantity_modes_reject_wrong_operation_before_device(self):
        import engine_worker as a
        import detail_gpu as g
        names=['리타','크라운','앨리스','모더니아','N102'];chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in names]
        effect=dict(type='damage',name='fixed',stat='dealt_fixed_damage',target='target_body',fixed_value=50,trigger=dict(timing=['full_charge_hit'],condition=[]))
        stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in names}
        for field,value in ((4,0),(10,-4),(59,1),(39,128)):
            p=g.compile_effects(chars,[(effect,names[0])]);p['effects'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):g.run(None,[p],[[0,2,103,0,0,0,0,0]],[[0,0]],[stats])

if __name__=='__main__':unittest.main()
