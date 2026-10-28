"""ADD schedule is authored input; its independent oracle is original BossScript."""
import copy,hashlib,importlib.util,json,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator.boss_pattern import BossScript
from portable_add_attack_schedule import compile_add_schedule,INPUT_WORDS,OUTPUT_WORDS,STATE_BASE,QUEUE_BASE
from portable_add_attack_cases import fixtures
from world_add_attack_native import observe


class AddAttackScheduleTests(unittest.TestCase):
    def test_lowering_never_runs_the_native_clock_and_preserves_literals(self):
        for c in fixtures():
            before=copy.deepcopy(c)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU firing schedule as input')):w,p=compile_add_schedule(c)
            self.assertEqual(c,before);self.assertEqual(len(w),INPUT_WORDS)
            for node in p:
                if node.summon is None or node.summon.attack is None:continue
                at=2336+node.idx*8
                self.assertEqual(w[at:at+2],[node.summon.count,node.summon.attack.hits])
                self.assertEqual(struct.unpack('<d',struct.pack('<II',*w[at+2:at+4]))[0],node.summon.attack.interval)
                self.assertEqual(w[16+node.idx*64+6],0,'ADD shots must not become BODY shots')

    def test_original_queue_interleaves_sources_and_renews_generation(self):
        c=next(c for c in fixtures() if 'interleaved' in c['name']);_,p=compile_add_schedule(c);n=observe(c,p)
        initial=[r[:4] for r in n['queued_attacks'] if r[4:6]==[0,0]]
        self.assertEqual(initial,[[0,1,1,0],[0,2,1,0],[1,0,1,0],[2,1,1,0],[2,1,1,1],[2,1,1,2]])
        renewed=[r for r in n['queued_attacks'] if r[0]==0 and r[2]==2]
        self.assertTrue(renewed);self.assertEqual(renewed[0][:4],[0,1,2,0])
        self.assertEqual(n['states'][0][6],1,'Original finish retires the renewed ADDs too')

    def test_expiration_wins_over_a_same_time_due_shot(self):
        c=fixtures()[-1];_,p=compile_add_schedule(c);n=observe(c,p)
        self.assertEqual([r[3] for r in n['queued_attacks']],[0,1])

    def test_existing_scheduler_stays_closed_to_unconnected_add_attacks(self):
        from portable_world_schedule_specs import compile_schedule
        with self.assertRaisesRegex(ValueError,'Summon attack lifecycle'):compile_schedule(fixtures()[0])

    def test_source_and_wire_keep_cursor_ownership_and_no_runtime_growth(self):
        source=(ROOT/'gpu/world_add_attack_cursor.slang').read_text()
        self.assertIn('wsReached(when,due)',source)
        self.assertNotIn('Runtime',source)
        self.assertEqual(QUEUE_BASE-STATE_BASE,128*4)
        self.assertEqual(OUTPUT_WORDS-QUEUE_BASE,1024*8)

    def test_adapter_has_all_positive_and_raw_rejection_inputs(self):
        s=importlib.util.spec_from_file_location('add_schedule_adapter',ROOT/'research/verify-add-attack-schedule.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        rows,raw=m.prepare()
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(19,8))
        self.assertEqual(len(raw),4+len(rows)*INPUT_WORDS*4)
        for name,_,domain in rows:
            if domain is not None:self.assertIsInstance(m.native_reference(domain)['queued_attacks'],list)

    def test_readiness_anchors_the_independent_component_scope(self):
        from portable_readiness_semantics import enemy_ammo_prerequisites
        p=enemy_ammo_prerequisites();c=p['declared_add_firing_component']
        raw=(ROOT/c['evidence']).read_bytes();r=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),c['evidence_sha256'])
        self.assertEqual((r['input_count'],r['native_cases']),(19,8))
        self.assertTrue(r['calculation_verified']);self.assertEqual(r['gpu_calls'],0)
        self.assertFalse(c['full_battle_actor_pool_connected']);self.assertFalse(c['ammo_connected'])
        self.assertFalse(c['cuda_verified']);self.assertFalse(p['enemy_shot_reload_connected'])

    def test_registered_cache_path_preserves_every_case_and_requires_cubin(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        import nikke_gpu
        regular=nikke_gpu.SUITES['add-attack-schedule'];cached=nikke_gpu.SUITES['add-attack-schedule-cache-only']
        for key in ('script','source','golden','inputs','native','input_words','output_words'):self.assertEqual(regular[key],cached[key])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        self.assertNotIn('require_paired_generation',cached,'Standalone probe cannot require resident generation cache')


if __name__=='__main__':unittest.main()
