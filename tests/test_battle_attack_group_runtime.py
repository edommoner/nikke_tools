"""Autonomous native shot boundaries, matched recipients and cleanup."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path,PureWindowsPath,PurePosixPath
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline,buff_manager
from runner import sim
from battle_attack_group_runtime import battle_attack_groups
from portable_battle_attack_group_cases import fixtures
from portable_battle_attack_group_contracts import verify
from world_battle_attack_group_native import observe
from effect_runtime import state
def roster():
    s=importlib.util.spec_from_file_location('group_test_roster',ROOT/'research/verify-world-projectile-rosters.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def snapshot():return (timeline.simulate,sim.simulate,timeline.BossScript,timeline.HitEvent,timeline.CharState._fire,timeline.CharState._charge_fire,buff_manager.BuffManager.notify,buff_manager.BuffManager._resolve_target,buff_manager.BuffManager.register_damage_handler,buff_manager.BuffManager.publish_landing)
class BattleAttackGroupTests(unittest.TestCase):
    def test_source_audit_names_are_identical_on_windows_and_posix(self):
        from portable_missing_consumer_audit import source_name
        for path_type,root in [(PureWindowsPath,'C:/repo'),(PurePosixPath,'/repo')]:
            base=path_type(root)
            self.assertEqual(source_name(base/'app'/'battle_attack_group_runtime.py',base),'app/battle_attack_group_runtime.py')
            with self.assertRaises(ValueError):source_name(base.parent/'other'/'producer.py',base)
    def test_full_original_effects_and_factories_do_not_simulate(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU hit input')):
            cases=fixtures();self.assertEqual(len(cases),22)
            original=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())
            for c in cases:
                p=engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True))
                for owner in c['body']['squad']:
                    got=[x['effect'] for x in p['effects'] if x['owner']==owner and x['effect'].get('source') in ('스킬1','스킬2','스킬3')]
                    self.assertEqual(got,[e for e in original[owner] if not e.get('favorite',0)])
    def test_real_physical_packets_count_distinct_enemies_and_trigger_once(self):
        cases=fixtures()
        for c in (cases[1],cases[12],cases[20],cases[21]):
            before=copy.deepcopy(c);n,_=observe(c);self.assertTrue(verify(c,n)['verified']);self.assertEqual(c,before)
            self.assertTrue(n['children']);self.assertEqual(len(n['notifications']),len(n['groups']))
            if c['contract']['threshold']==2:self.assertEqual(len(n['groups'][0]['targets']),2)
            if c['contract'].get('declared_listener'):self.assertGreater(n['shots'][0]['packets'],1)
    def test_single_boss_preserves_original_complete_battle_and_shots(self):
        r=roster()
        for c in (fixtures()[0],fixtures()[10]):
            before=snapshot();baseline,shots=r.native_reference(c['body']);n,_=observe(c)
            self.assertEqual(n['battle'],baseline);self.assertEqual(n['projectile_shots'],shots);self.assertFalse(n['notifications']);self.assertEqual(snapshot(),before)
    def test_respawn_and_dead_targets_never_receive_frozen_children(self):
        for c in [c for c in fixtures() if c['contract'].get('reopened') or c['contract']['capacity']==1.]:
            n,_=observe(c);verify(c,n);bad=copy.deepcopy(n);bad['child_landings'][0]['target']=[5,0,2]
            with self.assertRaises(AssertionError):verify(c,bad)
    def test_source_and_queued_child_exceptions_release_owned_state(self):
        c=fixtures()[1];r=roster()
        for stage in ('notify','child'):
            before=snapshot();data=None;original_notify=buff_manager.BuffManager.notify;original_register=buff_manager.BuffManager.register_damage_handler
            def notify(manager,event,*args,**kwargs):
                if stage=='notify' and event.startswith('multi_hit:'):raise RuntimeError('injected group failure')
                return original_notify(manager,event,*args,**kwargs)
            def register(manager,handler):
                def wrapped(effect,*args,**kwargs):
                    answer=handler(effect,*args,**kwargs)
                    if stage=='child' and effect.get('stat')=='bonus_damage':raise RuntimeError('injected group failure')
                    return answer
                return original_register(manager,wrapped)
            with patch.object(buff_manager.BuffManager,'notify',notify),patch.object(buff_manager.BuffManager,'register_damage_handler',register):
                with self.assertRaisesRegex(RuntimeError,'injected group failure'):
                    with battle_attack_groups(routing=c['routing']) as data:r.native_reference(c['body'])
            self.assertEqual(snapshot(),before);self.assertIsNotNone(data)
            for manager in data['managers']:
                runtime=state(manager)
                self.assertFalse(runtime.event_stack);self.assertFalse(runtime.impact_stack)
                for key in ('attack_groups','sealed_attack_groups','dispatching_attack_groups'):self.assertFalse(runtime.resources.get(key))
    def test_explicit_policy_and_plain_world_guards_restore_default_path(self):
        for value in (None,True,'parts-count-as-enemies'):
            with self.assertRaises(ValueError):
                with battle_attack_groups(routing=value):pass
        with battle_attack_groups(routing='all-logical-enemies'):
            with self.assertRaisesRegex(ValueError,'Nested'):
                with battle_attack_groups(routing='all-logical-enemies'):pass
        c=copy.deepcopy(fixtures()[0]);c['body']['enemy']['has_parts']=True;before=snapshot()
        with self.assertRaisesRegex(ValueError,'plain body/add'):observe(c)
        self.assertEqual(snapshot(),before)
    def test_forged_matched_set_and_uninstalled_default_are_rejected(self):
        from test_target_counter_runtime import manager as make_manager,NAMES
        from attack_group_specs import AttackTargets,AttackKey
        from impact_specs import ActorHandle,ActorKind
        from reference_rewrite import referenced_names
        from portable_missing_consumer_audit import verify as audit
        m=make_manager([]);token=AttackTargets(AttackKey(NAMES[0],7,1),(ActorHandle(ActorKind.BODY,0),))
        with battle_attack_groups(routing='all-logical-enemies'):
            with self.assertRaisesRegex(ValueError,'owned sealed'):m.notify('multi_hit:1',0,NAMES[0],attack_targets=token)
        self.assertNotIn('_nikke_shot_land_scope',referenced_names(timeline.simulate));self.assertEqual(audit(ROOT)['default_battle_attack_group_producer_calls'],[])
if __name__=='__main__':unittest.main()
