"""Real product parity at the first localized late-random query divergences."""
import array
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
import portable_detail as product
from portable_native import HOST_THREADS
from portable_backend import execute
from portable_specs import LIMITS as L


class TeamSearchS4Tests(unittest.TestCase):
    def check_squad(self, squad_id, duration):
        settings = json.loads((ROOT / 'research/team-search/s1-inputs.json').read_text())
        base = json.loads(Path(settings['benchmark']).read_text())[0]
        base.update(settings['settings'])
        rows = [json.loads(line) for line in
                (ROOT / 'research/team-search/s1-results.jsonl').read_text().splitlines()]
        token = HOST_THREADS.set(1)
        try:
            with tempfile.TemporaryDirectory(prefix='s4-parity-') as tmp:
                from unittest.mock import patch
                with patch.dict(os.environ, NIKKE_DETAIL_CAPTURE_ROOT=tmp):
                    answer = product.evaluate_many([dict(base, squad=rows[squad_id]['members'],
                        duration=duration, compute_backend='native_detail', verify_detail=True)],
                        verification='full')[0]
                self.assertNotIn('error', answer)
                compute = answer['result']['compute']
                self.assertEqual(compute['backend'], 'native_detail')
                self.assertTrue(compute['cpu_verification']['matched'])
        finally:
            HOST_THREADS.reset(token)

    def test_empty_pending_exclusion_reuses_ordinary_query(self):
        # timeline.py:3885/4026-4059 and buff_manager.py:4556: empty set key.
        self.check_squad(17, 4)

    def test_dot_refresh_invalidates_numeric_query(self):
        # buff_manager.py:3651: Kurumi refresh at 5.933333333333318s.
        self.check_squad(127, 6.2)

    def test_auto_reload_start_invalidates_numeric_query(self):
        # timeline.py:3217: 2B starts reloading before Snow White's query.
        self.check_squad(17, 49)

    def test_nonempty_mode_charge_has_no_prestart_query(self):
        # timeline.py:2024/2072: E.H.'s first mode charge at 3.2s.
        self.check_squad(238, 3.25)

    def test_percentage_only_sync_preserves_cached_numeric_buffs(self):
        # Soline's first affected shot is at 15.000000000000325s.
        self.check_squad(743, 15.05)

    def test_last_mode_charge_invalidates_before_base_ammo_restore(self):
        # E.H.: charge-end bump, restoration query, mode-end bump, landing.
        self.check_squad(238, 4)

    def test_final_periodic_tick_keeps_resident_max_hp_until_removal(self):
        # Mast: the last 37 hits use t=10.099899999999995s.
        self.check_squad(1410, 10.2)

    def test_damage_query_does_not_resolve_direct_healing_rank(self):
        # Sakura SR's lowest-HP buff resolves at the first heal, after the
        # Flora HP grant, rather than the preceding damage-stat query.
        self.check_squad(1189, 5)

    def test_equal_nonempty_pending_exclusions_share_query(self):
        # At 123.5833333333276s, Isabel's two pending rows both exclude only
        # Sonic Chaser 5. The early burst has different cast-count branches.
        self.check_squad(404, 124)

    def test_adjacent_hp_max_waits_for_previous_actor_notification(self):
        # Flora's own full-HP notice must finish before her neighbour's
        # percentage is synchronized and emits its independent crossing.
        self.check_squad(1626, 5.1)

    def test_cleanse_invalidates_after_stripping_harmful_members(self):
        # Sora's cleanse at 62.58333333333106s must clear her cast query.
        self.check_squad(255, 63)

    def test_post_reload_wait_does_not_query_after_completion_callbacks(self):
        # timeline.py:1504-1522: Jill's completion at 3.4166666666666594s
        # grants two carriers, then waits without querying her buffs again.
        self.check_squad(823, 5)

    def test_logical_mode_activation_invalidates_before_weapon_entry(self):
        # buff_manager.py:3733: Laplace activates at 3.1999999999999935s,
        # between her burst-controller query and first mode weapon query.
        self.check_squad(819, 5)

    def test_capped_stack_add_preserves_numeric_query_without_recipient_stacks(self):
        # buff_manager.py:3516-3527: Mica's capped ordinary carriers at
        # 50.08333333333177s leave the dictionary cached for her landing.
        self.check_squad(1081, 50.12)

    def test_finite_hp_modifier_enables_canonical_boundary_observation(self):
        # reference_health_runtime.py:18-20: Bay's heal must not become
        # the first observation of an HP value already published at a boundary.
        self.check_squad(462, 33.15)

    def test_cleanse_without_hp_modifiers_keeps_first_heal_observation(self):
        # reference_health_runtime.py:15-20,95-97: Sora first synchronizes
        # the five full-HP actors during her heal at 15.583333333333687s.
        self.check_squad(2374, 16)

    def test_sentinel_charge_mode_refill_does_not_query_base_capacity(self):
        # timeline.py:2587-2590: Guilty's first sentinel charge at 3.2s.
        self.check_squad(1567, 3.25)

    def test_direct_heal_reader_invalidates_when_freezing_a_pending_selector(self):
        # buff_manager.py:2765-2768: Pascal freezes Lily's heal-received
        # recipient at 120.01666666666114s, after his cast dictionary query.
        self.check_squad(258, 120.05)

    def test_new_dot_and_staged_stack_updates_invalidate_numeric_queries(self):
        # buff_manager.py:3666 and installed staged_dot_runtime.py:59,73:
        # first registration at 17.8s and ten scoped staged applications.
        self.check_squad(2284, 21)

    def test_zero_lifesteal_read_does_not_publish_new_lazy_hp_percentages(self):
        # timeline.py:5160-5164: Brid's zero-lifesteal landing resolves
        # Rapunzel's HP recipients but does not synchronize their percentages
        # before Soline's first dictionary read at 30.016666666666243s.
        self.check_squad(2349, 30.05)

    def test_global_named_remove_invalidates_even_without_a_resident(self):
        # buff_manager.py:1531 invalidates even when to_remove is empty.
        fixture = json.loads((ROOT / 'tests/fixtures/team-search-s2-v1.json').read_text())
        squad = next(case['squad'] for case in fixture['cases'] if case['id'] == 366)
        prepared, _ = product.prepare(dict(fixture['base'], squad=squad, duration=1))
        reader = copy.deepcopy(next(row for row in prepared['effects']
            if row['effect'].get('stat') == 'atk_caster_based_pct'
            and row['effect'].get('target') == 'allies_random:1'))
        reader['effect']['trigger'] = dict(timing=['every:15s'], condition=[])
        epochs = []
        for remove in (False, True):
            case = copy.deepcopy(prepared)
            case['effects'] = [copy.deepcopy(reader)]
            if remove:
                case['effects'].append(dict(owner=reader['owner'], effect=dict(
                    source='스킬1', type='instant', name='empty removal',
                    stat='remove_named_buff', target='self', target_effect='absent',
                    trigger=dict(timing=['battle_start'], condition=[]))))
            source, iw, ow, words, _ = product.compile_product(case)
            with tempfile.TemporaryDirectory(prefix='s4-empty-removal-') as tmp:
                path = Path(tmp) / 'readback.bin'
                execute(source, 'portableEvents', array.array('I', [1, *words]).tobytes(),
                        iw, ow, 'native', readback_path=path)
                raw = array.array('I'); raw.frombytes(path.read_bytes())
                self.assertEqual(raw[0], 0)
                self.assertEqual(raw[L['NATIVE_QUERY_BASE']], 0x4e515231)
                epochs.append(raw[L['NATIVE_QUERY_BASE'] + 1])
        self.assertEqual(epochs[1] - epochs[0], 1)


if __name__ == '__main__':
    unittest.main()
