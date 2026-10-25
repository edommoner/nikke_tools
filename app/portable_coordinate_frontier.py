"""Source-bound dependency frontier, never a GPU support certificate.

Reuses the public model-gap audit and exact composed source/arena auditors.
It imports no native battle, compiler or GPU backend.
"""
import ast
import hashlib
import json
from pathlib import Path


def verify(root, overrides=None):
    from portable_model_gap_audit import verify as model_audit
    from portable_arena_specs import audit_live_sources, audit_profile
    root = Path(root)
    overrides = overrides or {}
    model = model_audit(root, overrides)
    arena = {**audit_live_sources(root), **audit_profile('combined-v1')}
    assert arena['address_plan_verified'] and arena['runtime_connected']
    base = 'research/upstream/nikke-calc-master/calculator/'
    paths = [base + name for name in ('timeline.py', 'aim.py', 'boss_pattern.py')]
    paths += ['app/battle_attack_group_runtime.py', 'gpu/attack_group_runtime.slang',
              'gpu/coordinate_area_runtime.slang', 'research/world_projectile_native.py',
              'research/world_coordinate_physical_native.py', 'research/portable_coordinate_physical_cases.py',
              'research/world_coordinate_physical_common.py']
    texts = {p: overrides.get(p, (root / p).read_text()) for p in paths}
    def function(path, name):
        rows = [n for n in ast.walk(ast.parse(texts[path]))
                if isinstance(n, ast.FunctionDef) and n.name == name]
        assert len(rows) == 1, 'Canonical consumer changed: ' + name
        return ast.unparse(rows[0])
    pellet = function(base + 'timeline.py', '_coord_pellet')
    landing = function(base + 'aim.py', 'landing')
    geometry = function(base + 'boss_pattern.py', 'landing')
    # Bind the decomposition to the actual producers, not task prose.
    for token in ('L = geom.landing(ax, ay, R, grow)',
                  'body_f = max(0.0, 1.0 - sum(L.front) - L.core_open)',
                  'pcb = L.core_open / wb if wb > 1e-12 else 0.0',
                  "round(r['damage'] * q)", "round(r['damage'] * p)",
                  'sample_landing(ax, ay, R, random, angle=needs_angle(ax, ay, tg, geom.core))'):
        assert token in pellet, 'Coordinate packet contract changed: ' + token
    for token in ('for gx, gw in zip(_GL_X, _GL_W)',
                  'rho = R * (mid + half * gx) ** (1.0 / k)',
                  '_subtract(arcs, covered)', '_union(covered, arcs)',
                  'core_open=clip(c_open)', 'reach=tuple((clip(v) for v in reach))'):
        assert token in landing, 'Coordinate integration contract changed: ' + token
    assert 'round(ax, 6)' in geometry and 'self._cache[key] = landing(' in geometry
    producer = texts['app/battle_attack_group_runtime.py']
    assert 'Shot groups require plain logical normal packets' in producer
    assert 'Shot group model requires plain body/add world' in producer
    assert 'if any(not _is_normal(ev) or ev.to is not None or ev.rule or ev.split or ev.part_damage or ev.interrupt_damage for ev in answer):' in producer
    assert 'elif any(not _is_normal(ev) or ev.to is not None or ev.rule or ev.target or ev.extra or ev.split or ev.part_damage or ev.interrupt_damage for ev in answer):' in producer
    for token in ('coordinate_packets=False', 'Coordinate shot groups require expanded normal packets', "runtime.data['physical_receipts'].append"):
        assert token in producer, 'Coordinate receipt adapter drift: '+token
    legacy_observer = texts['research/world_projectile_native.py']
    assert 'len(answer)%muzzles==0 and len({h.damage for h in answer})==1' in legacy_observer
    assert 'actorPoolCount(s)!=1' in texts['gpu/attack_group_runtime.slang']
    assert 'Coordinate physical probability/parts routing is unconnected.' in texts['gpu/attack_group_runtime.slang']
    assert 'coordinateAreaContains' in texts['gpu/coordinate_area_runtime.slang']
    common_policy = texts['research/world_coordinate_physical_common.py']
    for token in ("patch.object(boss_pattern, 'landing', common_landing)",
                  "kwargs.get('config', {}).get('rng_mode') != 'expected'",
                  'result = native(case)', "REFERENCE_KIND = 'deterministic-common-cpu'"):
        assert token in common_policy, 'Common physical reference policy changed: ' + token
    from portable_slang_generation import source_hashes
    arc_sources = source_hashes(root, 'gpu/coordinate_arc_probe.slang')
    arc_sources = {name: hashlib.sha256(overrides[name].encode()).hexdigest()
                   if name in overrides else digest for name,digest in arc_sources.items()}
    arc_golden = json.loads((root/'research/portable-coordinate-arcs-short-expected.json').read_text())
    arc_source_matches = arc_golden['source_sha256'] == arc_sources
    scalar_sources=source_hashes(root,'gpu/coordinate_arc_scalar_probe.slang')
    scalar_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest()
                    if name in overrides else digest for name,digest in scalar_sources.items()}
    scalar_path=root/'research/portable-coordinate-arc-scalar-short-expected.json'
    # Other immutable suite packages may omit this separate primitive proof.
    # Absence is explicit; it must not become support or block new development.
    scalar_matches=(json.loads(scalar_path.read_text())['source_sha256']==scalar_sources
                    if scalar_path.is_file() else None)
    from portable_coordinate_numeric_v1 import PROFILE,contract_sha256,check_schema
    check_schema(root)
    numeric_sources=source_hashes(root,'gpu/coordinate_numeric_probe.slang')
    numeric_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest()
                     if name in overrides else digest for name,digest in numeric_sources.items()}
    numeric_path=root/'research/portable-coordinate-numeric-short-expected.json'
    numeric_matches=(json.loads(numeric_path.read_text())['source_sha256']==numeric_sources
                     if numeric_path.is_file() else None)
    geometry_sources=source_hashes(root,'gpu/coordinate_geometry_probe.slang')
    geometry_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest()
                      if name in overrides else digest for name,digest in geometry_sources.items()}
    geometry_path=root/'research/portable-coordinate-geometry-short-expected.json'
    geometry_matches=(json.loads(geometry_path.read_text())['source_sha256']==geometry_sources
                      if geometry_path.is_file() else None)
    landing_sources=source_hashes(root,'gpu/coordinate_landing_probe.slang')
    landing_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest()
                     if name in overrides else digest for name,digest in landing_sources.items()}
    landing_path=root/'research/portable-coordinate-landing-short-expected.json'
    landing_matches=(json.loads(landing_path.read_text())['source_sha256']==landing_sources
                     if landing_path.is_file() else None)
    physical_sources=source_hashes(root,'gpu/world_coordinate_physical_entry.slang')
    physical_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest()
                      if name in overrides else digest for name,digest in physical_sources.items()}
    physical_path=root/'research/portable-coordinate-physical-short-expected.json'
    physical_golden=json.loads(physical_path.read_text()) if physical_path.is_file() else None
    physical_matches=physical_golden['source_sha256']==physical_sources if physical_golden else None
    physical_entry=overrides.get('gpu/world_coordinate_physical_entry.slang',
                                 (root/'gpu/world_coordinate_physical_entry.slang').read_text())
    physical_runtime=overrides.get('gpu/coordinate_physical_runtime.slang',
                                   (root/'gpu/coordinate_physical_runtime.slang').read_text())
    assert '#define WEAPON_TYPED_DAMAGE(s,who,w,coefficient,when,legacy) coordinatePhysicalSample(s,who,w,coefficient,when)' in physical_entry
    assert '#define WEAPON_BODY_AMOUNT(s,who,legacy) coordinatePhysicalDeliver(s,who,legacy)' in physical_entry
    assert 'if(commands[s.inputBase+104402]!=0' in physical_runtime
    assert 'notifyWorldTeamFraction(s,who,0,actorNumber(bank+4)' in physical_runtime
    quantity_path=root/'research/portable-coordinate-quantity-short-expected.json'
    quantity_golden=json.loads(quantity_path.read_text()) if quantity_path.is_file() else None
    quantity_matches=quantity_golden['source_sha256']==physical_sources if quantity_golden else None
    emission_path=root/'research/portable-coordinate-accum-emission-short-expected.json'
    emission_golden=json.loads(emission_path.read_text()) if emission_path.is_file() else None
    emission_matches=emission_golden['source_sha256']==physical_sources if emission_golden else None
    core_sources=source_hashes(root,'gpu/world_coordinate_core_entry.slang')
    core_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in core_sources.items()}
    core_path=root/'research/portable-coordinate-core-short-expected.json'
    core_golden=json.loads(core_path.read_text()) if core_path.is_file() else None
    core_matches=core_golden['source_sha256']==core_sources if core_golden else None
    cache_sources=source_hashes(root,'gpu/world_coordinate_cache_entry.slang')
    cache_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in cache_sources.items()}
    cache_path=root/'research/portable-coordinate-cache-short-expected.json'
    cache_golden=json.loads(cache_path.read_text()) if cache_path.is_file() else None
    cache_matches=cache_golden['source_sha256']==cache_sources if cache_golden else None
    matrix_path=root/'research/portable-coordinate-matrix-short-expected.json'
    matrix_golden=json.loads(matrix_path.read_text()) if matrix_path.is_file() else None
    matrix_matches=matrix_golden['source_sha256']==cache_sources if matrix_golden else None
    from portable_coordinate_aim_wire import LAYOUT as aim_layout,check_schema as check_aim_schema
    check_aim_schema(root)
    aim_sources=source_hashes(root,'gpu/world_coordinate_aim_entry.slang')
    aim_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in aim_sources.items()}
    aim_path=root/'research/portable-coordinate-aim-short-expected.json'
    aim_golden=json.loads(aim_path.read_text()) if aim_path.is_file() else None
    aim_matches=aim_golden['source_sha256']==aim_sources if aim_golden else None
    control_sources=source_hashes(root,'gpu/world_coordinate_control_entry.slang')
    control_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in control_sources.items()}
    control_path=root/'research/portable-coordinate-control-short-expected.json'
    control_golden=json.loads(control_path.read_text()) if control_path.is_file() else None
    control_matches=control_golden['source_sha256']==control_sources if control_golden else None
    from portable_coordinate_group_frontier import verify as group_frontier
    group_plan=group_frontier(root)
    from portable_coordinate_route_audit import verify as route_audit
    route_policy=route_audit(root,overrides)
    group_sources=source_hashes(root,'gpu/world_coordinate_group_entry.slang')
    group_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in group_sources.items()}
    group_path=root/'research/portable-coordinate-group-short-expected.json'
    group_golden=json.loads(group_path.read_text()) if group_path.is_file() else None
    group_matches=group_golden['source_sha256']==group_sources if group_golden else None
    mixed_sources=source_hashes(root,'gpu/world_coordinate_mixed_entry.slang')
    mixed_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in mixed_sources.items()}
    mixed_path=root/'research/portable-coordinate-mixed-short-expected.json'
    mixed_golden=json.loads(mixed_path.read_text()) if mixed_path.is_file() else None
    mixed_matches=mixed_golden['source_sha256']==mixed_sources if mixed_golden else None
    sample_sources=source_hashes(root,'gpu/coordinate_sample_probe.slang')
    sample_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in sample_sources.items()}
    sample_path=root/'research/portable-coordinate-sample-short-expected.json'
    sample_golden=json.loads(sample_path.read_text()) if sample_path.is_file() else None
    sample_matches=sample_golden['source_sha256']==sample_sources if sample_golden else None
    sampled_battle_sources=source_hashes(root,'gpu/world_coordinate_sampling_entry.slang')
    sampled_battle_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in sampled_battle_sources.items()}
    sampled_battle_path=root/'research/portable-coordinate-sampled-battle-short-expected.json'
    sampled_battle_golden=json.loads(sampled_battle_path.read_text()) if sampled_battle_path.is_file() else None
    sampled_battle_matches=sampled_battle_golden['source_sha256']==sampled_battle_sources if sampled_battle_golden else None
    sampled_parent_sources=source_hashes(root,'gpu/world_coordinate_sampling_parent_entry.slang')
    sampled_parent_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in sampled_parent_sources.items()}
    sampled_parent_path=root/'research/portable-coordinate-sampled-parent-short-expected.json'
    sampled_parent_golden=json.loads(sampled_parent_path.read_text()) if sampled_parent_path.is_file() else None
    sampled_parent_matches=sampled_parent_golden['source_sha256']==sampled_parent_sources if sampled_parent_golden else None
    sampled_skill_sources=source_hashes(root,'gpu/world_coordinate_sampling_skill_entry.slang')
    sampled_skill_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in sampled_skill_sources.items()}
    sampled_skill_path=root/'research/portable-coordinate-sampled-skill-short-expected.json'
    sampled_skill_golden=json.loads(sampled_skill_path.read_text()) if sampled_skill_path.is_file() else None
    sampled_skill_matches=sampled_skill_golden['source_sha256']==sampled_skill_sources if sampled_skill_golden else None
    sampled_burst_sources=source_hashes(root,'gpu/world_coordinate_sampling_burst_entry.slang')
    sampled_burst_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in sampled_burst_sources.items()}
    sampled_burst_path=root/'research/portable-coordinate-sampled-burst-short-expected.json'
    sampled_burst_golden=json.loads(sampled_burst_path.read_text()) if sampled_burst_path.is_file() else None
    sampled_burst_matches=sampled_burst_golden['source_sha256']==sampled_burst_sources if sampled_burst_golden else None
    sampled_vital_sources=source_hashes(root,'gpu/world_coordinate_sampling_vital_entry.slang')
    sampled_vital_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in sampled_vital_sources.items()}
    sampled_vital_path=root/'research/portable-coordinate-sampled-vital-short-expected.json'
    sampled_vital_golden=json.loads(sampled_vital_path.read_text()) if sampled_vital_path.is_file() else None
    sampled_vital_matches=sampled_vital_golden['source_sha256']==sampled_vital_sources if sampled_vital_golden else None
    ratio_sources=source_hashes(root,'gpu/packet_ratio_probe.slang')
    ratio_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in ratio_sources.items()}
    ratio_path=root/'research/portable-packet-ratio-short-expected.json'
    ratio_golden=json.loads(ratio_path.read_text()) if ratio_path.is_file() else None
    ratio_matches=ratio_golden['source_sha256']==ratio_sources if ratio_golden else None
    round_sources=source_hashes(root,'gpu/coordinate_round_probe.slang')
    round_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in round_sources.items()}
    round_path=root/'research/portable-coordinate-round-short-expected.json'
    round_matches=json.loads(round_path.read_text())['source_sha256']==round_sources if round_path.is_file() else None
    integer_sources=source_hashes(root,'gpu/packet_integer_probe.slang')
    integer_sources={name:hashlib.sha256(overrides[name].encode()).hexdigest() if name in overrides else digest for name,digest in integer_sources.items()}
    integer_path=root/'research/portable-packet-integer-short-expected.json'
    integer_matches=json.loads(integer_path.read_text())['source_sha256']==integer_sources if integer_path.is_file() else None
    assert 'bm.accumulate_damage' in function(base+'timeline.py','_land_boss')
    assert 'bm.accumulate_damage' not in function(base+'timeline.py','_land_target')
    from portable_coordinate_landing_v1 import TARGETS,CUTS,OUTPUT as LANDING_OUTPUT
    dependencies = [
        dict(id='landing-probability', classification='gpu_port_gap',
             native='Geometry.landing -> aim.landing',
             work='Shared binary64 arcs, ordered occlusion, radial quadrature and cache-key rounding',
             verified_primitives=['interval-union', 'interval-intersection', 'interval-subtraction'],
             depends_on=['numeric-policy']),
        dict(id='physical-packet-expansion', classification='gpu_port_gap',
             native='CharState._coord_pellet',
             work='Per-pellet body/front/reach packets, conditional core probability, per-target damage rounding',
             private_expected_entry='gpu/world_coordinate_physical_entry.slang',
             private_expected_packets_connected=True,
             remaining=[
                        'sampling-rng','uncovered-mixed-scenes','original-definitions'],
             depends_on=['landing-probability', 'physical-native-observation']),
        dict(id='coordinate-shot-groups', classification='gpu_port_gap',
             native='battle_attack_group_runtime.Producer.wrap_fire / packet_scope',
             work='Bind actual expanded coordinate packet receipts to GPU group collection/seal',
             native_coordinate_packet_adapter_available=True,
             native_reference_cli='coordinate-group-common',
             default_plain_packet_policy_preserved=True,
             physical_gpu_group_receipts_connected=True,
             group_runtime_source='gpu/world_coordinate_group_entry.slang',
             depends_on=['physical-packet-expansion', 'physical-native-observation']),
        dict(id='physical-native-observation', classification='reference_adapter',
             native='world_projectile_native.capture_projectile_shots',
             replacement_observer='research/world_coordinate_physical_native.py',
             reference_tests='tests/test_coordinate_physical_reference.py',
             scope='Expected mode authored worlds; no GPU or group proof',
             legacy_equal_packet_observer_preserved=True,
             common_policy_observer='research/world_coordinate_physical_common.py',
             common_policy_reference_cli='coordinate-physical-common',
             common_policy_is_historical_native_equivalence=False,
             depends_on=[]),
        dict(id='physical-rng', classification='gpu_port_gap',
             native='CharState._coord_pellet -> sample_landing',
             work='Preserve random draw count/order, angle requirement, front-most and reach routing',
             private_physical_executor_implemented=True,shared_scalar_condition_rng_implemented=True,
             sampled_damage_skills_admitted=False,parent_quantity_admitted=False,
             native_reference_cli='coordinate-sampled-battle-common',
             depends_on=['physical-packet-expansion', 'numeric-policy']),
        dict(id='manual-coordinate-aim', classification='gpu_port_gap',
             native='CharState._aim_point / simulate._resolve_aims',
             work='Authored coordinate waypoints and frame camera arbitration',
             common_policy_reference_cli='coordinate-aim-common',
             static_authored_aim_ir_available=True,shared_gpu_aim_hooks_implemented=True,
             sealed_shared_gpu_aim_source_matches_current=aim_matches,
             aim_query_phases=['prior-frame aim for pre-arbitration skill handlers','resolved current-frame aim for physical ticks'], depends_on=[]),
        dict(id='numeric-policy', classification='gpu_numeric_implementation_gap',
             work='Implement selected deterministic shared numeric contract; retain native host disagreement evidence',
             user_decision_required=False, implementation_required=True, depends_on=[]),
    ]
    return dict(schema=1, passed=True, scope='Source audit and dependency plan only',
                native_model_available=True, public_gpu_admitted=False,
                private_composed_arena_verified=True, private_physical_scope='legacy-composed-body-only; separate coordinate-physical expected profile',
                coordinate_physical_expected=dict(suite='coordinate-physical',
                    source_sha256=physical_sources,proof_available=physical_golden is not None,
                    sealed_source_matches_current=physical_matches,
                    requires_new_metal_proof=not physical_matches,
                    input_count=len(physical_golden['entries']) if physical_golden else None,
                    reference_kind='deterministic-common-cpu',
                    runtime_connected=True,group_owner_mask_required=0,
                    physical_packet_capture_before_notifications=True,
                    physical_delivery_after_notifications=True,
                    live_core_nodes_connected=False,manual_aim_connected=False,
                    expanded_full_charge_parent_quantity_in_physical23_proof=False,
                    rng_connected=False,all_characters_certified=False,
                    public_gpu_admitted=False),
                coordinate_packet_quantity=dict(suite='coordinate-quantity',
                    proof_available=quantity_golden is not None,sealed_source_matches_current=quantity_matches,
                    input_count=len(quantity_golden['entries']) if quantity_golden else None,
                    source_sha256=physical_sources,reference_kind='deterministic-common-cpu',
                    packet_sum='unsigned128',packet_terms=128,multiplier_max=1024,
                    exact_integer_bound_bits=80,binary64_rounding='once after exact sum and multiplication',
                    expanded_full_charge_parent_quantity_connected=True,
                    native_creation_and_landing_times_distinguished=True,
                    integer_probe=dict(suite='packet-integer',sealed_source_matches_current=integer_matches,
                                       source_sha256=integer_sources),
                    public_gpu_admitted=False),
                coordinate_target_accumulation=dict(classification='native_reference_exclusion',
                    direct_target_consumer=False,reference_suite='coordinate-accumulation-policy',
                    game_rule_verified=False,extra_gpu_collection_required_for_parity=False,
                    coordinate_accumulation_emission_connected=True),
                coordinate_accumulation_emission=dict(suite='coordinate-accum-emission',
                    proof_available=emission_golden is not None,sealed_source_matches_current=emission_matches,
                    requires_new_metal_proof=not emission_matches,
                    input_count=len(emission_golden['entries']) if emission_golden else None,
                    source_sha256=physical_sources,reference_kind='deterministic-common-cpu',
                    body_only_receipt_connected=True,shared_queue_and_lifetime_core=True,
                    excluded_coordinate_scenarios=['ADD sharing','enemy attack nodes'],
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_live_core=dict(suite='coordinate-core',
                    proof_available=core_golden is not None,sealed_source_matches_current=core_matches,
                    requires_new_metal_proof=not core_matches,
                    input_count=len(core_golden['entries']) if core_golden else None,
                    source_sha256=core_sources,reference_kind='deterministic-common-cpu',
                    runtime_connected=True,graph_lifetime_reused=True,
                    winner='greatest diameter; newest start then declaration on equal diameter',
                    default_auto_aim_tracks_selected_core=True,base_core_at_origin=True,
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_geometry_cache=dict(suite='coordinate-cache',
                    proof_available=cache_golden is not None,sealed_source_matches_current=cache_matches,
                    requires_new_metal_proof=not cache_matches,
                    input_count=len(cache_golden['entries']) if cache_golden else None,
                    source_sha256=cache_sources,reference_kind='deterministic-common-cpu',
                    runtime_connected=True,shared_across_shooters=True,
                    key='CPython-compatible decimal-six nearest-even; signed-zero keys canonicalized',
                    value='first exact landing result for an equal key in the same Geometry',
                    entries_no_targets=4096,entries_127_targets=231,hash_slots=8192,
                    overflow='explicit rejection; no eviction',
                    duplicate_target_labels='binding/reference boundary; not admitted',
                    round_probe=dict(suite='coordinate-round',sealed_source_matches_current=round_matches),
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_area_matrix=dict(suite='coordinate-matrix',
                    proof_available=matrix_golden is not None,sealed_source_matches_current=matrix_matches,
                    input_count=len(matrix_golden['entries']) if matrix_golden else None,
                    profile='coordinate-area-matrix-common-v1',reference_kind='deterministic-common-cpu',
                    shared_numeric_profile=PROFILE,host_transcendentals_in_input=False,
                    static_authored_rotation_lowering=True,shared_cache_executor=True,
                    native_area_distance_scoped_to_common_reference=True,
                    historical_cpu_profile_retained=True,
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_authored_aim=dict(suite='coordinate-aim',proof_available=aim_golden is not None,
                    sealed_source_matches_current=aim_matches,requires_new_metal_proof=not aim_matches,
                    source_sha256=aim_sources,input_count=len(aim_golden['entries']) if aim_golden else None,
                    reference_cli='coordinate-aim-common',reference_kind='deterministic-common-cpu',
                    shared_runtime_hooks_implemented=True,persistent_point_bank=True,
                    pre_arbitration_skill_aim_retained=True,post_arbitration_physical_aim=True,
                    state_begin=aim_layout['STATE'],state_end=aim_layout['STATE']+aim_layout['STATE_WORDS'],
                    authored_entries_per_owner=8,window_kinds=4,anchor_kinds=5,
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_control_compositions=dict(suite='coordinate-control',
                    source_sha256=control_sources,proof_available=control_golden is not None,
                    sealed_source_matches_current=control_matches,requires_new_metal_proof=not control_matches,
                    input_count=len(control_golden['entries']) if control_golden else None,
                    base_weapon_reload_time_in_control_queries=True,
                    live_reload_fraction_controls_clip_classification=True,
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_group_integration=group_plan,
                coordinate_route_policy=route_policy,
                coordinate_mixed_world=dict(suite='coordinate-mixed',source_sha256=mixed_sources,
                    proof_available=mixed_golden is not None,sealed_source_matches_current=mixed_matches,
                    requires_new_metal_proof=not mixed_matches,input_count=len(mixed_golden['entries']) if mixed_golden else None,
                    reference_cli='coordinate-mixed-common',reference_kind='deterministic-common-cpu',
                    scoped_nodes=['buff','shield','vanish','move','groggy','direct boss attack'],
                    split_damage_routing_implemented=True,split_rounding='ordered binary64 reciprocal/multiply; nearest-even integer',
                    direct_part_skill_trace_uses_native_body_slot=True,
                    source_seal_is_not_cuda_execution=True,
                    remaining=['sampling-rng','summon attack payloads','debuff payloads','original-definitions'],
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_gpu_shot_groups=dict(suite='coordinate-group',source_sha256=group_sources,
                    proof_available=group_golden is not None,sealed_source_matches_current=group_matches,
                    requires_new_metal_proof=not group_matches,input_count=len(group_golden['entries']) if group_golden else None,
                    expanded_packet_receipts_connected=True,relocated_complete_stride=1507328,
                    compact_history_words_retained=186528,public_gpu_admitted=False,all_characters_certified=False),
                coordinate_skill_shape_contains_is_physical_landing=False,
                angular_interval_algebra=dict(suite='coordinate-arcs',
                    sealed_source_matches_current=arc_source_matches, source_sha256=arc_sources,
                    requires_new_metal_proof=not arc_source_matches,
                    operands_capacity=512, output_capacity=1024,
                    whole_geometry_capacity_certified=False, battle_connected=False),
                angular_scalar_arithmetic=dict(suite='coordinate-arc-scalar',
                    proof_available=scalar_matches is not None,
                    sealed_source_matches_current=scalar_matches,
                    source_sha256=scalar_sources, battle_connected=False,
                    operations=['positive-modulo','arc-wrap','arc-shift','compensated-measure'],
                    zero_width_arc_preserved=True, existing_runtime_sum_reused=True,
                    does_not_include=['acos','atan2','radial-quadrature']),
                deterministic_numeric_primitives=dict(suite='coordinate-numeric',
                    contract=PROFILE,contract_sha256=contract_sha256(),
                    proof_available=numeric_matches is not None,sealed_source_matches_current=numeric_matches,
                    source_sha256=numeric_sources,reference_kind='deterministic-common-cpu',
                    operations=['sincos-degrees','sincos-bounded-radians','atan2','acos','sqrt'],
                    battle_connected=False,full_numeric_policy_implemented=False,
                    native_host_disagreement_evidence_preserved=True),
                deterministic_shape_geometry=dict(suite='coordinate-geometry',
                    contract=PROFILE,proof_available=geometry_matches is not None,
                    sealed_source_matches_current=geometry_matches,source_sha256=geometry_sources,
                    authored_angles_consumed_on_gpu=True,rotation_matrix_precomputed_on_cpu=False,
                    operations=['distance','contains','circle-arcs','halfplane-arcs','grown-rotated-rectangle-arcs','radial-breaks'],
                    nonfinite_intermediate_rejected=True,denominator_underflow_rejected=True,
                    battle_connected=False,radial_integrator_connected=False,
                    whole_geometry_capacity_certified=False),
                deterministic_radial_landing=dict(suite='coordinate-landing',
                    proof_available=landing_matches is not None,sealed_source_matches_current=landing_matches,
                    source_sha256=landing_sources,reference_kind='deterministic-common-cpu',
                    unit_power_contract='coordinate-unit-power-v1',quadrature_contract='coordinate-gauss-legendre-10-v1',
                    targets_capacity=TARGETS,cuts_capacity=CUTS,output_words=LANDING_OUTPUT,
                    prepared_frame_values_on_gpu=True,all_cuts_retained=True,
                    operations=['front-probability','reach-probability','core-open','core-under'],
                    battle_connected=False,sampling_rng_connected=False,cache_key_rounding_connected=False,
                    whole_geometry_capacity_certified=False),
                deterministic_sample_points=dict(suite='coordinate-sample',
                    source_sha256=sample_sources,proof_available=sample_golden is not None,
                    sealed_source_matches_current=sample_matches,input_count=len(sample_golden['entries']) if sample_golden else None,
                    existing_integer_mt_reused=True,uniform_bits=53,mt_words_per_uniform=2,
                    no_angle_uniforms=1,angle_uniforms=2,complete_mt_state_compared=True,
                    native_reference_cli='coordinate-sampling-common',native_sampled_pellet_observation_available=True,
                    battle_connected=False,critical_sampling_connected=False,
                    remaining=['physical RNG state separate from boss target stream','per-pellet damage/critical and notification order','variable packet bank and parent quantity','shared group receipt delivery'],
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_sampled_battles=dict(suite='coordinate-sampled-battle',source_sha256=sampled_battle_sources,
                    proof_available=sampled_battle_golden is not None,sealed_source_matches_current=sampled_battle_matches,
                    input_count=len(sampled_battle_golden['entries']) if sampled_battle_golden else None,
                    reference_kind='deterministic-common-cpu',native_reference_cli='coordinate-sampled-battle-common',
                    physical_rng_separate_from_boss=True,per_pellet_snapshots=True,
                    ordered_auto_and_charge_notifications=True,condition_rng=['not_core','prob'],
                    reused_expected_only_scratch=True,logical_pellet_capacity=1024,target_capacity=127,
                    admitted_definition_kinds=['buff'],sampled_damage_skills_admitted=False,parent_quantity_admitted=False,
                    group_receipt_functions_reused=True,group_owner_examples_verified=False,
                    remaining=['non-buff effects including weapon changes, healing, sampled damage/queue effects','parent reference quantity integer division','group-owner sampled worlds','original definitions and public admission'],
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_sampled_parent=dict(suite='coordinate-sampled-parent',source_sha256=sampled_parent_sources,
                    proof_available=sampled_parent_golden is not None,sealed_source_matches_current=sampled_parent_matches,
                    input_count=len(sampled_parent_golden['entries']) if sampled_parent_golden else None,
                    reference_kind='deterministic-common-cpu',native_reference_cli='coordinate-sampled-parent-common',
                    admitted_definition_kinds=['buff','dealt_fixed_damage'],
                    parent_quantity='exact uint128 created physical packet sum / muzzle; one nearest-even binary64 rounding',
                    whole_battle_integer_damage='persistent uint128 BODY/PART credits; ordered binary64 diagnostic retained',
                    parent_children_consume_rng=False,extra_runtime_bytes=0,extra_output_words=0,
                    group_owner_examples_verified=False,
                    remaining=['ordinary damage skill RNG','weapon changes and healing in sampled battles','group-owner sampled worlds','original definitions and public admission'],
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_sampled_skills=dict(suite='coordinate-sampled-skill',source_sha256=sampled_skill_sources,
                    proof_available=sampled_skill_golden is not None,sealed_source_matches_current=sampled_skill_matches,
                    input_count=len(sampled_skill_golden['entries']) if sampled_skill_golden else None,
                    reference_kind='deterministic-common-cpu',native_reference_cli='coordinate-sampled-skill-common',
                    admitted_definition_kinds=['buff','ordinary damage','dealt_fixed_damage'],
                    critical_uniform_per_body_hit=1,critical_uniforms_at_zero_and_unit_rate=True,
                    target_packets_reuse_body_critical=True,cast_factors_frozen_across_children=True,
                    queue_and_named_hit_context_reused=True,depth_capacity=32,extra_runtime_bytes=0,extra_output_words=0,
                    remaining=['deferred burst skill sampling','weapon changes and healing in sampled battles','sampled group-owner and mixed effect worlds','original definitions and public admission'],
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_sampled_bursts=dict(suite='coordinate-sampled-burst',source_sha256=sampled_burst_sources,
                    proof_available=sampled_burst_golden is not None,sealed_source_matches_current=sampled_burst_matches,
                    input_count=len(sampled_burst_golden['entries']) if sampled_burst_golden else None,
                    reference_kind='deterministic-common-cpu',native_reference_cli='coordinate-sampled-burst-common',
                    pending_modes=['legacy-bonus','land-in-full-burst'],legacy_per_hit_critical=True,
                    legacy_generation_before_optin_and_landing=True,optin_count_latched_at_cast=True,
                    optin_stats_requeried_at_entry=True,optin_named_critical_context=True,
                    pending_entries=512,hits_per_entry=256,output_words=1769472,
                    retained_output_prefix_words=1507328,additional_output_bytes=1048576,additional_runtime_bytes=0,
                    remaining=['weapon changes and healing in sampled battles','sampled group-owner and mixed effect worlds','original definitions and public admission'],
                    public_gpu_admitted=False,all_characters_certified=False),
                coordinate_sampled_vital=dict(suite='coordinate-sampled-vital',source_sha256=sampled_vital_sources,
                    proof_available=sampled_vital_golden is not None,sealed_source_matches_current=sampled_vital_matches,
                    input_count=len(sampled_vital_golden['entries']) if sampled_vital_golden else None,
                    reference_kind='deterministic-common-cpu',native_reference_cli='coordinate-sampled-vital-common',
                    shared_weapon_modes=True,shared_body_cover_healing=True,shared_current_hp_reduce=True,
                    live_mode_muzzles=True,first_coefficient=True,legacy_and_optin_pending=True,
                    automatic_reload_cover_repair=True,manual_cover_controls_packed=False,
                    input_words=109528,output_words=1769472,additional_runtime_bytes=0,
                    remaining=['sampled group-owner and mixed effect worlds','further weapon-mode flags and control combinations','manual cover/control composition packing','further health/storage/instant combinations','original definitions and public admission'],
                    public_gpu_admitted=False,all_characters_certified=False),
                packet_integer_ratio=dict(suite='packet-ratio',source_sha256=ratio_sources,
                    proof_available=ratio_golden is not None,sealed_source_matches_current=ratio_matches,
                    input_count=len(ratio_golden['entries']) if ratio_golden else None,
                    numerator_bits=128,divisor_min=1,divisor_max=1024,rounding='single nearest even'),
                logical_pellets_equal_emitted_packets=False, dependencies=dependencies,
                source_sha256={p: hashlib.sha256(t.encode()).hexdigest() for p, t in texts.items()},
                model_gap_audit=model, gpu_calls=0, native_battle_calls=0,
                calculation_verified=False, full_goal_complete=False)
