"""Compact aggregate rows preserve wire, labels, native domains and rejection gates."""
import array,importlib.util,struct,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('compact_regression',ROOT/'research/verify-world-regression-short.py');reg=importlib.util.module_from_spec(s);s.loader.exec_module(reg)

class CompactAggregateTests(unittest.TestCase):
    def adapter(self,rows,data=None):
        if data is None:data=struct.pack('<I',len(rows))+b''.join(struct.pack('<II',*r[1]) for r in rows)
        return types.SimpleNamespace(suite=types.SimpleNamespace(INPUT=2,OUTPUT=8),prepare=lambda:(rows,data))

    def combine(self,adapters):
        with patch.object(reg,'suite',types.SimpleNamespace(INPUT=2,OUTPUT=8)):return reg.combine(adapters)

    def test_wire_and_domain_identity_preserved_with_compact_rows(self):
        domain={'native':'same object'};words=[0xffffffff,17]
        entries,raw=self.combine(dict(first=self.adapter([('native',words,domain)]),second=self.adapter([('reject',[64,0],None)])))
        self.assertEqual(raw,struct.pack('<IIIII',2,0xffffffff,17,64,0))
        self.assertEqual([e[0] for e in entries],['first/native','second/reject'])
        self.assertTrue(all(isinstance(e[1],array.array) and e[1].typecode=='I' for e in entries))
        self.assertIs(entries[0][2][1],domain);self.assertIsNone(entries[1][2]);self.assertEqual(words,[0xffffffff,17])
        entries[0][1][0]=0;self.assertEqual(words[0],0xffffffff)

    def test_bad_header_size_words_or_domain_stride_still_rejected(self):
        rows=[('case',[1,2],None)]
        for data in (struct.pack('<III',2,1,2),struct.pack('<II',1,1),struct.pack('<IIII',1,1,2,3),struct.pack('<III',1,1,3)):
            with self.subTest(data=data),self.assertRaisesRegex(ValueError,'input/header mismatch'):
                self.combine(dict(family=self.adapter(rows,data)))
        with self.assertRaisesRegex(ValueError,'row stride mismatch'):
            self.combine(dict(family=self.adapter([('case',[1],None)],struct.pack('<III',1,1,2))))
        bad=self.adapter(rows);bad.suite.OUTPUT=9
        with self.assertRaisesRegex(ValueError,'exact wire strides'):self.combine(dict(family=bad))

    def test_duplicate_identity_and_out_of_range_word_remain_failures(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            self.combine(dict(family=self.adapter([('case',[1,2],None),('case',[3,4],None)])))
        with self.assertRaises((OverflowError,ValueError)):
            self.combine(dict(family=self.adapter([('case',[-1,2],None)],struct.pack('<III',1,0xffffffff,2))))

if __name__=='__main__':unittest.main()
