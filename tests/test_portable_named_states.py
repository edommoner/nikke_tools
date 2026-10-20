import copy, importlib.util, json, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_named_state_oracle import observe
from portable_trigger_specs import validate_input
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('named_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-named-states.json').read_text())['cases']
def case(name):return next(c for c in CASES if c['name']=='named-state-'+name)
def buffs(name):return [q['attack_buffs'] for q in observe(case(name))['queries']]
class NamedStateContracts(unittest.TestCase):
    def test_unicode_colons_and_whitespace_survive_expiry(self):
        for i in range(8):self.assertEqual([r[0] for r in buffs(str(i)+'-self-live-expiry')],[10,0])
    def test_finite_condition_is_an_activation_gate(self):self.assertEqual([r[0] for r in buffs('finite-gate-keeps-duration-after-state-expiry')],[10,10])
    def test_negative_predicate_rechecks_at_query_time(self):
        for i in range(8):self.assertEqual([r[0] for r in buffs(str(i)+'-negative-activation')],[10,0,10])
    def test_named_apply_and_end_events_keep_the_complete_suffix(self):
        for i in range(8):self.assertEqual([r[0] for r in buffs(str(i)+'-apply-and-end')],[10,20])
    def test_membership_is_independent_of_the_marker_caster(self):
        self.assertEqual(buffs('other-caster-other-recipient')[0],[0]*5)
        self.assertEqual(buffs('other-caster-self-recipient')[0],[10]*5)
        self.assertEqual(buffs('own-caster-other-recipient')[0],[0]*5)
    def test_condition_uses_its_caster_and_not_query_recipient(self):self.assertEqual(buffs('query-recipient-is-not-condition-owner')[0],[0,10,0,0,0])
    def test_exact_names_do_not_trim_or_prefix_match(self):
        for name in ('spaces-are-distinct','prefixes-are-distinct'):self.assertEqual(buffs(name)[0],[0]*5)
    def test_empty_self_state_keeps_native_no_weapon_mode_semantics(self):self.assertEqual(buffs('unnamed-state-retains-empty-mode-rule')[0][0],10)
    def test_two_colon_names_remain_independent(self):self.assertEqual([r[0] for r in buffs('two-different-colon-states')],[10,0])
    def test_ordered_notification_keeps_duplicates_and_scope(self):
        self.assertEqual(buffs('ordered-notices-recipients')[0],[20,10,0,0,0])
        self.assertEqual(buffs('ordered-notices-None')[0],[10,10,0,0,0])
    def test_stat_applied_events_keep_the_typed_suffix_and_order(self):
        for stat in ('dot_dmg_pct','split_dmg_pct'):self.assertEqual(buffs('stat-applied-'+stat)[0],[20,10,0,0,0])
    def test_stat_notices_cover_refresh_unnamed_and_lazy_registration(self):
        for stat in ('dot_dmg_pct','split_dmg_pct'):
            for count in (1,11,21):self.assertEqual(buffs('stat-'+stat+'-order-'+str(count))[0][0],count*10)
            self.assertEqual(buffs('stat-'+stat+'-refresh-max-one')[0][0],20)
            self.assertEqual(buffs('stat-'+stat+'-unnamed')[0][0],10)
            self.assertEqual(buffs('stat-'+stat+'-lazy-stays-unresolved')[0][0],0)
            self.assertEqual(buffs('stat-'+stat+'-named-child-removes-parent')[0][0],210)
    def test_eager_alias_after_lazy_resolution_uses_incoming_targets(self):
        for stat in ('dot_dmg_pct','split_dmg_pct'):self.assertEqual([r[0] for r in buffs('alias-resolved-lazy-to-eager-'+stat)],[0,10])
    def test_base_rl_charge_classification_applies_explosion_bonus(self):
        from portable_burst_oracle import observe as weapon
        damage=lambda name:weapon(case(name))['queries'][0]['damage'][0]
        self.assertEqual(damage('base-RL-charge-50'),1500)
        for name in ('base-SR-charge-50','base-AR-charge-50','base-RL-charge-0'):self.assertEqual(damage(name),1000)
        self.assertEqual(damage('base-RL-charge--50'),500)
        self.assertEqual(damage('base-RL-auto-50'),1000)
    def test_unknown_base_weapon_type_is_rejected(self):
        c=copy.deepcopy(case('base-RL-charge-50'));c['combat']['weapons'][0]['base_weapon_type']='unknown'
        with self.assertRaises(ValueError):v.compile_case(c)
    def test_known_unsupported_and_malformed_events_remain_rejected(self):
        for timing in ('event:','event:state_end:','event:part_destroy','event:enemy_spawn','event:projectile_destroy','event:accum_full:A:B','event:target_counter_complete:A:B','event:ally_hp_below:abc','event:adjacent_hp_below:50:bad','stack_reach:A:B:1','every_stack:A:B:1','hit_count:A:B:1'):
            with self.subTest(timing=timing),self.assertRaises(ValueError):validate_input(dict(trigger=dict(timing=[timing],condition=[])))
    def test_structured_predicates_do_not_acquire_an_ambiguous_colon_parser(self):
        for condition in ('target_code:전격','self_stack_above:A:B:1','gauge_above:A:B:1'):
            with self.subTest(condition=condition),self.assertRaises(ValueError):validate_input(dict(trigger=dict(timing=['on_attack'],condition=[condition])))
    def test_every_authored_case_compiles_without_mutating_its_names(self):
        for c in CASES:
            before=copy.deepcopy(c);words,_=v.compile_case(c);self.assertEqual(c,before);self.assertEqual(len(words),L['INPUT_WORDS'])
if __name__=='__main__':unittest.main()
