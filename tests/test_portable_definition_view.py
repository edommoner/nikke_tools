"""Reject changed canonical fields, expressions, snapshots or override semantics."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_definition_view_contract import verify


class DefinitionViewTests(unittest.TestCase):
    def test_coordinate_receipt_delta_is_explicit_and_other_changes_are_rejected(self):
        names=['gpu/full_burst_landing_runtime.slang','gpu/coordinate_skill_runtime.slang','gpu/coordinate_area_runtime.slang','gpu/world_coordinate_full_burst_entry.slang']
        self.assertEqual(verify(ROOT)['reviewed_coordinate_full_burst_sources'],names)
        changes=[(names[0],'moveCoordinateReceipt(s,fromIndex,toIndex);','moveCoordinateReceipt(s,fromIndex+1,toIndex);'),
            (names[0],'begin=results[header];','begin=0;'),
            (names[1],'uint from=s.resourceOutput+CP_PACKETS+fromIndex*CP_SNAPSHOT_WORDS;','uint from=s.resourceOutput+CP_PACKETS+(fromIndex+1)*CP_SNAPSHOT_WORDS;'),
            (names[2],'return d.damagePending<=2;','return d.damagePending<=3;'),
            (names[3],'#define PORTABLE_FULL_BURST_LANDING','#define PORTABLE_FULL_BURST_LANDING_DISABLED')]
        for name,old,new in changes:
            source=(ROOT/name).read_text();self.assertIn(old,source)
            with self.subTest(name=name,old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

    def test_all55_properties_wire_snapshot_and_unchanged_shared_consumers(self):
        result=verify(ROOT);self.assertTrue(result['verified']);self.assertEqual(result['properties'],55);self.assertFalse(result['other_shared_sources_unchanged']);self.assertTrue(result['other_sources_outside_reviewed_delta_unchanged']);self.assertEqual(result['reviewed_scope_snapshot_sources'],['gpu/world_actor_state.slang'])

    def test_interrupt_frame_codec_and_group_delta_reject_other_changes(self):
        for name,old,new in [('gpu/event_runtime.slang','uint interruptReach;','uint interruptReach,extra;'),('gpu/world_interrupt_runtime.slang','WORLD_INTERRUPT_TOTAL_BASE=785424','WORLD_INTERRUPT_TOTAL_BASE=785422'),('gpu/world_interrupt_runtime.slang','dispatch(s,17,0,who,0,when,output,amount)','dispatch(s,17,0,who,0,when,output,ONE)'),('gpu/world_periodic_runtime.slang','interruptPacketSlot(from,i)','interruptPacketSlot(from,i+1)'),('gpu/interrupt_packet_codec.slang','index*7','index*8')]:
            source=(ROOT/name).read_text();self.assertIn(old,source)
            with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

    def test_scope_snapshot_changes_outside_exact_reviewed_delta_are_rejected(self):
        name='gpu/world_actor_state.slang';source=(ROOT/name).read_text()
        for old,new in [('return results[at];','return results[at+1];'),('actorStateQueryScopeSnapshot(at);','actorStateQueryScopeSnapshot(at+1);')]:
            with self.subTest(old=old),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

    def test_damage_factor_ledger_rejects_any_unreviewed_body_or_product(self):
        self.assertEqual(verify(ROOT)['reviewed_damage_factor_sources'],['gpu/damage_runtime.slang','gpu/damage_factors.slang'])
        for name,old,new in [('gpu/damage_runtime.slang','factors[7] = f3','factors[7] = ONE'),('gpu/damage_factors.slang','f64Div(factors[0],HUNDRED)','factors[0]')]:
            source=(ROOT/name).read_text();self.assertIn(old,source)
            with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

    def test_part_receipt_ledger_rejects_recalculation_and_bank_or_group_changes(self):
        for name,old,new in [('gpu/skill_part_receipt.slang','781328','781320'),('gpu/dispatch_phases.slang','frames[depth].healthValue=partAmount','frames[depth].healthValue=f.healthValue'),('gpu/counter_landing_runtime.slang','results[counterHead(s)+10]=1','results[counterHead(s)+10]=0'),('gpu/world_skill_runtime.slang','storeSkillPartAmount(at,r.partAmount)','storeSkillPartAmount(at,r.amount)')]:
            source=(ROOT/name).read_text();self.assertIn(old,source)
            with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})

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
