"""Lossless records beyond64, strict decoding, static opt-in and arena bounds."""
import array,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_battle_attack_group_input import compile_battle,COMPACT,COMPACT_WORDS,HEADER,LOG,SLOT_WORDS,OUTPUT_WORDS,PACKETS
from portable_battle_attack_group_cases import fixtures
from portable_specs import LIMITS as L
spec=importlib.util.spec_from_file_location('long_group_decoder',ROOT/'research/verify-world-attack-group-battle-short.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class LongGroupTests(unittest.TestCase):
    def test_static_optin_changes_only_history_flag(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU trace input')):
            case=fixtures()[1];p=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
            old,_=compile_battle(p,routing='native');new,_=compile_battle(p,routing='native',group_history='compact')
            self.assertEqual([i for i,(a,b) in enumerate(zip(old,new)) if a!=b],[104403])
            for value in (None,True,'truncate'):
                with self.assertRaises(ValueError):compile_battle(p,routing='native',group_history=value)
    def compact(self):
        block=array.array('I',[0])*OUTPUT_WORDS;block[HEADER+10]=1;block[HEADER+11]=65*28
        for i in range(65):
            at=COMPACT+i*28;block[at]=2;block[at+2]=i+1;block[at+4]=1
            if i<64:block[LOG+i*SLOT_WORDS:LOG+i*SLOT_WORDS+28]=block[at:at+28]
        return block
    def test_all65_records_are_preserved_without_hash_or_omission(self):
        block=self.compact();offsets=v.group_record_offsets(block,True,65)
        self.assertEqual([block[p+2] for p in offsets],list(range(1,66)))
        self.assertGreaterEqual(COMPACT,PACKETS+L['LANDINGS']);self.assertEqual(COMPACT+COMPACT_WORDS,OUTPUT_WORDS)
        with self.assertRaises(AssertionError):v.group_record_offsets(block,False,65)
    def test_truncation_extra_data_bad_count_and_prefix_are_rejected(self):
        for word,value in [(HEADER+11,COMPACT_WORDS+1),(HEADER+11,65*28-1),(HEADER+11,65*28+1),(COMPACT+64*28+4,129),(LOG+2,999)]:
            block=self.compact();block[word]=value
            with self.assertRaises(AssertionError):v.group_record_offsets(block,True,65)

if __name__=='__main__':unittest.main()
