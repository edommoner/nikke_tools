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
              'research/world_coordinate_physical_native.py', 'research/portable_coordinate_physical_cases.py']
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
    assert 'ev.part_damage or ev.interrupt_damage' in producer
    legacy_observer = texts['research/world_projectile_native.py']
    assert 'len(answer)%muzzles==0 and len({h.damage for h in answer})==1' in legacy_observer
    assert 'actorPoolCount(s)!=1' in texts['gpu/attack_group_runtime.slang']
    assert 'Coordinate physical probability/parts routing is unconnected.' in texts['gpu/attack_group_runtime.slang']
    assert 'coordinateAreaContains' in texts['gpu/coordinate_area_runtime.slang']
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
    dependencies = [
        dict(id='landing-probability', classification='gpu_port_gap',
             native='Geometry.landing -> aim.landing',
             work='Shared binary64 arcs, ordered occlusion, radial quadrature and cache-key rounding',
             verified_primitives=['interval-union', 'interval-intersection', 'interval-subtraction'],
             depends_on=['numeric-policy']),
        dict(id='physical-packet-expansion', classification='gpu_port_gap',
             native='CharState._coord_pellet',
             work='Per-pellet body/front/reach packets, conditional core probability, per-target damage rounding',
             depends_on=['landing-probability', 'physical-native-observation']),
        dict(id='coordinate-shot-groups', classification='adapter_gap',
             native='battle_attack_group_runtime.Producer.wrap_fire / packet_scope',
             work='Observe expanded physical packets and collect BODY/ADD receipts without counting PART/INTERRUPT as enemies',
             depends_on=['physical-packet-expansion', 'physical-native-observation']),
        dict(id='physical-native-observation', classification='reference_adapter',
             native='world_projectile_native.capture_projectile_shots',
             replacement_observer='research/world_coordinate_physical_native.py',
             reference_tests='tests/test_coordinate_physical_reference.py',
             scope='Expected mode authored worlds; no GPU or group proof',
             legacy_equal_packet_observer_preserved=True,
             depends_on=[]),
        dict(id='physical-rng', classification='gpu_port_gap',
             native='CharState._coord_pellet -> sample_landing',
             work='Preserve random draw count/order, angle requirement, front-most and reach routing',
             depends_on=['physical-packet-expansion', 'numeric-policy']),
        dict(id='manual-coordinate-aim', classification='gpu_port_gap',
             native='CharState._aim_point / simulate._resolve_aims',
             work='Authored coordinate waypoints and frame camera arbitration', depends_on=[]),
        dict(id='numeric-policy', classification='gpu_numeric_implementation_gap',
             work='Implement selected deterministic shared numeric contract; retain native host disagreement evidence',
             user_decision_required=False, implementation_required=True, depends_on=[]),
    ]
    return dict(schema=1, passed=True, scope='Source audit and dependency plan only',
                native_model_available=True, public_gpu_admitted=False,
                private_composed_arena_verified=True, private_physical_scope='body-only',
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
                logical_pellets_equal_emitted_packets=False, dependencies=dependencies,
                source_sha256={p: hashlib.sha256(t.encode()).hexdigest() for p, t in texts.items()},
                model_gap_audit=model, gpu_calls=0, native_battle_calls=0,
                calculation_verified=False, full_goal_complete=False)
