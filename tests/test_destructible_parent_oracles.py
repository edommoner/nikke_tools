"""Real saved blocks retain every audit while the live parent reuses its oracle."""
import array,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('typed_parent_tests',ROOT/'research/verify-destructible-body-heal-share-retention-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from portable_parent_oracles import ParentOracles,provider
class DestructibleParentTests(unittest.TestCase):
    def test_all52_domains_have_the_same_direct_provider(self):
        rows,_=a.prepare();found=[provider(a,d) for _,_,d in rows if d is not None]
        self.assertEqual(len(found),52)
        for value in found:
            self.assertIs(value[0],a.__dict__);self.assertEqual(value[1],'native_reference');self.assertIs(value[2],a.native_reference)
    def test_real_old_and_shared_blocks_reuse_once_and_still_detect_corruption(self):
        from portable_specs import LIMITS as L
        rows,_=a.prepare();golden=json.loads((ROOT/'research/portable-destructible-body-heal-share-retention-short-expected.json').read_text())
        fixtures=[('portable-destructible-body-lifesteal-raw.json',18),('portable-destructible-body-heal-share-raw.json',49)]
        for filename,shift in fixtures:
            f=json.loads((ROOT/'tests/fixtures'/filename).read_text());r=f['records'][0];index=shift+r['index'];name,w,domain=rows[index]
            self.assertEqual(name,r['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),r['input_sha256'])
            block=array.array('I',[0])*f['output_words']
            for at,value in r['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),r['output_sha256'])
            # The old lifesteal block was at index0; its own saved trace stores
            # absolute scratch addresses. Only decoding is used here, not a
            # claim that the block has a different full-readback fingerprint.
            expected=golden['entries'][index]['native_sha256'];original=a.native_reference;calls=[]
            def witness(d):
                calls.append(d)
                if len(calls)>1:raise AssertionError('Fresh native executed during live-parent reuse')
                return original(d)
            with tempfile.TemporaryDirectory() as tmp,patch.object(a,'native_reference',witness):
                m=dict(package_id='real-saved-fixture',golden=dict(entries=[dict(native_sha256=expected)]));capture=Path(tmp);parent=ParentOracles(m,capture)
                try:
                    parent.prepare(a,[(name,w,domain)]);before=parent.before(0);n=a.native_reference(domain);parent.remember(0,before,n,a.cross.digest);parent.finish();parent.start(m,capture)
                    with parent.comparison(0):result=a.compare(block,domain)
                    self.assertEqual(a.cross.digest(result),expected);self.assertEqual(len(calls),1);self.assertEqual(parent.receipt()['reused_native_cases'],1)
                    # Only this unit's mutations use a copy of its verified
                    # oracle. Production independent audits remain fresh.
                    bad=array.array('I',block);bad[L['HEALTH_STATE_BASE']+9]^=0x40000000
                    with patch.object(a,'native_reference',return_value=copy.deepcopy(n)):
                        with self.assertRaises(AssertionError):a.compare(bad,domain)
                finally:parent.close()
            self.assertIs(a.native_reference,original)
if __name__=='__main__':unittest.main()
