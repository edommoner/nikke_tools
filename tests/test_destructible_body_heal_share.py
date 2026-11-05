"""Actual recipient clamping, source accounting and complete original effects."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('typed_share_tests',ROOT/'research/verify-destructible-body-heal-share-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class BodyHealShareTests(unittest.TestCase):
    def test_complete_original_rosters_pack_without_cpu_hit_inputs(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU event input')):rows,data=a.prepare()
        self.assertEqual(len(rows),12);self.assertEqual(len(data),4+12*110112*4)
        original=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())
        for _,_,(c,m,p,_) in rows:
            self.assertEqual(len(p['effects']),73)
            for owner in c['body']['squad']:
                actual=[r['effect'] for r in p['effects'] if r['owner']==owner and r['effect'].get('source') in ('스킬1','스킬2','스킬3')]
                self.assertEqual(actual,[r for r in original[owner] if not r.get('favorite',0)])
    def test_native_receipts_are_per_recipient_and_queries_not_added(self):
        from world_destructible_accum_native import observe as plain
        c=a.fixtures()[0];before=copy.deepcopy(c);n=a.native_reference((c,));baseline,_=plain(c)
        stripped=copy.deepcopy(n);stripped.pop('healing_recipients');stripped.pop('heal_share_events');self.assertEqual(stripped,baseline);self.assertEqual(c,before)
        self.assertTrue(any(r['owner'] in (2,3) and r['after']>r['before'] for r in n['healing_recipients']))
        self.assertGreater(len(n['healing_recipients']),len(n['healing']))
    def test_recipient_observer_restores_scopes_after_failure(self):
        from calculator import timeline,buff_manager
        from runner import sim
        from effect_runtime import CATALOG
        def snapshot():return (sys.getprofile(),timeline.simulate,sim.simulate,buff_manager.BuffManager.register_damage_handler,buff_manager.BuffManager.apply_shared_body_heal)
        before=snapshot();original=CATALOG.emit
        def fail(event,*args,**kwargs):
            if event=='before_body_heal':raise RuntimeError('injected body clamp failure')
            return original(event,*args,**kwargs)
        with patch.object(CATALOG,'emit',side_effect=fail):
            with self.assertRaisesRegex(RuntimeError,'injected body clamp failure'):a.observe(a.fixtures()[0])
        self.assertEqual(snapshot(),before)
    def test_saved_all_recipient_healing_and_wrong_attribution_rejected(self):
        from portable_backend import source_hashes
        from portable_specs import LIMITS as L
        f=json.loads((ROOT/'tests/fixtures/portable-destructible-body-heal-share-raw.json').read_text());rows,_=a.prepare()
        from portable_attack_group_source_contract import retained_source_hashes
        self.assertEqual(f['source_sha256'],retained_source_hashes(ROOT,'gpu/destructible_roster_accum_entry.slang'));checked=0
        for r in f['records']:
            name,w,domain=rows[r['index']];self.assertEqual(name,r['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),r['input_sha256'])
            block=array.array('I',[0])*f['output_words']
            for at,value in r['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),r['output_sha256'])
            n=a.native_reference(domain);a.shared_compare(block,domain,copy.deepcopy(n))
            faults=[base+who*10+9 for base in (L['HEALTH_STATE_BASE'],L['HEALTH_QUERY_BASE']) for who in range(5)]
            faults.extend((L['HEALTH_STATE_BASE']+21,L['HEALTH_QUERY_BASE']+31))
            for offset in faults:
                bad=array.array('I',block);bad[offset]^=0x40000000
                with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):a.shared_compare(bad,domain,copy.deepcopy(n))
                checked+=1
            bad=copy.deepcopy(n);bad['healing_recipients']=bad['healing']
            with self.assertRaises(AssertionError):a.shared_compare(block,domain,bad)
            c,m,p,w=domain;c=copy.deepcopy(c);c.pop('body_heal_sharing_v1')
            with self.assertRaisesRegex(AssertionError,'recipient receipts'):a.shared_compare(block,(c,m,p,w),copy.deepcopy(n))
        self.assertEqual(checked,24)
if __name__=='__main__':unittest.main()
