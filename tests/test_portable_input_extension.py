import hashlib,json,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_input_extension import verify_extension
from portable_cover_policy_specs import INPUT_BASE,INPUT_WORDS,empty
class InputExtensionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.old=Path(self.tmp.name)/'old';self.new=Path(self.tmp.name)/'new';self.old.mkdir();self.new.mkdir()
        self.prefix=b'\1\0\0\0'*INPUT_BASE;self.suffix=struct.pack('<'+str(INPUT_WORDS)+'I',*empty())
    def write(self,path,rows):
        raw=struct.pack('<I',len(rows))+b''.join(b for _,b in rows);(path/'input.bin').write_bytes(raw)
        return dict(input_sha256=hashlib.sha256(raw).hexdigest(),entries=[dict(name=n,input_sha256=hashlib.sha256(b).hexdigest()) for n,b in rows])
    def test_registered_default_extension_preserves_literal_prefix(self):
        old=self.write(self.old,[('old',self.prefix)]);new=self.write(self.new,[('added',self.prefix+self.suffix),('old',self.prefix+self.suffix)])
        same,r=verify_extension(self.old,old,self.new,new,'coordinate-policy-v1');self.assertEqual(same,{'old':True});self.assertTrue(r['all_inputs_rehashed']);self.assertEqual(r['gpu_calls'],0)
    def test_nondefault_extension_and_changed_prefix_are_not_equivalent(self):
        old=self.write(self.old,[('old',self.prefix)])
        for value in (self.prefix+b'\1'+self.suffix[1:],b'\2'+self.prefix[1:]+self.suffix):
            new=self.write(self.new,[('old',value)]);same,_=verify_extension(self.old,old,self.new,new,'coordinate-policy-v1');self.assertFalse(same['old'])
    def test_whole_and_case_hashes_are_required(self):
        old=self.write(self.old,[('old',self.prefix)]);new=self.write(self.new,[('old',self.prefix+self.suffix)])
        for where in ('input_sha256','entries'):
            bad=json.loads(json.dumps(new))
            if where=='entries':bad['entries'][0]['input_sha256']='0'*64
            else:bad[where]='0'*64
            with self.assertRaises(ValueError):verify_extension(self.old,old,self.new,bad,'coordinate-policy-v1')
    def test_squad_default_extension_and_changed_prefix(self):
        from portable_squad_control_specs import INPUT_BASE as B,INPUT_WORDS as W,empty as E
        prefix=b'\1\0\0\0'*B;suffix=struct.pack('<'+str(W)+'I',*E())
        old=self.write(self.old,[('old',prefix)])
        new=self.write(self.new,[('old',prefix+suffix)])
        same,r=verify_extension(self.old,old,self.new,new,'coordinate-squad-v1');self.assertTrue(same['old']);self.assertEqual(r['input_prefix_words'],109656)
        new=self.write(self.new,[('old',b'\2'+prefix[1:]+suffix)])
        same,_=verify_extension(self.old,old,self.new,new,'coordinate-squad-v1');self.assertFalse(same['old'])
    def test_unknown_contract_rejected_before_file_access(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):verify_extension('/missing',{},'/missing',{},'ignore-input')
    def test_burst_default_extension_requires_exact_disabled_descriptor(self):
        from portable_burst_control_specs import INPUT_BASE as B,WORDS as W,empty as E
        prefix=b'\1\0\0\0'*B;suffix=struct.pack('<'+str(W)+'I',*E())
        old=self.write(self.old,[('old',prefix)]);new=self.write(self.new,[('old',prefix+suffix)])
        same,r=verify_extension(self.old,old,self.new,new,'coordinate-burst-control-v1');self.assertTrue(same['old']);self.assertEqual(r['input_prefix_words'],109792)
        for at in (0,8,len(suffix)-1):
            changed=bytearray(suffix);changed[at]^=1
            new=self.write(self.new,[('old',prefix+changed)])
            same,_=verify_extension(self.old,old,self.new,new,'coordinate-burst-control-v1');self.assertFalse(same['old'])
if __name__=='__main__':unittest.main()
