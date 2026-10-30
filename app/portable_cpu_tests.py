"""One CPU-only unittest worker, preserving every selected group and its logs."""
import contextlib,os,re,sys,time,unittest
from pathlib import Path

AUDIT_FILES = {'test_coordinate_power_v1.py': ('requirements-validation.txt',),'test_coordinate_landing_v1.py': ('requirements-validation.txt',),
    'test_coordinate_healing.py': ('research/portable-coordinate-auto-reload-short-expected.json',),'test_coordinate_auto_reload.py': ('research/portable-coordinate-mode-actions-short-expected.json',),
    'test_coordinate_mode_actions.py': ('research/portable-coordinate-burst-control-short-expected.json',),
    'test_original_lock_health_parts.py': ('research/portable-original-lock-composition-v1-expected.json',),
    'test_original_shield_weapons.py': ('research/upstream/nikke-calc-master/data/parsed_skills.json',),
    'test_original_lock_controls.py': ('research/portable-original-lock-composition-v1-expected.json',),
    'test_coordinate_mixed.py': ('research/portable-coordinate-group-short-expected.json',),
    'test_coordinate_sampled_delivery.py': ('research/portable-coordinate-sampled-vital-short-expected.json',),
    'test_coordinate_physical_frontier.py': (
    'research/upstream/nikke-calc-master/docs/IMPL-STATUS.md',
    'research/portable-coordinate-arcs-short-expected.json',
    'tests/fixtures/coordinate-common-numeric-decision.json'),
    'test_portable_model_gap_audit.py': (
    'tests/fixtures/resident-append-full106-metal-v1.json',
    'tests/fixtures/resident-append-cross-gpu-v1.json',
    'research/upstream/nikke-calc-master/docs/IMPL-STATUS.md',
    'tests/fixtures/coordinate-common-numeric-decision.json',
    'tests/fixtures/heavyarms-lock-published-contract.json',
    'research/upstream/nikke-calc-master/data/parsed_skills.json')}


AUDIT_FILES['test_original_catalogue_burst.py']=('research/portable-original-catalogue-burst-v1-expected.json','research/portable-original-catalogue-initial-v1-expected.json')
AUDIT_FILES['test_original_catalogue_roles_sealed.py']=('research/portable-original-catalogue-roles-v1-expected.json',)
AUDIT_FILES['test_original_catalogue_incoming_sealed.py']=('research/portable-original-catalogue-incoming-v1-expected.json',)
AUDIT_FILES['test_recipient_order_observation.py']=('tests/fixtures/portable-recipient-order-observation-source-delta.json',)
AUDIT_FILES['test_original_catalogue_support.py']=(
    'tests/fixtures/original-catalogue-support-independent-v1.json',
    'research/portable-original-catalogue-support-v1-expected.json',
    'research/portable-compiler-full--original-catalogue-support-source-certificate.json')
AUDIT_FILES['test_original_support_conditions.py']=(
    'research/portable-original-catalogue-support-v1-expected.json',
    'research/portable-original-support-conditions-v1-expected.json',
    'research/portable-compiler-full--original-support-conditions-source-certificate.json',
    'tests/fixtures/original-support-conditions-independent-v1.json')
AUDIT_FILES['test_original_threshold_conditions.py']=(
    'research/portable-original-support-conditions-v1-expected.json',
    'research/portable-original-threshold-conditions-v1-expected.json',
    'research/portable-compiler-full--original-threshold-conditions-source-certificate.json',
    'tests/fixtures/original-threshold-conditions-independent-v1.json',
    'tests/fixtures/original-threshold-gpu-counts-v1.json')
AUDIT_FILES['test_original_probability_conditions.py']=(
    'research/portable-original-threshold-conditions-v1-expected.json',
    'research/portable-original-probability-conditions-v1-expected.json',
    'research/portable-compiler-full--original-probability-conditions-source-certificate.json',
    'tests/fixtures/original-probability-conditions-independent-v1.json',
    'tests/fixtures/original-probability-gpu-counts-v1.json')
