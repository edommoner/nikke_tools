"""A real manager event drives shared activation and continuation ownership."""
import array,copy,hashlib,importlib.util,json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('df_tests',ROOT/'research/verify-destructible-frame-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class FrameTests(unittest.TestCase):
    def test_real_event_budget_and_late_root_sampling(self):
        answers={c['name'].split('/')[-1]:a.native_reference(c) for c in a.fixtures()};number=lambda x:struct.unpack('<d',bytes.fromhex(x))[0]
        self.assertEqual(answers['trigger-not-due']['activations'],0);self.assertEqual(answers['trigger-not-due']['receipts'],[])
        self.assertEqual(answers['manager-budget-once']['activations'],1);self.assertEqual(answers['two-root-attacks']['activations'],2)
        self.assertEqual(answers['empty-does-not-consume-budget']['activations'],0)
        self.assertEqual(len(answers['high-slot128']['receipts']),128);self.assertEqual(answers['high-slot128']['receipts'][-1]['slot'],127)
        self.assertEqual(number(answers['two-root-attacks']['sampled']['damage']),500.)
        self.assertEqual([number(r['remaining']) for r in answers['two-root-attacks']['state'][:2]],[50.,50.])
        named=answers['named-hit-child-after-counter'];self.assertEqual(named['activations'],2);self.assertEqual(number(named['atk']),32.)
        self.assertEqual(number(named['sampled']['damage']),595.)
        siblings=answers['siblings-refresh-before-death'];self.assertEqual(number(siblings['atk']),33.)
        self.assertEqual([(r['name'],r['reason'],r['epoch']) for r in siblings['trace']],[('first','threshold',1),('second','threshold',2),('second','death',3)])
    def test_existing_handler_is_restored_after_callback_failure(self):
        from destructible_frame_runtime import projectile_handler
        from destructible_world_runtime import DestructibleWorld
        from test_target_counter_runtime import manager,NAMES
        c=a.fixtures()[0];bm=manager(c['effects']);world=DestructibleWorld(c['nodes'],c['bindings']);world.advance(0.)
        bm.register_damage_handler(lambda *args:None);old=bm._damage_handler;resolver=bm._resolve_target
        def fail(*args):raise RuntimeError('observer failure')
        with self.assertRaisesRegex(RuntimeError,'observer failure'):
            with projectile_handler(bm,world,a.skill.character(c),base_attack=1000.,weapon=a.skill.engine_worker.META[NAMES[0]],defense=0.,attack_id=123,observe=fail):bm.notify('burst_cast',0.,NAMES[0])
        self.assertIs(bm._damage_handler,old)
        self.assertEqual(bm._resolve_target,resolver)
    def test_source_inverse_is_exact_and_cannot_hide_further_changes(self):
        from portable_destructible_frame_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-destructible-frame-source-delta.json').read_text());project_sources(ROOT)
        for name,row in data['sources'].items():
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})
    def test_typed_child_continuations_do_not_reenter_dispatch(self):
        source=(ROOT/'gpu/destructible_frame_runtime.slang').read_text()
        self.assertNotIn('dispatch(',source);self.assertIn('pushFrame(s,frames,depth,26',source)
        self.assertLess(715000+32*544,786416)
        rows,data=a.prepare();self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(26,17));self.assertEqual(len(data),4+26*102600*4)
    def test_saved_actual_frame_outputs_detect_budget_child_and_context_corruption(self):
        from portable_backend import source_hashes
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-frame-raw.json').read_text());self.assertEqual(fixture['source_sha256'],source_hashes('gpu/destructible_frame_probe.slang'))
        rows,_=a.prepare();by_name={name:(name,words,c) for name,words,c in rows}
        for record in fixture['records']:
            b=array.array('I',[0])*786432
            for i,v in record['nonzero']:b[i]=v
            self.assertEqual(hashlib.sha256(b.tobytes()).hexdigest(),record['output_sha256']);name,words,c=by_name[record['name']]
            self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            if c is None:
                a.validate_rejection(b,name);b[0]=0
                with self.assertRaises(AssertionError):a.validate_rejection(b,name)
                continue
            a.compare(b,c)
            for offset in [705008,705006,710000,705000,a.skill.L['COUNTER_CONTEXT_BASE']]:
                changed=array.array('I',b);changed[offset]^=1
                with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):a.compare(changed,c)
if __name__=='__main__':unittest.main()
