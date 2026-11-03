import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from engine_gpu_admission import require_supported,UnsupportedEngineKeys

class EngineGPUAdmissionTests(unittest.TestCase):
    def test_every_new_key_is_named(self):
        rows=[{'target':v} for v in ('self_and_engaged_allies','allies_down_all')]
        rows += [{'stat':v} for v in ('engaged_state','normal_atk_width_pct')]
        rows += [{'trigger':{'condition':[v]}} for v in ('during_full_charge','ally_down_count_above:1','ally_down_count_below:2')]
        for row in rows:
            with self.subTest(row=row),self.assertRaises(UnsupportedEngineKeys) as error:
                require_supported([row])
            self.assertIn(row['trigger']['condition'][0] if 'trigger' in row else next(iter(row.values())),str(error.exception))
        with self.assertRaisesRegex(UnsupportedEngineKeys,'hp_only_caster_based_pct'):
            require_supported([],['렐릭 베젤 큐브'])
        require_supported([{'target':'self','stat':'atk_pct','condition':['during_charge']}])

    def test_new_cube_rejected_on_legacy_and_shared_compilation_paths(self):
        import copy,engine_worker,portable_detail
        demo=engine_worker.detail_demo()
        body=dict(profile=demo['profile'],squad=demo['squad'],duration=3)
        body['profile']['chars'][body['squad'][0]]['cube']={'name':'렐릭 베젤 큐브','level':15}
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU battle forbidden')):
            for flag in ('_compile_gpu_detail','_compile_gpu'):
                with self.subTest(flag=flag),self.assertRaisesRegex(UnsupportedEngineKeys,'cube:렐릭 베젤 큐브'):
                    engine_worker.evaluate(dict(copy.deepcopy(body),**{flag:True}))
            with patch.object(portable_detail,'_execute_prepared',side_effect=AssertionError('GPU forbidden')):
                with self.assertRaisesRegex(UnsupportedEngineKeys,'max_stack:3'):
                    portable_detail.evaluate(dict(copy.deepcopy(body),compute_backend='metal_detail'))

    def test_real_character_rejected_without_cpu_battle_or_device(self):
        import engine_worker,portable_detail
        body=engine_worker.detail_demo()
        old=body['squad'][0];name='마리안 : 퀸'
        body['profile']['chars'][name]=body['profile']['chars'].pop(old)
        body['squad'][0]=name
        body.update(compute_backend='metal_detail',duration=3)
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU battle forbidden')),patch.object(portable_detail,'_execute_prepared',side_effect=AssertionError('GPU forbidden')):
            with self.assertRaisesRegex(UnsupportedEngineKeys,'engaged_state'):
                portable_detail.evaluate(body)

if __name__=='__main__':unittest.main()
