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

if __name__=='__main__':unittest.main()
