"""Focused acceptance suite for owned profiles and the normal detailed UI path."""
import argparse,hashlib,json,sys,time,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'app'),str(ROOT/'scripts')]

if __name__=='__main__':
    modules=['test_adapter','test_detail_full','test_detail_control',
             'test_detail_burst_stage','test_detail_weapons','test_detail_shields','test_detail_immunity','test_detail_batch','test_detail_charge_immunity','test_detail_optimal_range','test_detail_world','test_detail_ally_conditions','test_detail_team_hits','test_detail_capacity','test_detail_counts','test_detail_named','test_detail_named_capacity','test_detail_boss_clock','test_detail_boss_buffs']
    modules.append('test_detail_incoming')
    modules.append('test_detail_survival')
    modules.append('test_detail_hp_edge')
    modules.append('test_detail_hp_edge_boundary')
    modules.append('test_detail_survival_scaling')
    modules.append('test_detail_survival_scaling_boundary')
    modules.append('test_detail_cover_capacity')
    modules.append('test_detail_cover_capacity_boundary')
    modules.append('test_detail_decoy_healing')
    modules.append('test_detail_decoy_healing_boundary')
    modules.append('test_detail_outgoing_healing')
    modules.append('test_detail_outgoing_healing_boundary')
    modules.append('test_detail_healing_storage')
    modules.append('test_detail_healing_storage_boundary')
    modules.append('test_detail_heal_sharing')
    modules.append('test_detail_heal_sharing_boundary')
    modules.append('test_detail_heal_charge')
    modules.append('test_detail_heal_charge_boundary')
    modules.append('test_detail_named_magnitude')
    modules.append('test_detail_named_hits')
    modules.append('test_detail_damage_accum')
    modules.append('test_detail_max_hp_snapshot')
    modules.append('test_detail_base_copy')
    modules.append('test_detail_lifecycle_carriers')
    modules.append('test_detail_named_targets')
    modules.append('test_detail_damage_basis')
    modules.append('test_detail_deferred_attack')
    modules.append('test_detail_resource_limits')
    modules.append('test_detail_gauges')
    modules.append('test_detail_typed_impacts')
    modules.append('test_detail_target_counters')
    parser=argparse.ArgumentParser()
    parser.add_argument('--scope',choices=['full','recovery','fast'],default='full')
    args=parser.parse_args()
    common=['test_resource_specs','test_effect_overrides','test_damage_query_runtime','test_lifecycle_carriers','test_base_copy_runtime','test_max_hp_snapshot_runtime','test_damage_accum_runtime','test_detail_damage_accum_boundary','test_detail_named_hits_boundary','test_detail_named_magnitude_boundary','test_effect_spec','test_verification_session','test_reference_rewrite','test_effect_runtime','test_protection_runtime']
    if args.scope=='recovery':
        modules=['test_adapter']+[m for m in modules if any(m.startswith('test_detail_'+f) for f in
            ('decoy_healing','outgoing_healing','healing_storage','heal_sharing','heal_charge'))]
    elif args.scope=='fast':
        modules=['test_adapter','test_detail_hp_edge_boundary','test_detail_survival_scaling_boundary',
                 'test_detail_cover_capacity_boundary','test_detail_decoy_healing_boundary',
                 'test_detail_outgoing_healing_boundary','test_detail_healing_storage_boundary',
                 'test_detail_heal_sharing_boundary','test_detail_heal_charge_boundary']
    modules=['test_target_counter_runtime','test_impact_runtime','test_attack_timing_specs','test_damage_basis_specs','test_named_target_specs']+common+modules
    files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for directory,pattern in
        [('app','*.py'),('app','detail_effects*'),('scripts','*.py')] for p in (ROOT/directory).glob(pattern) if p.is_file()}
        |{f'tests/{m}.py' for m in modules})
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    started=time.perf_counter()
    from verification_session import close,stats
    suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
    try:
        result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
        reuse=stats()
    finally:close()
    stable=hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=result.wasSuccessful() and not result.skipped and stable,
        selection=args.scope,source_stable=stable,execution_reuse=reuse,
        tests_run=result.testsRun,skipped=len(result.skipped),seconds=round(time.perf_counter()-started,3),modules=modules,
        failures=[{'test':str(t),'traceback':tb} for t,tb in result.failures+result.errors],
        scope={'full':'Full normal-path regression set; supported mechanics only, not all-character battle correctness.',
               'recovery':'Owned adapter, common specification, migrated recovery GPU comparators and their original state/witness checks plus boundaries. Includes historical cases once per exact comparator/input.',
               'fast':'Common specification, verification-session isolation, owned adapter and compiler boundaries. No GPU battle tests.'}[args.scope],
        source_sha256=hashes)
    destination='research/detail-normal-acceptance.json' if args.scope=='full' else f'research/detail-common-{args.scope}-acceptance.json'
    (ROOT/destination).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
