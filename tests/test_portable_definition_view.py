"""Reject changed canonical fields, expressions, snapshots or override semantics."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_definition_view_contract import verify


class DefinitionViewTests(unittest.TestCase):
    def test_all55_properties_wire_snapshot_and_unchanged_shared_consumers(self):
        result=verify(ROOT);self.assertTrue(result['verified']);self.assertEqual(result['properties'],55)

    def test_changed_getter_signedness_or_override_is_rejected(self):
        name='gpu/event_runtime.slang';source=(ROOT/name).read_text()
        for old,new in [('definition_owner(_wireInput,_wireRow)','definition_kind(_wireInput,_wireRow)'),('property int budget','property uint budget'),('_overrideMask|=1U','_overrideMask&=1U'),('_route=newValue','_hits=newValue')]:
            with self.subTest(old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

    def test_changed_snapshot_initialization_or_wire_offset_is_rejected(self):
        name='gpu/definition_runtime.slang';source=(ROOT/name).read_text()
        for old,new in [('d._wireRow=row','d._wireRow=0'),('d._overrideMask=0','d._overrideMask=1'),('+D_OWNER]','+D_KIND]')]:
            with self.subTest(old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

    def test_changed_event_state_numeric_body_or_local_copy_site_is_rejected(self):
        for name,old,new in [('gpu/event_runtime.slang','s.sourceTime=when','s.sourceTime=0'),('gpu/landing_runtime.slang','d.damageHits=receipt.hits','d.damageHits=1'),('gpu/binary64.slang','uint','int')]:
            source=(ROOT/name).read_text();self.assertIn(old,source)
            with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

    def test_probe_literal_oracle_detects_wrong_copy_alias_and_raw_bit_loss(self):
        spec=importlib.util.spec_from_file_location('view_probe',ROOT/'research/verify-definition-view-short.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        entries,data=probe.prepare();self.assertEqual(len(entries),6)
        for name,words,domain in entries:
            expected=probe.native_reference(domain);correct=expected+[0]*(probe.suite.OUTPUT-len(expected));self.assertEqual(probe.compare(correct,domain),expected)
            for index in (2,3,4,5,7,9,11,13,14,17,18):
                changed=list(correct);changed[index]^=1
                with self.subTest(case=name,index=index),self.assertRaises(AssertionError):probe.compare(changed,domain)


if __name__=='__main__':unittest.main()
