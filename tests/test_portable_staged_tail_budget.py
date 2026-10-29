"""Keep native work small without paying a fresh process for each rejection."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_staged_continuation as cont
import portable_continuation_package as capsule
import test_portable_staged_continuation as fixture


class TailBudgetTests(unittest.TestCase):
    def test_exact_membership_splits_real_battles_and_keeps_rejection_coverage(self):
        self.assertEqual(cont.tail_groups(15,0,1,native_indices=[0,1,2],reject_group_size=12),[[0],[1],[2],list(range(3,15))])
        self.assertEqual(cont.tail_groups(8,2,1,native_indices=[0,3,6],reject_group_size=2),[[2],[3],[4,5],[6],[7]])
        self.assertEqual(cont.tail_groups(5,1,2),[[1,2],[3,4]])
        for size in (0,-1,True,16,'12'):
            with self.subTest(size=size),self.assertRaises(ValueError):cont.tail_groups(15,0,1,native_indices=[0],reject_group_size=size)
        for native in (None,[True],[2,1],[0,0],[-1],[15]):
            with self.subTest(native=native),self.assertRaises(ValueError):cont.tail_groups(15,0,1,native_indices=native,reject_group_size=12)

    def test_resume_binds_rejection_budget_and_preserves_failed_and_completed_evidence(self):
        f=fixture.ContinuationTests();f.setUp();self.addCleanup(f.doCleanups)
        before=list(f.f.calls)
        cont.resume(f.c,f.tx,f.f.tx,1,'metal',reject_group_size=2)
        self.assertEqual(f.f.calls,before)
        c=fixture.cli.load(f.tx/'transaction.json');self.assertEqual(c['reject_group_size'],2)
        self.assertEqual(c['case_groups'],[[2]])
        fixture.flow.context(f.c,f.tx)
        for change in (dict(reject_group_size=None),dict(reject_group_size=True),dict(case_groups=[[1,2]])):
            fixture.cli.write(f.tx/'transaction.json',dict(c,**change))
            with self.subTest(change=change),self.assertRaises(ValueError):fixture.flow.context(f.c,f.tx)
        self.assertEqual(fixture.cli.load(f.failed/'execution.json'),f.facts)

    def test_wrapper_forwards_only_explicit_optional_decimal_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);request=dict(parent_transaction=str(root/'parent'),group_size='1',reject_group_size='12')
            plan=fixture.packet.recipe('owner','preflight-resume','cuda',root/'out',root/'original',180,request)
            args=fixture.packet.proof_arguments(plan)
            self.assertEqual(args[-2:],['--reject-group-size','12'])
            for bad in (dict(request,extra='1'),dict(request,reject_group_size=True),dict(request,reject_group_size='-1')):
                with self.assertRaises(ValueError):fixture.packet.recipe('owner','preflight-resume','cuda',root/'out',root/'original',180,bad)


class FullOwnerTests(unittest.TestCase):
    def original(self):
        return dict(package_id='old',purpose='sealed',suite='x',golden={'same':1},files=[dict(path=n,bytes=1,sha256='old') for n in (*capsule.FULL_REPLACED,'tests/test_portable_staged_continuation.py','gpu/x.slang')])

    def test_full_owner_preserves_original_tests_and_every_noncontroller_byte(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'gpu-package.json').write_text('{}')
            original=self.original();schema,replaced,added=capsule.layout(original)
            self.assertEqual(schema,capsule.FULL_SCHEMA)
            self.assertNotIn('tests/test_portable_staged_continuation.py',replaced)
            current=copy.deepcopy(original);current['controller_continuation']=dict(schema=schema,base_package_id='old',base_manifest_sha256=fixture.cli.sha(b'{}'),replaced=list(replaced),added=list(added))
            current['files']+=[dict(path=n,bytes=0,sha256='new') for n in added]
            from types import SimpleNamespace
            cli=SimpleNamespace(ROOT=root,sha=fixture.cli.sha)
            for name in replaced:(root/name).parent.mkdir(parents=True,exist_ok=True);(root/name).write_text('controller')
            with patch.object(capsule,'source_guard') as guard:
                capsule.validate_lineage(cli,current,original,root);guard.assert_called_once()
                for name in ('gpu/x.slang','tests/test_portable_staged_continuation.py'):
                    bad=copy.deepcopy(current);next(r for r in bad['files'] if r['path']==name)['sha256']='changed'
                    with self.subTest(name=name),self.assertRaisesRegex(ValueError,'native/GPU/data/test'):capsule.validate_lineage(cli,bad,original,root)
                bad=copy.deepcopy(current);bad['payload_projection']={}
                with self.assertRaisesRegex(ValueError,'inventory'):capsule.validate_lineage(cli,bad,original,root)

    def test_partial_controller_or_second_extension_is_rejected(self):
        old=self.original();old['files'].pop(0)
        with self.assertRaises(ValueError):capsule.layout(old)
        old=self.original();old['files'].append(dict(path=capsule.FULL_ADDED[0],bytes=1,sha256='old'))
        with self.assertRaises(ValueError):capsule.layout(old)


if __name__=='__main__':unittest.main()
