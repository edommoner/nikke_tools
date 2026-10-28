"""Literal wire/ABI and original effect bindings, with no simulation values."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_named_range_battle_cases import fixtures
from world_named_range_battle_full_native import prepare_case
from portable_named_range_battle_wire import *
from portable_specs import LIMITS as L,FIELDS as F
class NamedRangeWire(unittest.TestCase):
    def test_original_definitions_survive_private_lowering_and_no_computed_values(self):
        c=fixtures()[0];before=copy.deepcopy(c);w,d=prepare_case(c);self.assertEqual(c,before);self.assertEqual(len(w),116224)
        self.assertEqual(w[BASE:BASE+4],[MAGIC,1,1,len(d[2])]);self.assertEqual(len(d[0]['effects']),87)
        self.assertEqual(set(d[1]['named_range_battle']['domains'].values()),{93,94})
        for original,stat in d[1]['named_range_battle']['domains'].items():
            row=d[1]['binding_source_indices'].index(original);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
            self.assertEqual(w[at+F['STAT']],stat);self.assertEqual(w[at+F['KIND']],0)
        self.assertFalse(d[1]['named_range_battle']['gpu_admitted']);self.assertLessEqual(END,OUTPUT)
    def test_shader_schema_and_explicit_entry_wire_agree(self):
        from portable_backend import validate_composed_stride
        check_schema(ROOT);validate_composed_stride(SOURCE,INPUT,OUTPUT)
        with self.assertRaises(ValueError):validate_composed_stride(SOURCE,115680,OUTPUT)
        with self.assertRaises(ValueError):validate_composed_stride(SOURCE,INPUT,1769856)
    def test_raw_cases_and_checked_source_inverse_are_complete(self):
        from portable_named_range_battle_source_contract import project_sources
        import json
        ledger=json.loads((ROOT/'tests/fixtures/portable-named-range-battle-source-delta.json').read_text());old=project_sources(ROOT)
        for name,row in ledger['files'].items():
            self.assertEqual(old[name],row['before'])
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
        s=importlib.util.spec_from_file_location('range_battle_adapter_test',ROOT/'research/verify-named-range-battle.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        rows,raw=a.prepare();self.assertEqual(len(rows),16);self.assertEqual(sum(d is not None for _,_,d in rows),4);self.assertEqual(len(raw),4+16*INPUT*4)
if __name__=='__main__':unittest.main()
