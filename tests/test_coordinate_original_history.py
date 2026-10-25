"""Retained histories must account for every omitted event explicitly."""
import array,copy,sys,unittest,struct,hashlib
from contextlib import nullcontext
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_roster_team_history import fractional_view

class OriginalHistoryTests(unittest.TestCase):
    def data(self,count):
        b=array.array('I',[0x57465231,min(count,2048),7,max(count-2048,0),0,0,0,0])
        n=dict(fractional_hits=list(range(count)),fractional_accumulators=[dict(value=.5)],damage=[12])
        return b,n
    def test_exact_retention_boundaries_keep_final_state_and_originals(self):
        for count in (0,2047,2048,2049,3870):
            b,n=self.data(count);before=copy.deepcopy((b,n));view,expected=fractional_view(b,n,0)
            self.assertEqual((b,n),before)
            self.assertEqual(expected['fractional_hits'],n['fractional_hits'][:2048])
            self.assertEqual(expected['fractional_accumulators'],n['fractional_accumulators'])
            self.assertEqual(expected['damage'],n['damage']);self.assertEqual(view[3],0)
    def test_wrong_count_omissions_magic_and_reserved_words_are_rejected(self):
        for offset in (0,1,3,4,5,6,7):
            b,n=self.data(3870);b[offset]+=1
            with self.assertRaises(AssertionError):fractional_view(b,n,0)
    def test_omission_without_overflow_is_rejected(self):
        b,n=self.data(2048);b[3]=1
        with self.assertRaises(AssertionError):fractional_view(b,n,0)

class ProjectileHistoryTests(unittest.TestCase):
    def data(self,count):
        from portable_projectile_specs import HEAD,TRACE,TRACE_COUNT
        block=array.array('I',[0])*(TRACE+TRACE_COUNT*16)
        block[HEAD:HEAD+4]=array.array('I',[0x57505231,min(count,TRACE_COUNT),max(0,count-TRACE_COUNT),0])
        shots=[dict(owner=i%5,kind='_fire',weapon_type='MG',time=i/60,pellets=1,muzzles=1) for i in range(count)]
        for i,s in enumerate(shots[:TRACE_COUNT]):
            block[TRACE+i*16:TRACE+(i+1)*16]=array.array('I',[s['owner'],2,*struct.unpack('<II',struct.pack('<d',s['time'])),1,1,*([0]*10)])
        return block,shots,{'MG':{'type':'auto_warmup'}}
    def test_retained_shots_and_exact_omissions_preserve_source(self):
        from portable_coordinate_projectile_history import legacy_view
        from portable_projectile_specs import HEAD
        for count in (0,2048,2103,2107):
            b,shots,mech=self.data(count);before=array.array('I',b)
            view=legacy_view(b,shots,mech);self.assertEqual(b,before);self.assertEqual(view[HEAD+2],0)
    def test_wrong_identity_amount_omission_or_reserved_data_fails(self):
        from portable_coordinate_projectile_history import legacy_view
        from portable_projectile_specs import HEAD,TRACE
        for at in [HEAD+1,HEAD+2,HEAD+4,TRACE,TRACE+1,TRACE+2,TRACE+4,TRACE+5,TRACE+6,TRACE+8,TRACE+15]:
            b,shots,mech=self.data(2103);b[at]+=1
            with self.assertRaises(AssertionError):legacy_view(b,shots,mech)

class ComparatorRefreshTests(unittest.TestCase):
    def api(self):
        digest=lambda b:hashlib.sha256(b).hexdigest()
        paths={'research/verify-coordinate-sampled-parent-short.py':'old','app/engine_worker.py':'fixed'}
        rows=lambda d:[dict(path=k,sha256=v) for k,v in d.items()]
        data=struct.pack('<III',1,4,5);entry=dict(name='original',input_sha256=digest(data[4:]),native_sha256='retained')
        old=dict(purpose='development',selected_cases=[],suite='coordinate-original',package_id='old',files=rows(paths),golden=dict(input_sha256=digest(data),entries=[entry]))
        spec=dict(code={'research/verify-coordinate-sampled-parent-short.py':dict(before='old',after='new')})
        api=SimpleNamespace(ROOT=Path('/unused'),forbid_gpu=nullcontext,verify_saved_package=lambda _:old,load=lambda _:spec,
            open_suite=lambda _:SimpleNamespace(suite=SimpleNamespace(INPUT=2)),prepare_entries=lambda *_:([('original',[4,5],object())],data),sha=digest)
        after=rows({**paths,'research/verify-coordinate-sampled-parent-short.py':'new'})
        return api,old,after
    def test_comparator_refresh_keeps_golden_and_never_calls_native(self):
        from portable_original_history_repackage import baseline
        api,old,rows=self.api();g,r=baseline(api,'coordinate-original','/unused',rows)
        self.assertEqual(g,old['golden']);self.assertEqual(r['native_domains_recomputed'],0)
        self.assertTrue(r['full_fresh_saved_replay_required']);self.assertFalse(r['calculation_verified'])
    def test_canonical_or_unreviewed_comparator_changes_are_rejected(self):
        from portable_original_history_repackage import baseline
        for path in ('app/engine_worker.py','research/verify-coordinate-sampled-parent-short.py'):
            api,old,rows=self.api()
            next(r for r in rows if r['path']==path)['sha256']='unreviewed'
            with self.assertRaises(ValueError):baseline(api,'coordinate-original','/unused',rows)
    def test_changed_prepared_input_is_rejected(self):
        from portable_original_history_repackage import baseline
        api,old,rows=self.api();old['golden']['input_sha256']='changed'
        with self.assertRaises(ValueError):baseline(api,'coordinate-original','/unused',rows)

if __name__=='__main__':unittest.main()
