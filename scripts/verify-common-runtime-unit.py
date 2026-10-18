"""One shared lightweight suite, without character-specific case duplication."""
import argparse,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--native-stage',action='store_true');args=parser.parse_args()
    modules=['test_target_counter_runtime','test_impact_runtime','test_effect_runtime','test_effect_spec','test_reference_rewrite',
        'test_damage_query_runtime','test_resource_specs','test_effect_overrides','test_detail_build_contract','test_event_index_specs','test_periodic_source_runtime','test_staged_dot_runtime','test_quantity_specs','test_attack_group_runtime','test_world_actor_runtime','test_world_condition_specs','test_target_context_runtime','test_enemy_recipient_runtime','test_periodic_target_runtime','test_named_ally_targets','test_weapon_mode_specs','test_mode_input_policy']
    excluded=['test_detail_build_contract'] if args.native_stage else []
    modules=[name for name in modules if name not in excluded]+['test_timer_registry_runtime']
    files=list((ROOT/'app').glob('*.py'))+[ROOT/f'tests/{name}.py' for name in modules]+[ROOT/'scripts/enemy_recipient_cases.py',ROOT/'scripts/enemy_fanout_cases.py',ROOT/'scripts/enemy_mutation_cases.py',ROOT/'scripts/periodic_target_cases.py']
    files += [ROOT/'scripts/timer_registry_cases.py']
    manifests=['app/detail_effects-sm86.json']+([] if args.native_stage else ['app/detail_effects-build.json'])
    files += [Path(__file__).resolve()]+[ROOT/p for p in ['app/detail_effects.cu','data/engine-effect-overrides.json']+manifests]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(modules))
    stable=before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=result.wasSuccessful() and not result.skipped and stable,tests_run=result.testsRun,skipped=len(result.skipped),
        failures=[dict(test=str(t),traceback=tb) for t,tb in result.failures+result.errors],source_stable=stable,source_sha256=before,
        native_stage_only=args.native_stage,excluded_modules=excluded)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