AUDIT_FILES['test_cover_defense_numeric.py']=('research/cover-defense-random-inputs-v1.json','research/portable-cover-defense-numeric-v1-expected.json','tests/fixtures/cover-defense-numeric-metal-v1.json','tests/fixtures/cover-defense-numeric-independent-v1.json')
AUDIT_FILES['test_cover_defense_battle.py']=('tests/fixtures/cover-defense-battle-cpu-v1.json',)
AUDIT_FILES['test_cover_defense_wire.py']=('tests/fixtures/cover-defense-battle-cpu-v1.json','tests/fixtures/portable-cover-defense-source-delta.json')
AUDIT_FILES['test_heavyarms_lock_reference.py']=AUDIT_FILES['test_portable_model_gap_audit.py']
AUDIT_FILES['test_bay_published_allocation.py']=('tests/fixtures/bay-published-allocation-v1.json',)
AUDIT_FILES['test_portable_entry_plan.py']=('tests/fixtures/bay-published-allocation-v1.json',)
for _test in ('test_effect_target_count_policy.py','test_effect_target_count_reference.py','test_portable_effect_target_count.py','test_effect_target_count_shots.py'):
    AUDIT_FILES[_test]=('research/upstream/nikke-calc-master/data/parsed_skills.json',)
AUDIT_FILES['test_effect_target_count_policy.py']=AUDIT_FILES['test_portable_model_gap_audit.py']
AUDIT_FILES['test_effect_range.py']=('research/upstream/nikke-calc-master/data/parsed_skills.json',)
AUDIT_FILES['test_portable_scope_snapshot_audit.py']=(
    'tests/fixtures/portable-resident-scalar-generated.json',
    'tests/fixtures/portable-healing-hp-snapshot-delta.json')
AUDIT_FILES['test_resident_append_probe.py']=('tests/fixtures/portable-resident-scalar-generated.json',)
AUDIT_FILES['test_dispatch_frame_storage.py']=(
    'research/portable-coordinate-resident-frames-short-expected.json',
    'research/portable-coordinate-resident-frames-short-v2-expected.json',
    'research/portable-compiler-full--coordinate-resident-frames-v2-source-certificate.json')
AUDIT_FILES['test_moving_frames.py']=(
    'research/portable-moving-group-v2-expected.json',
    'research/portable-moving-frames-v1-expected.json',
    'research/portable-compiler-full--moving-frames-source-certificate.json')
AUDIT_FILES['test_quantity_moving_frames.py']=(
    'research/portable-moving-frames-v1-expected.json',
    'research/portable-moving-visited-v1-expected.json',
    'research/portable-compiler-full--moving-visited-source-certificate.json')
AUDIT_FILES['test_portable_readiness_semantics.py']=(
    'research/upstream/nikke-calc-master/docs/IMPL-STATUS.md',
    'tests/fixtures/enemy-movement-math-metal-v1.json',
    'tests/fixtures/enemy-movement-math-cuda-v1.json',
    'tests/fixtures/enemy-movement-battle-metal-v1.json',
    'tests/fixtures/moving-typed-metal-v1.json',
    'tests/fixtures/moving-group-metal-v1.json',
    'tests/fixtures/moving-many-metal-v1.json',
    'research/portable-moving-typed-v1-expected.json',
    'research/portable-enemy-movement-battle-v1-expected.json',
    'tests/fixtures/resident-current-cuda-native-join-v1.json',
    'tests/fixtures/resident-append-full106-metal-v1.json',
    'tests/fixtures/resident-append-cross-gpu-v1.json',
    'tests/fixtures/resident-current-cuda-v2-summary.json')
AUDIT_FILES['test_portable_partitioned_current.py']=(
    'tests/fixtures/partitioned-physical-reference-v1.json',
    'tests/fixtures/resident-append-full106-metal-v1.json',
    'research/portable-coordinate-resident-frames-short-v2-expected.json')
AUDIT_FILES['test_portable_partitioned_witness.py']=(
    'tests/fixtures/resident-current-cuda-v2-summary.json',
    'research/portable-coordinate-resident-frames-short-v2-expected.json')
