"""Explicit address relocation checks both ends, preserving every other word."""
import copy,hashlib,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_partitioned_addresses as addresses


class AddressViewTests(unittest.TestCase):
    def row(self,local=0,receipt=2,depth=1):
        row=bytearray(addresses.WORDS*4);field=addresses.DFS_BASE+depth*544+530;target=addresses.RECEIPT_BASE+(receipt-1)*1040
        struct.pack_into('<II',row,field*4,local*addresses.WORDS+target,receipt);struct.pack_into('<I',row,target*4,receipt)
        struct.pack_into('<I',row,100*4,0xdeadbeef)
        return row,field,target
    def test_local_and_logical_addresses_target_the_same_unchanged_receipt(self):
        row,field,target=self.row(local=12);original=bytes(row)
        count,changes=addresses.logical_row_inplace(row,12,16)
        self.assertEqual(count,1);self.assertEqual(len(changes),1)
        self.assertEqual(struct.unpack_from('<I',row,field*4)[0],28*addresses.WORDS+target)
        self.assertEqual(row[:field*4],original[:field*4]);self.assertEqual(row[(field+1)*4:],original[(field+1)*4:])
    def test_no_exclusions_for_zero_unowned_wrong_target_or_wrong_receipt(self):
        for kind in ('unowned','target','id','signature'):
            row,field,target=self.row()
            if kind=='unowned':struct.pack_into('<I',row,(field+1)*4,0)
            elif kind=='target':struct.pack_into('<I',row,field*4,target+1)
            elif kind=='id':struct.pack_into('<I',row,(field+1)*4,129)
            else:struct.pack_into('<I',row,target*4,1)
            original=bytes(row)
            with self.subTest(kind=kind),self.assertRaises(ValueError):addresses.logical_row_inplace(row,0,16)
            self.assertEqual(row,original)
    def test_first_batch_has_identity_view_but_still_checks_references(self):
        row,_,_=self.row(local=3);original=bytes(row);count,changes=addresses.logical_row_inplace(row,3,0)
        self.assertEqual(count,1);self.assertEqual(changes,[]);self.assertEqual(row,original)
    def test_bounds_and_typed_indices_fail_closed(self):
        for row,local,first in ((bytearray(4),0,0),(bytearray(addresses.WORDS*4),False,0),(bytearray(addresses.WORDS*4),0,65535)):
            with self.assertRaises(ValueError):addresses.logical_row_inplace(row,local,first)

    def test_numerical_changes_are_never_excluded_from_the_logical_view(self):
        row,_,_=self.row();expected=hashlib.sha256(row).hexdigest();struct.pack_into('<I',row,40,0xf00dcafe)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'raw';path.write_bytes(row)
            layout=dict(output_words=addresses.WORDS,output_bytes=len(row),input_count=1,batch_size=1,batches=[dict(first_case=0,cases=1)])
            with self.assertRaisesRegex(ValueError,'Non-address words'):addresses.view_file(path,layout,[dict(name='numeric',output_sha256=expected)])


if __name__=='__main__':unittest.main()
