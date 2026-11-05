"""Selection producer contracts, including synchronous generation replacement."""
import array,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('da_tests',ROOT/'research/verify-destructible-attack-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from destructible_attack_runtime import projectiles
from destructible_world_runtime import DestructibleWorld
from impact_specs import ActorHandle
from test_target_counter_runtime import manager,NAMES
class AttackTests(unittest.TestCase):
    def test_live_projectile_set_and_real_counter_children(self):
        rows={c['name'].split('/')[-1]:a.native_reference(c) for c in a.fixtures()}
        mixed=rows['mixed-live-only-projectiles'];self.assertEqual([r['handle'][0] for r in mixed['receipts']],[2,2])
        self.assertEqual([r['alive'] for r in mixed['state']],[False,False,True,True]);self.assertEqual(mixed['atk'],a.bits(11.))
        self.assertEqual(rows['new-generation']['receipts'][0]['handle'],[2,10,2]);self.assertEqual(rows['new-generation']['trace'],[])
        for name in ('only-shields-empty','delayed-empty'):self.assertEqual(rows[name]['receipts'],[])
        self.assertEqual(len(rows['high-slot128']['receipts']),128);self.assertEqual(rows['high-slot128']['receipts'][-1]['slot'],127)
        self.assertEqual(rows['high-slot128']['atk'],a.bits(11.))
        self.assertEqual(rows['miss-no-counter']['trace'],[]);self.assertTrue(all(r['alive'] for r in rows['miss-no-counter']['state']))
        self.assertEqual(rows['fractional-credit']['state'][0]['remaining'],a.bits(99.75))
    def test_packing_has_no_reference_or_gpu_calls(self):
        import portable_backend
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle during packing')),patch.object(portable_backend,'build',side_effect=AssertionError('No GPU')):
            rows,data=a.prepare()
        self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(15,9));self.assertEqual(len(data),4+15*102600*4)
    def test_selection_freezes_handles_before_synchronous_children(self):
        c=a.fixtures()[0];w=DestructibleWorld(c['nodes'],c['bindings']);bm=manager(c['effects']);bm.notify('battle_start',0,NAMES[0]);w.advance(0)
        original=bm.notify
        def notify(event,t,caster,**kw):
            result=original(event,t,caster,**kw)
            if event=='event:target_counter_complete:marker':
                old=w.targets.rows[1];w.targets.retire(1,old.handle);w.targets.spawn(1,ActorHandle(2,11,2),100)
            return result
        bm.notify=notify
        receipts=projectiles(w,bm,NAMES[2],1,2,1000.,1.,123)
        self.assertEqual(receipts[1][1],ActorHandle(2,11,1));self.assertFalse(receipts[1][2]['delivered']);self.assertEqual(w.targets.rows[1].remaining,100)
    def test_empty_selection_still_validates_packet_and_frame(self):
        c=a.fixtures()[5];w=DestructibleWorld(c['nodes'],c['bindings']);bm=manager(c['effects'])
        with self.assertRaises(ValueError):projectiles(w,bm,NAMES[2],1,2,1.)
        w.advance(0)
        for who,outcome,damage,credit in [('unknown',2,1.,1.),(NAMES[2],0,1.,0.),(NAMES[2],2,float('nan'),1.)]:
            with self.assertRaises(ValueError):projectiles(w,bm,who,1,outcome,damage,credit)
        self.assertTrue(all(r.alive for r in w.targets.rows))
    def test_saved_gpu_selection_identity_state_and_counter_trace_are_checked(self):
        from portable_backend import source_hashes
        from portable_specs import LIMITS as L
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-attack-raw.json').read_text())
        from portable_destructible_frame_source_contract import verify_retained_sources
        verify_retained_sources(ROOT,'gpu/destructible_attack_probe.slang',fixture['source_sha256'])
        rows,_=a.prepare()
        for record in fixture['records']:
            block=array.array('I',[0])*786432
            for i,v in record['nonzero']:block[i]=v
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            name,_,c=rows[record['index']];self.assertEqual(name,record['name'])
            if c is None:
                a.validate_rejection(block,name);block[0]=0
                with self.assertRaises(AssertionError):a.validate_rejection(block,name)
                continue
            a.compare(block,c)
            offsets=[710000,616386,705000,L['TARGET_COUNTER_QUERY_BASE']+4]
            if block[710000]:offsets.extend([710004,710007])
            for offset in offsets:
                corrupt=array.array('I',block);corrupt[offset]^=1
                with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):a.compare(corrupt,c)
if __name__=='__main__':unittest.main()