AUDIT_FILES['test_portable_partitioned_join.py']=(
    'tests/fixtures/resident-current-envelope-v1-summary.json',
    'research/portable-coordinate-resident-frames-short-v2-expected.json')
AUDIT_FILES['test_enemy_movement_wire.py']=('tests/fixtures/portable-enemy-movement-source-delta.json',)
AUDIT_FILES['test_moving_group_events.py']=('tests/fixtures/moving-group-native-events-v1.json','tests/fixtures/moving-group-metal-v1.json','research/portable-moving-group-v1-expected.json')

def validate_dependency_files(root,patterns,included=None):
    """Reject missing audit data before tests/native work or execution claims."""
    root=Path(root)
    names={name for pattern in patterns for name in AUDIT_FILES.get(pattern,())}
    for name in sorted(names):
        path=root/name
        if not path.is_file() or path.is_symlink():
            raise ValueError('CPU audit dependency missing: '+name)
        if included is not None and name not in included:
            raise ValueError('CPU audit dependency missing from immutable payload: '+name)


def validate_groups(root,patterns):
    if len(set(patterns))!=len(patterns):raise ValueError('Duplicate CPU test group')
    for pattern in patterns:
        if not re.fullmatch(r'test_[A-Za-z0-9_]+\.py',pattern) or not (root/'tests'/pattern).is_file():
            raise ValueError('CPU test file missing or invalid: '+pattern)
    validate_dependency_files(root,patterns)


def run_groups(root,capture,patterns,write):
    """Execute in registry order; failure stops before any later group or GPU."""
    root=Path(root);capture=Path(capture);validate_groups(root,patterns)
    if (capture/'cpu-tests.json').exists():raise FileExistsError('Fresh CPU test receipt required')
    for pattern in patterns:
        for suffix in ('.stdout.log','.stderr.log'):
            if (capture/(pattern+suffix)).exists():raise FileExistsError('Fresh CPU test logs required')
    before_path=list(sys.path);rows=[];loader=unittest.TestLoader()
    try:
        for pattern in patterns:
            started=time.perf_counter()
            with (capture/(pattern+'.stdout.log')).open('x',encoding='utf-8') as stdout,(capture/(pattern+'.stderr.log')).open('x',encoding='utf-8') as stderr,contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
                suite=loader.discover(str(root/'tests'),pattern=pattern)
                result=unittest.TextTestRunner(stream=stderr,verbosity=1).run(suite)
                success=result.wasSuccessful() and result.testsRun>0
                if result.testsRun==0:stderr.write('Required CPU group discovered zero tests\n')
            rows.append(dict(pattern=pattern,exit_code=0 if success else 1,elapsed_seconds=time.perf_counter()-started,
                tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),runner_pid=os.getpid()))
            write(capture/'cpu-tests.json',rows)
            if not success:break
        if not patterns:write(capture/'cpu-tests.json',rows)
    finally:sys.path[:]=before_path
    return rows


def complete(rows,patterns):
    return bool([r.get('pattern') for r in rows]==list(patterns) and all(type(r.get('exit_code')) is int and r['exit_code']==0 and type(r.get('tests')) is int and r['tests']>0 and r.get('failures')==0 and r.get('errors')==0 for r in rows))

AUDIT_FILES['test_enemy_movement_cuda_words.py']=('tests/fixtures/enemy-movement-math-cuda-v1.json','research/portable-enemy-movement-math-v1-expected.json')
AUDIT_FILES['test_moving_typed_wire.py']=('tests/fixtures/portable-moving-many-source-delta.json','tests/fixtures/portable-moving-typed-source-delta.json','tests/fixtures/portable-enemy-movement-source-delta.json','tests/fixtures/portable-coordinate-typed-weapon-source-delta.json','tests/fixtures/moving-typed-metal-v1.json','research/portable-moving-typed-v1-expected.json')
AUDIT_FILES['test_moving_many_wire.py']=('tests/fixtures/portable-moving-many-source-delta.json','tests/fixtures/portable-moving-typed-source-delta.json','tests/fixtures/portable-enemy-movement-source-delta.json','tests/fixtures/moving-many-metal-v1.json','research/portable-moving-many-v1-expected.json')
