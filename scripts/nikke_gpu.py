"""Portable GPU proof CLI. Packages are immutable inputs; captures are append-only runs."""
import argparse
import array
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import platform
import runpy
import site
import stat
import subprocess
import sys
import time
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/p) for p in ('app', 'research', 'scripts')]
# No GPU/backend/native imports at startup: collect/audit must work without them.
SUITES = {
    'projectile': dict(script='research/verify-world-projectile-short.py',
                       golden='research/portable-world-projectile-short-expected.json',
                       source='gpu/world_projectile_entry.slang', inputs=63, native=52,
                       tests=['test_portable_projectiles.py', 'test_portable_real_binding_proof.py','test_portable_readiness.py','test_portable_compile_cache.py']),
    'readiness':dict(script='research/verify-world-readiness-short.py',
                       golden='research/portable-world-readiness-v5-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=81,native=60,
                       tests=['test_portable_readiness.py','test_portable_burst_recipients.py','test_portable_compile_cache.py','test_portable_gpu_cli.py','test_portable_compile_cli.py','test_portable_cuda_artifact.py','test_portable_phase_audit.py','test_portable_windows_cleanup.py','test_portable_windows_observer.py']),
    'recipients':dict(script='research/verify-world-recipients-short.py',
                       golden='research/portable-world-recipients-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=6,native=6,
                       tests=['test_portable_recipient_extension.py']),
    'burst-recipients':dict(script='research/verify-world-burst-recipients-short.py',
                       golden='research/portable-world-burst-recipients-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=13,native=13,
                       tests=['test_portable_burst_recipients.py']),
    'lost-hp-roster':dict(script='research/verify-world-lost-hp-rosters-short.py',
                       golden='research/portable-world-projectile-short-expected.json',
                       source='gpu/world_projectile_entry.slang',inputs=8,native=8,development_only=True,
                       tests=['test_portable_readiness.py','test_portable_real_binding_proof.py']),
    'reload': dict(script='research/verify-world-reload-short.py',
                   golden='research/portable-world-reload-short-expected.json',
                   source='gpu/world_reload_entry.slang', inputs=65, native=46,
                   tests=['test_portable_world_reload.py']),
}
SUITES['lost-hp-diagnostic']=dict(SUITES['lost-hp-roster'],source='gpu/world_projectile_admission_entry.slang')
SUITES['stun']=dict(script='research/verify-world-stun-short.py',golden='research/portable-world-stun-short-expected.json',
                   source='gpu/world_projectile_entry.slang',inputs=46,native=36,
                   tests=['test_portable_stun.py'])
SUITES['burst-recipients-diagnostic']=dict(SUITES['burst-recipients'],source='gpu/world_projectile_admission_entry.slang',development_only=True)
SUITES['roster-regression']=dict(script='research/verify-world-roster-regression-short.py',
    golden='research/portable-world-roster-regression-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=86,native=86,
    tests=['test_portable_roster_regression.py','test_portable_real_binding_proof.py'])
SUITES['skill-cooldown']=dict(script='research/verify-world-skill-cooldown-short.py',
    golden='research/portable-world-skill-cooldown-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=25,native=21,
    tests=['test_portable_skill_cooldown.py','test_portable_typed_recipient_delegation.py'])
SUITES['regression']=dict(script='research/verify-world-regression-short.py',
    golden='research/portable-world-revival-notify-regression-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=759,native=602,
    tests=['test_portable_gpu_cli.py','test_portable_gpu_replay.py','test_portable_phase_audit.py','test_portable_regression_adapter.py','test_portable_roster_regression.py',
           'test_portable_readiness.py','test_portable_stun.py','test_portable_typed_recipient_delegation.py',
           'test_portable_skill_cooldown.py','test_portable_healing_storage.py','test_portable_trigger_reduction.py','test_portable_skill_critical.py','test_portable_skill_interval.py','test_portable_skill_interval_flat.py','test_portable_lazy_bank.py','test_portable_compiler_stats.py','test_portable_base_copy.py','test_portable_seal.py','test_portable_persona.py','test_portable_compile_cache.py','test_portable_named_magnitude.py','test_portable_enemy_selection.py','test_portable_capture_storage.py','test_portable_attack_magnitude.py','test_portable_revive_reference.py','test_portable_revival.py'])
SUITES['healing-storage']=dict(script='research/verify-world-healing-storage-short.py',
    golden='research/portable-world-healing-storage-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=51,native=39,development_only=True,
    tests=['test_portable_healing_storage.py'])
SUITES['roster-admission-diagnostic']=dict(script='research/verify-world-roster-regression-short.py',
    golden='research/portable-world-roster-regression-short-expected.json',
    source='gpu/world_projectile_admission_entry.slang',inputs=62,native=62,development_only=True,
    tests=['test_portable_real_binding_proof.py'])
SUITES['trigger-reduction']=dict(script='research/verify-world-trigger-reduction-short.py',
    golden='research/portable-world-trigger-reduction-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=48,native=40,development_only=True,
    tests=['test_portable_trigger_reduction.py'])
SUITES['skill-critical']=dict(script='research/verify-world-skill-critical-short.py',
    golden='research/portable-world-skill-critical-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=36,native=26,development_only=True,
    tests=['test_portable_skill_critical.py'])
SUITES['skill-interval']=dict(script='research/verify-world-skill-interval-short.py',
    golden='research/portable-world-skill-interval-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=32,native=28,development_only=True,
    tests=['test_portable_skill_interval.py'])
SUITES['skill-interval-flat']=dict(script='research/verify-world-skill-interval-flat-short.py',
    golden='research/portable-world-skill-interval-flat-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=57,native=40,development_only=True,
    tests=['test_portable_skill_interval_flat.py'])
SUITES['lazy-bank']=dict(script='research/verify-world-lazy-bank-short.py',
    golden='research/portable-world-lazy-bank-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=8,native=7,development_only=True,
    tests=['test_portable_lazy_bank.py','test_portable_compiler_stats.py'])
SUITES['base-copy']=dict(script='research/verify-world-base-copy-short.py',
    golden='research/portable-world-base-copy-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=47,native=32,development_only=True,
    tests=['test_portable_base_copy.py','test_portable_readiness.py'])
SUITES['persona']=dict(script='research/verify-world-persona-short.py',
    golden='research/portable-world-persona-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=41,native=25,development_only=True,
    tests=['test_portable_persona.py','test_portable_recipient_extension.py'])

SUITES['named-magnitude']=dict(script='research/verify-world-named-magnitude-short.py',
    golden='research/portable-world-named-magnitude-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=54,native=43,development_only=True,
    tests=['test_portable_named_magnitude.py','test_portable_readiness.py'])

SUITES['attack-magnitude']=dict(script='research/verify-world-attack-magnitude-short.py',
    golden='research/portable-world-attack-magnitude-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=52,native=42,development_only=False,
    tests=['test_portable_attack_magnitude.py','test_portable_named_magnitude.py','test_portable_readiness.py'])
SUITES['attack-magnitude-diagnostic']=dict(SUITES['attack-magnitude'],source='gpu/world_projectile_admission_entry.slang')

SUITES['enemy-selection']=dict(script='research/verify-world-enemy-selection-short.py',
    golden='research/portable-world-enemy-selection-short-expected.json',
    source='gpu/world_projectile_entry.slang',inputs=60,native=51,development_only=True,
    tests=['test_portable_enemy_selection.py','test_portable_readiness.py'])

SUITES['enemy-selection-diagnostic']=dict(SUITES['enemy-selection'],source='gpu/world_projectile_admission_entry.slang',require_rejection_stage=True)
SUITES['roster-skill-diagnostic']=dict(SUITES['roster-admission-diagnostic'],source='gpu/world_projectile_skill_diagnostic_entry.slang')

SUITES['revive']=dict(script='research/verify-world-revive-short.py',golden='research/portable-world-revive-short-expected.json',source='gpu/world_projectile_entry.slang',inputs=35,native=26,development_only=True,tests=['test_portable_revive_reference.py','test_portable_revival.py'])
SUITES['revive-diagnostic']=dict(SUITES['revive'],source='gpu/world_projectile_admission_entry.slang',require_rejection_stage=True)

SCHEMA = 1
SUITES['regression-resident']=dict(SUITES['regression'],source='gpu/world_projectile_resident_entry.slang',golden='research/portable-world-phases-resident-regression-short-expected.json',development_only=False,tests=SUITES['regression']['tests']+['test_portable_resident_layout.py','test_portable_resident_transport.py','test_portable_resident_build.py','test_portable_module_check.py'])
SUITES['entry-reload']=dict(script='research/verify-world-entry-reload-short.py',golden='research/portable-world-entry-reload-short-expected.json',source='gpu/world_entry_reload_resident_entry.slang',inputs=37,native=31,development_only=False,tests=['test_portable_entry_reload_full_reference.py','test_portable_entry_reload_gpu.py','test_portable_combat.py','test_portable_resident_layout.py'])
SUITES['entry-reload-regression']=dict(SUITES['regression-resident'],script='research/verify-world-entry-reload-regression-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-definition-view-regression-short-expected.json',inputs=796,native=633,development_only=False,tests=SUITES['regression-resident']['tests']+['test_portable_entry_reload_gpu.py','test_portable_entry_reload_full_reference.py','test_portable_weapon_phases.py','test_portable_offline_assembly.py','test_portable_readback_stream.py','test_portable_regression_compact.py','test_portable_file_transport.py','test_portable_cpu_batch.py','test_portable_query_boundaries.py','test_portable_ptx_stats.py'])
SUITES['resident-binding']=dict(script='research/verify-resident-binding-short.py',golden='research/portable-resident-binding-file-transfer-short-expected.json',source='gpu/resident_runtime_binding_probe.slang',inputs=4,native=4,development_only=False,tests=['test_portable_resident_layout.py','test_portable_resident_transport.py','test_portable_resident_build.py','test_portable_module_check.py'])
SUITES['entry-reload-regression']['tests'].append('test_portable_heal_share_reference.py')
SUITES['entry-reload-regression']['tests'].append('test_portable_phase_codegen.py')
SUITES['entry-reload-regression']['tests'].append('test_portable_heal_share_extra_reference.py')
SUITES['entry-reload-regression']['tests'].append('test_portable_definition_view.py')
SUITES['entry-reload-regression']['tests'].append('test_portable_readiness_semantics.py')
SUITES['entry-reload-regression']['tests'].append('test_portable_heal_share_targets.py')
SUITES['entry-reload-regression']['tests'].append('test_portable_heal_share_lifesteal.py')
SUITES['definition-view']=dict(script='research/verify-definition-view-short.py',source='gpu/definition_view_probe.slang',
    golden='research/portable-definition-view-probe-expected.json',inputs=6,native=6,development_only=False,
    tests=['test_portable_definition_view.py','test_portable_resident_layout.py','test_portable_resident_transport.py'])
SUITES['damage-factors']=dict(script='research/verify-damage-factors-short.py',source='gpu/damage_factors_probe.slang',
    golden='research/portable-damage-factors-short-expected.json',inputs=16,native=16,development_only=False,
    tests=['test_portable_damage_factors.py'])
SUITES['lost-hp-attack']=dict(script='research/verify-world-lost-hp-attack-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-lost-hp-attack-short-expected.json',inputs=29,native=21,development_only=False,tests=['test_portable_lost_hp_attack_reference.py','test_portable_lost_hp_attack.py','test_portable_readiness.py','test_portable_definition_view.py','test_portable_mode_capacity.py','test_portable_query_boundaries.py','test_portable_seal.py','test_portable_cpu_batch.py'])
SUITES['pellet-shot']=dict(script='research/verify-world-pellet-shot-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-pellet-shot-short-expected.json',inputs=36,native=21,development_only=False,tests=['test_portable_pellet_shot_reference.py','test_portable_pellet_shot.py','test_portable_readiness.py','test_portable_definition_view.py','test_portable_weapon_phases.py','test_portable_query_boundaries.py','test_portable_seal.py','test_portable_cpu_batch.py'])
SUITES['ammo-equivalent']=dict(script='research/verify-world-ammo-equivalent-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-ammo-equivalent-short-expected.json',inputs=46,native=29,development_only=False,tests=['test_portable_manual_swap_reference.py','test_portable_ammo_equivalent_reference.py','test_portable_ammo_equivalent.py','test_portable_readiness_semantics.py','test_portable_definition_view.py','test_portable_skill_hp_basis.py','test_portable_physical_interrupt.py','test_portable_seal.py','test_portable_cpu_batch.py'])
SUITES['ammo-equivalent-rosters']=dict(SUITES['ammo-equivalent'],script='research/verify-world-ammo-equivalent-rosters-short.py',golden='research/portable-world-ammo-equivalent-rosters-short-expected.json',inputs=2,native=2,tests=['test_portable_ammo_equivalent.py','test_portable_definition_view.py','test_portable_real_binding_proof.py'])
SUITES['ammo-equivalent-catalogue']=dict(SUITES['ammo-equivalent'],script='research/verify-world-ammo-equivalent-catalogue-short.py',golden='research/portable-world-ammo-equivalent-catalogue-short-expected.json',inputs=1,native=1)
SUITES['manual-swap']=dict(SUITES['ammo-equivalent'],script='research/verify-world-manual-swap-short.py',golden='research/portable-world-manual-swap-short-expected.json',inputs=30,native=23,development_only=False,parent_oracle_reuse=True,tests=SUITES['ammo-equivalent']['tests']+['test_portable_accuracy_predicate_reference.py','test_portable_parent_oracles.py','test_portable_manual_swap.py','test_portable_weapon_phases.py','test_portable_query_boundaries.py'])
SUITES['accuracy-predicate']=dict(SUITES['manual-swap'],script='research/verify-world-accuracy-predicate-short.py',golden='research/portable-world-accuracy-predicate-short-expected.json',inputs=32,native=26,development_only=False,tests=SUITES['manual-swap']['tests']+['test_portable_accuracy_predicate.py'])
SUITES['accuracy-predicate-diagnostic']=dict(SUITES['accuracy-predicate'],source='gpu/world_accuracy_admission_entry.slang',development_only=True)
SUITES['accuracy-predicate-rosters']=dict(SUITES['accuracy-predicate'],script='research/verify-world-accuracy-predicate-rosters-short.py',golden='research/portable-world-accuracy-predicate-rosters-short-expected.json',inputs=2,native=2)
SUITES['undying-predicate']=dict(SUITES['accuracy-predicate'],script='research/verify-world-undying-predicate-short.py',golden='research/portable-world-undying-predicate-short-expected.json',inputs=28,native=22,development_only=False,tests=SUITES['accuracy-predicate']['tests']+['test_portable_undying_predicate_reference.py','test_portable_undying_predicate.py','test_portable_state_predicate_reference.py','test_portable_ally_random_reference.py','test_portable_state_work_routing.py'])
SUITES['ally-random-gpu']=dict(SUITES['undying-predicate'],script='research/verify-world-ally-random-short.py',golden='research/portable-world-ally-random-short-expected.json',inputs=30,native=20,development_only=True,tests=SUITES['undying-predicate']['tests']+['test_portable_ally_random_gpu.py'])
SUITES['state-focus']=dict(SUITES['ally-random-gpu'],script='research/verify-world-state-focus-short.py',golden='research/portable-world-state-focus-short-expected.json',inputs=66,native=54,development_only=True,tests=SUITES['ally-random-gpu']['tests']+['test_portable_state_focus.py','test_portable_interrupt_aim_reference.py'])
SUITES['state-focus-rosters']=dict(SUITES['state-focus'],script='research/verify-world-state-focus-rosters-short.py',golden='research/portable-world-state-focus-rosters-short-expected.json',inputs=6,native=6,tests=['test_portable_late_attack_random_reference.py','test_portable_state_work_routing.py','test_portable_state_focus_rosters.py','test_portable_state_focus.py','test_portable_definition_view.py','test_portable_real_binding_proof.py'])
SUITES['late-attack-random']=dict(SUITES['state-focus-rosters'],script='research/verify-world-late-attack-random-short.py',golden='research/portable-world-late-attack-random-short-expected.json',inputs=19,native=11,tests=SUITES['state-focus-rosters']['tests']+['test_portable_native_query.py','test_portable_weapon_phases.py','test_portable_query_boundaries.py','test_quantity_specs.py'])
SUITES['mixed-query']=dict(SUITES['late-attack-random'],script='research/verify-world-mixed-query-short.py',golden='research/portable-world-mixed-query-short-expected.json',inputs=6,native=6,development_only=False,tests=['test_portable_mixed_query.py','test_portable_scratch_layout.py','test_portable_ordered_history.py','test_portable_generation_request.py'])
SUITES['mixed-query-diagnostic']=dict(SUITES['mixed-query'],script='research/verify-world-mixed-query-diagnostic-short.py',source='gpu/world_heal_share_diagnostic_entry.slang',golden='research/portable-world-mixed-query-diagnostic-short-expected.json',tests=SUITES['mixed-query']['tests']+['test_portable_heal_share_trace.py'])
SUITES['interrupt-aim']=dict(SUITES['mixed-query'],script='research/verify-world-interrupt-aim-short.py',golden='research/portable-world-interrupt-aim-short-expected.json',inputs=24,native=24,development_only=True,tests=['test_portable_interrupt_aim_reference.py','test_portable_interrupt_aim.py','test_portable_state_focus.py','test_portable_definition_view.py','test_portable_physical_interrupt.py','test_portable_scratch_layout.py','test_portable_state_work_routing.py'],support_files=['research/portable-interrupt-aim-rejection-stage.json'])
SUITES['interrupt-aim-diagnostic']=dict(SUITES['interrupt-aim'],script='research/verify-world-interrupt-aim-diagnostic-short.py',source='gpu/world_interrupt_aim_diagnostic_entry.slang',golden='research/portable-world-interrupt-aim-diagnostic-short-expected.json')
SUITES['aimed-factors']=dict(SUITES['interrupt-aim'],script='research/verify-world-aimed-factor-short.py',golden='research/portable-world-aimed-factor-short-expected.json',inputs=8,native=8,tests=['test_portable_aimed_packet_reference.py','test_portable_aimed_factor.py','test_portable_definition_view.py','test_portable_physical_interrupt.py','test_portable_state_focus.py','test_portable_state_work_routing.py'])
SUITES['aimed-factors-diagnostic']=dict(SUITES['aimed-factors'],script='research/verify-world-aimed-factor-diagnostic-short.py',source='gpu/world_interrupt_aim_diagnostic_entry.slang',golden='research/portable-world-aimed-factor-diagnostic-short-expected.json')
SUITES['aimed-area']=dict(SUITES['aimed-factors'],script='research/verify-world-aimed-area-short.py',golden='research/portable-world-aimed-area-short-expected.json',inputs=12,native=12,tests=['test_portable_aimed_area.py','test_portable_aimed_packet_reference.py','test_portable_definition_view.py','test_portable_physical_interrupt.py','test_portable_scratch_layout.py','test_portable_interrupt_aim.py','test_portable_state_work_routing.py'])
SUITES['aimed-area-diagnostic']=dict(SUITES['aimed-area'],script='research/verify-world-aimed-area-diagnostic-short.py',source='gpu/world_interrupt_aim_diagnostic_entry.slang',golden='research/portable-world-aimed-area-diagnostic-short-expected.json')
SUITES['aimed-callback']=dict(SUITES['aimed-area-diagnostic'],script='research/verify-world-aimed-callback-short.py',golden='research/portable-world-aimed-callback-short-expected.json',inputs=20,native=20,tests=['test_portable_aimed_callback.py','test_portable_gpu_cli.py','test_portable_cpu_batch.py','test_portable_aimed_area.py','test_portable_physical_interrupt.py','test_portable_scratch_layout.py','test_portable_state_work_routing.py'])
SUITES['aimed-rosters']=dict(SUITES['aimed-area'],script='research/verify-world-aimed-rosters-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-aimed-rosters-short-expected.json',inputs=12,native=12,parent_oracle_reuse=True,cpu_test_timeout=180,tests=['test_portable_aimed_rosters.py','test_portable_aimed_enemy.py','test_portable_state_work_routing.py','test_portable_state_focus_rosters.py','test_portable_real_binding_proof.py','test_portable_parent_oracles.py'])
SUITES['aimed-rosters']['support_files']=list(dict.fromkeys(SUITES['aimed-rosters'].get('support_files',[])+['research/portable-world-aimed-area-retention-short-expected.json']))
SUITES['aimed-enemy']=dict(SUITES['aimed-area-diagnostic'],script='research/verify-world-aimed-enemy-short.py',golden='research/portable-world-aimed-enemy-short-expected.json',inputs=6,native=6,tests=['test_portable_aimed_enemy.py','test_portable_aimed_area.py','test_portable_interrupt_aim.py','test_portable_definition_view.py'])
SUITES['squad-stage']=dict(SUITES['aimed-area'],script='research/verify-world-squad-stage-short.py',golden='research/portable-world-squad-stage-short-expected.json',inputs=30,native=16,tests=['test_portable_squad_stage.py','test_portable_ally_burst.py','test_portable_burst_recipients.py','test_portable_definition_view.py','test_portable_state_work_routing.py'])
SUITES['partial-charge']=dict(SUITES['squad-stage'],source='gpu/world_partial_charge_entry.slang',script='research/verify-world-partial-charge-short.py',golden='research/portable-world-partial-charge-short-expected.json',inputs=45,native=23,development_only=True,tests=['test_portable_partial_charge.py','test_portable_nonfull_charge_reference.py','test_portable_nonfull_charge_routing.py','test_portable_definition_view.py','test_portable_charge_control.py','test_portable_world_roster_input.py','test_portable_squad_stage.py'])
SUITES['partial-charge-rosters']=dict(SUITES['partial-charge'],script='research/verify-world-partial-charge-rosters-short.py',golden='research/portable-world-partial-charge-rosters-short-expected.json',inputs=4,native=4)
SUITES['partial-charge-extended']=dict(SUITES['partial-charge'],script='research/verify-world-partial-charge-extended-short.py',golden='research/portable-world-partial-charge-extended-short-expected.json',inputs=14,native=14,tests=SUITES['partial-charge']['tests']+['test_portable_partial_charge_extended.py'])
SUITES['partial-charge-reduction']=dict(SUITES['partial-charge'],script='research/verify-world-partial-charge-reduction-short.py',golden='research/portable-world-partial-charge-reduction-short-expected.json',inputs=11,native=7,tests=SUITES['partial-charge']['tests']+['test_portable_partial_charge_reduction.py'])
SUITES['partial-query']=dict(SUITES['partial-charge'],script='research/verify-world-partial-query-short.py',golden='research/portable-world-partial-query-short-expected.json',inputs=17,native=17,tests=SUITES['partial-charge']['tests']+['test_portable_partial_query.py'])
SUITES['partial-query-diagnostic']=dict(SUITES['partial-query'],script='research/verify-world-partial-query-diagnostic-short.py',source='gpu/world_partial_query_diagnostic_entry.slang',golden='research/portable-world-partial-query-diagnostic-short-expected.json',inputs=2,native=2,tests=SUITES['partial-query']['tests']+['test_portable_query_diagnostic.py'])
SUITES['not-core']=dict(SUITES['partial-query'],script='research/verify-world-not-core-short.py',source='gpu/world_not_core_entry.slang',golden='research/portable-world-not-core-short-expected.json',inputs=32,native=27,tests=['test_portable_not_core_reference.py','test_portable_not_core_routing.py','test_portable_not_core_gpu.py','test_portable_definition_view.py','test_portable_scratch_layout.py'])
SUITES['not-core-legacy-reject']=dict(SUITES['not-core'],script='research/verify-world-not-core-legacy-reject-short.py',source='gpu/world_partial_charge_entry.slang',golden='research/portable-world-not-core-legacy-reject-short-expected.json',inputs=1,native=0)
SUITES['duration-scaling']=dict(SUITES['not-core'],script='research/verify-world-duration-scaling-short.py',source='gpu/world_duration_scaling_entry.slang',golden='research/portable-world-duration-scaling-short-expected.json',inputs=47,native=40,tests=['test_portable_duration_scaling_reference.py','test_portable_duration_scaling_mixed.py','test_portable_duration_scaling_gpu.py','test_portable_definition_view.py','test_portable_scratch_layout.py'])
SUITES['duration-scaling-diagnostic']=dict(SUITES['duration-scaling'],script='research/verify-world-duration-scaling-diagnostic-short.py',source='gpu/world_duration_scaling_diagnostic_entry.slang',golden='research/portable-world-duration-scaling-diagnostic-short-expected.json')
SUITES['duration-scaling-legacy-reject']=dict(SUITES['duration-scaling'],script='research/verify-world-duration-scaling-legacy-reject-short.py',source='gpu/world_not_core_entry.slang',golden='research/portable-world-duration-scaling-legacy-reject-short-expected.json',inputs=1,native=0)
SUITES['leftmost']=dict(SUITES['duration-scaling'],script='research/verify-world-leftmost-short.py',source='gpu/world_leftmost_entry.slang',golden='research/portable-world-leftmost-short-expected.json',inputs=21,native=13,tests=['test_portable_leftmost.py','test_portable_recipient_extension.py','test_portable_burst_recipients.py','test_portable_definition_view.py'])
SUITES['below-def']=dict(SUITES['leftmost'],script='research/verify-world-below-def-short.py',source='gpu/world_below_def_entry.slang',golden='research/portable-world-below-def-short-expected.json',inputs=21,native=13,tests=['test_portable_below_def.py','test_portable_leftmost.py','test_portable_definition_view.py','test_portable_duration_scaling_gpu.py'])
SUITES['skill-weapon']=dict(SUITES['below-def'],script='research/verify-world-skill-weapon-short.py',golden='research/portable-world-skill-weapon-short-expected.json',inputs=10,native=10,tests=['test_portable_skill_weapon.py','test_portable_below_def.py','test_portable_leftmost.py','test_portable_definition_view.py','test_portable_development_generation.py'])
SUITES['below-def-retention']=dict(SUITES['below-def'],script='research/verify-world-below-def-retention-short.py',golden='research/portable-world-below-def-retention-short-expected.json',inputs=95,native=72,tests=SUITES['below-def']['tests']+['test_portable_leftmost_replay.py','test_portable_gpu_replay.py','test_portable_development_generation.py','test_portable_generation_request.py','test_portable_gpu_cli.py'])
SUITES['burst1-ally']=dict(SUITES['skill-weapon'],script='research/verify-world-burst1-ally-short.py',golden='research/portable-world-burst1-ally-short-expected.json',inputs=20,native=12,tests=['test_portable_burst1_ally.py','test_portable_definition_view.py','test_portable_skill_weapon.py'])
SUITES['burst1-ally-retention']=dict(SUITES['burst1-ally'],script='research/verify-world-burst1-ally-retention-short.py',golden='research/portable-world-burst1-ally-retention-short-expected.json',inputs=125,native=94,tests=list(dict.fromkeys(SUITES['below-def-retention']['tests']+SUITES['skill-weapon']['tests']+['test_portable_burst1_ally.py','test_portable_readiness_semantics.py'])))
SUITES['leftmost-rosters']=dict(SUITES['leftmost'],script='research/verify-world-leftmost-rosters-short.py',golden='research/portable-world-leftmost-rosters-short-expected.json',inputs=6,native=6)
SUITES['random-cleanse']=dict(SUITES['burst1-ally'],script='research/verify-world-random-cleanse-short.py',source='gpu/world_random_cleanse_entry.slang',golden='research/portable-world-random-cleanse-short-expected.json',inputs=50,native=38,tests=['test_portable_random_cleanse.py','test_portable_ally_random_gpu.py','test_portable_ally_random_reference.py','test_portable_definition_view.py','test_portable_readiness_semantics.py'])
SUITES['random-cleanse-retention']=dict(SUITES['random-cleanse'],script='research/verify-world-random-cleanse-retention-short.py',golden='research/portable-world-random-cleanse-retention-short-expected.json',inputs=175,native=132,tests=list(dict.fromkeys(SUITES['burst1-ally-retention']['tests']+SUITES['random-cleanse']['tests'])))
SUITES['generation-boundary']=dict(SUITES['random-cleanse-retention'],tests=['test_portable_generation_separation.py','test_portable_generation_cache.py','test_portable_resident_build.py','test_portable_required_cache_preflight.py','test_portable_cache_probe.py','test_portable_compile_cache.py','test_portable_cuda_artifact.py','test_portable_phase_audit.py','test_portable_gpu_cli.py','test_portable_gpu_replay.py','test_portable_development_generation.py'])
SUITES['named-enemy-reference']=dict(SUITES['random-cleanse-retention'],tests=['test_portable_named_enemy_reference.py','test_portable_actor_state_input.py','test_portable_named_states.py','test_portable_enemy_selection.py','test_portable_readiness_semantics.py','test_portable_reference_optimization.py'])
SUITES['named-enemy']=dict(SUITES['random-cleanse'],source='gpu/world_named_enemy_entry.slang',script='research/verify-world-named-enemy-short.py',golden='research/portable-world-named-enemy-short-expected.json',inputs=32,native=23,tests=['test_portable_named_enemy_reference.py','test_portable_named_enemy_gpu.py','test_portable_definition_view.py'])
SUITES['named-enemy-diagnostic']=dict(SUITES['named-enemy'],source='gpu/world_named_enemy_diagnostic_entry.slang',script='research/verify-world-named-enemy-diagnostic-short.py',golden='research/portable-world-named-enemy-diagnostic-short-expected.json',inputs=23,native=23)
SUITES['named-enemy-retention']=dict(SUITES['named-enemy'],script='research/verify-world-named-enemy-retention-short.py',golden='research/portable-world-named-enemy-retention-short-expected.json',inputs=207,native=155,tests=list(dict.fromkeys(SUITES['random-cleanse-retention']['tests']+SUITES['named-enemy']['tests'])))
SUITES['named-enemy-removal']=dict(SUITES['named-enemy'],script='research/verify-world-named-enemy-removal-short.py',golden='research/portable-world-named-enemy-removal-short-expected.json',inputs=23,native=16,tests=['test_portable_named_enemy_removal.py','test_portable_actor_mutation_input.py','test_portable_removal.py','test_portable_named_enemy_gpu.py'])
SUITES['named-enemy-removal-retention']=dict(SUITES['named-enemy-removal'],script='research/verify-world-named-enemy-removal-retention-short.py',golden='research/portable-world-named-enemy-removal-retention-short-expected.json',inputs=230,native=171,tests=list(dict.fromkeys(SUITES['named-enemy-retention']['tests']+SUITES['named-enemy-removal']['tests'])))
SUITES['named-enemy-removal-rosters']=dict(SUITES['named-enemy-removal'],script='research/verify-world-named-enemy-removal-rosters-short.py',golden='research/portable-world-named-enemy-removal-rosters-short-expected.json',inputs=2,native=2,tests=['test_portable_named_enemy_removal_rosters.py','test_portable_named_enemy_removal.py'])
SUITES['full-burst-landing-reference']=dict(SUITES['named-enemy-removal-retention'],tests=['test_portable_full_burst_landing_reference.py','test_attack_timing_specs.py','test_portable_named_enemy_removal.py','test_portable_readiness_semantics.py','test_portable_reference_optimization.py'])
SUITES['full-burst-landing']=dict(SUITES['named-enemy-removal'],source='gpu/world_full_burst_landing_entry.slang',script='research/verify-world-full-burst-landing-short.py',golden='research/portable-world-full-burst-landing-short-expected.json',inputs=26,native=13,tests=['test_portable_full_burst_landing_reference.py','test_portable_full_burst_landing_gpu.py','test_attack_timing_specs.py','test_portable_definition_view.py'])
SUITES['full-burst-landing-retention']=dict(SUITES['full-burst-landing'],script='research/verify-world-full-burst-landing-retention-short.py',golden='research/portable-world-full-burst-landing-retention-short-expected.json',inputs=258,native=186,tests=list(dict.fromkeys(SUITES['named-enemy-removal-retention']['tests']+SUITES['full-burst-landing']['tests'])))
SUITES['full-burst-landing-rosters']=dict(SUITES['full-burst-landing'],script='research/verify-world-full-burst-landing-rosters-short.py',golden='research/portable-world-full-burst-landing-rosters-short-expected.json',inputs=2,native=2,tests=['test_portable_full_burst_landing_reference.py','test_portable_full_burst_landing_gpu.py'])
SUITES['full-burst-queue']=dict(SUITES['full-burst-landing'],script='research/verify-world-full-burst-queue-short.py',golden='research/portable-world-full-burst-queue-short-expected.json',inputs=7,native=7,tests=['test_portable_full_burst_queue.py','test_portable_full_burst_landing_gpu.py','test_portable_full_burst_landing_reference.py'])
SUITES['full-burst-queue-retention']=dict(SUITES['full-burst-queue'],script='research/verify-world-full-burst-queue-retention-short.py',golden='research/portable-world-full-burst-queue-retention-short-expected.json',inputs=267,native=195,tests=list(dict.fromkeys(SUITES['full-burst-landing-retention']['tests']+SUITES['full-burst-queue']['tests'])))
SUITES['full-burst-capacity']=dict(SUITES['full-burst-queue'],script='research/verify-world-full-burst-capacity-short.py',golden='research/portable-world-full-burst-capacity-short-expected.json',inputs=5,native=4,tests=['test_portable_full_burst_capacity.py','test_portable_full_burst_queue.py','test_portable_full_burst_landing_gpu.py'])
SUITES['full-burst-capacity-retention']=dict(SUITES['full-burst-capacity'],script='research/verify-world-full-burst-capacity-retention-short.py',golden='research/portable-world-full-burst-capacity-retention-short-expected.json',inputs=272,native=199,cpu_test_timeout=90,tests=list(dict.fromkeys(SUITES['full-burst-queue-retention']['tests']+SUITES['full-burst-capacity']['tests'])))
SUITES['full-burst-query']=dict(SUITES['full-burst-landing'],script='research/verify-world-full-burst-query-short.py',golden='research/portable-world-full-burst-query-short-expected.json',inputs=19,native=19,tests=['test_portable_full_burst_query.py','test_portable_skill_hp_basis.py','test_portable_full_burst_landing_gpu.py'])
SUITES['full-burst-query-diagnostic']=dict(SUITES['full-burst-query'],source='gpu/world_full_burst_query_diagnostic_entry.slang',script='research/verify-world-full-burst-query-diagnostic-short.py',golden='research/portable-world-full-burst-query-diagnostic-short-expected.json')
SUITES['full-burst-query-retention']=dict(SUITES['full-burst-query'],script='research/verify-world-full-burst-query-retention-short.py',golden='research/portable-world-full-burst-query-retention-short-expected.json',inputs=291,native=218,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['full-burst-capacity-retention']['tests']+SUITES['full-burst-query']['tests'])))
SUITES['parent-fixed']=dict(SUITES['full-burst-query'],upstream_documents=['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'],source='gpu/world_parent_fixed_entry.slang',script='research/verify-world-parent-fixed-short.py',golden='research/portable-world-parent-fixed-short-expected.json',inputs=30,native=23,tests=['test_portable_parent_fixed.py','test_quantity_specs.py','test_portable_readiness_semantics.py'])
SUITES['parent-fixed']['tests'].append('test_portable_max_ammo_scaling_reference.py')
SUITES['parent-fixed-retention']=dict(SUITES['parent-fixed'],script='research/verify-world-parent-fixed-retention-short.py',golden='research/portable-world-parent-fixed-retention-short-expected.json',inputs=321,native=241,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['full-burst-query-retention']['tests']+SUITES['parent-fixed']['tests'])))
SUITES['max-ammo-scaling']=dict(SUITES['parent-fixed'],source='gpu/world_max_ammo_scaling_entry.slang',script='research/verify-world-max-ammo-scaling-short.py',golden='research/portable-world-max-ammo-scaling-short-expected.json',inputs=28,native=20,tests=SUITES['parent-fixed']['tests']+['test_portable_max_ammo_scaling.py'])
SUITES['max-ammo-scaling-retention']=dict(SUITES['max-ammo-scaling'],script='research/verify-world-max-ammo-scaling-retention-short.py',golden='research/portable-world-max-ammo-scaling-retention-short-expected.json',inputs=349,native=261,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['parent-fixed-retention']['tests']+SUITES['max-ammo-scaling']['tests'])))
SUITES['max-ammo-scaling-rosters']=dict(SUITES['max-ammo-scaling'],script='research/verify-world-max-ammo-scaling-rosters-short.py',golden='research/portable-world-max-ammo-scaling-rosters-short-expected.json',inputs=2,native=2,tests=['test_portable_max_ammo_scaling.py','test_portable_definition_view.py','test_portable_max_ammo_scaling_rosters.py'])
SUITES['heal-charge']=dict(SUITES['max-ammo-scaling'],source='gpu/world_heal_charge_entry.slang',script='research/verify-world-heal-charge-short.py',golden='research/portable-world-heal-charge-short-expected.json',inputs=37,native=29,development_only=True,tests=['test_portable_heal_charge_reference.py','test_portable_heal_charge_gpu.py','test_quantity_specs.py','test_portable_readiness_semantics.py'])
SUITES['heal-charge-retention']=dict(SUITES['heal-charge'],script='research/verify-world-heal-charge-retention-short.py',golden='research/portable-world-heal-charge-retention-short-expected.json',inputs=386,native=290,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['max-ammo-scaling-retention']['tests']+SUITES['heal-charge']['tests'])))
SUITES['heal-charge-lifetime']=dict(SUITES['heal-charge'],script='research/verify-world-heal-charge-lifetime-short.py',golden='research/portable-world-heal-charge-lifetime-short-expected.json',inputs=12,native=12,tests=['test_portable_heal_charge_lifetime.py','test_portable_heal_charge_gpu.py','test_portable_heal_charge_reference.py','test_portable_heal_charge_history.py','test_portable_ordered_history.py'])
SUITES['heal-charge-lifetime-retention']=dict(SUITES['heal-charge-lifetime'],script='research/verify-world-heal-charge-lifetime-retention-short.py',golden='research/portable-world-heal-charge-lifetime-retention-short-expected.json',inputs=398,native=302,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['heal-charge-retention']['tests']+SUITES['heal-charge-lifetime']['tests'])))
SUITES['heal-charge-rosters']=dict(SUITES['heal-charge'],script='research/verify-world-heal-charge-rosters-short.py',golden='research/portable-world-heal-charge-rosters-short-expected.json',inputs=4,native=4,tests=['test_portable_heal_charge_lifetime.py','test_portable_heal_charge_rosters.py','test_portable_definition_view.py','test_portable_heal_charge_history.py','test_portable_ordered_history.py'])
SUITES['damage-accum-battle']=dict(SUITES['heal-charge-lifetime'],source='gpu/world_damage_accum_entry.slang',script='research/verify-world-damage-accum-short.py',golden='research/portable-world-damage-accum-short-expected.json',inputs=62,native=52,development_only=True,support_files=['research/portable-world-heal-charge-lifetime-short-expected.json'],tests=['test_portable_damage_accum_battle.py','test_portable_damage_accum_core.py','test_portable_damage_accum_reference.py'])
SUITES['damage-accum-retention']=dict(SUITES['damage-accum-battle'],script='research/verify-world-damage-accum-retention-short.py',golden='research/portable-world-damage-accum-retention-short-expected.json',inputs=460,native=354,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['heal-charge-lifetime-retention']['tests']+SUITES['damage-accum-battle']['tests'])))
SUITES['damage-accum-rosters']=dict(SUITES['damage-accum-battle'],script='research/verify-world-damage-accum-rosters-short.py',golden='research/portable-world-damage-accum-rosters-short-expected.json',inputs=4,native=4,tests=SUITES['damage-accum-battle']['tests']+['test_portable_damage_accum_rosters.py'])
SUITES['projectile-chain']=dict(SUITES['damage-accum-battle'],source='gpu/world_projectile_chain_entry.slang',script='research/verify-world-projectile-chain-short.py',golden='research/portable-world-projectile-chain-short-expected.json',inputs=32,native=24,development_only=True,tests=['test_portable_projectile_chain_reference.py','test_portable_projectile_chain_gpu.py','test_portable_damage_accum_battle.py'])
SUITES['projectile-chain-retention']=dict(SUITES['projectile-chain'],script='research/verify-world-projectile-chain-retention-short.py',golden='research/portable-world-projectile-chain-retention-short-expected.json',inputs=492,native=378,development_only=False,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['damage-accum-retention']['tests']+SUITES['projectile-chain']['tests'])))
SUITES['projectile-chain-rosters']=dict(SUITES['projectile-chain'],script='research/verify-world-projectile-chain-rosters-short.py',golden='research/portable-world-projectile-chain-rosters-short-expected.json',inputs=2,native=2,tests=SUITES['projectile-chain']['tests']+['test_portable_projectile_chain_rosters.py'])
SUITES['projectile-chain-reference']=dict(SUITES['damage-accum-battle'],tests=['test_portable_projectile_chain_reference.py','test_portable_projectile_chain_rosters.py','test_portable_damage_accum_core.py'],support_files=['research/portable-world-heal-charge-lifetime-short-expected.json','research/portable_projectile_chain_cases.py','research/world_projectile_chain_native.py','research/portable_projectile_chain_contracts.py','research/portable_projectile_chain_roster_cases.py'])
SUITES['damage-accum-core']=dict(script='research/verify-damage-accum-core-short.py',golden='research/portable-damage-accum-core-short-expected.json',source='gpu/damage_accum_probe.slang',inputs=41,native=34,support_files=['research/portable-world-heal-charge-lifetime-short-expected.json'],tests=['test_portable_damage_accum_core.py','test_portable_damage_accum_reference.py','test_portable_packet_stage.py'])
SUITES['destructible-target-core']=dict(SUITES['damage-accum-core'],script='research/verify-destructible-target-core-short.py',golden='research/portable-destructible-target-core-short-expected.json',source='gpu/destructible_target_probe.slang',support_files=SUITES['damage-accum-core']['support_files']+['research/portable-world-projectile-chain-short-expected.json'],inputs=46,native=24,upstream_documents=['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'],development_only=False,tests=['test_destructible_target_state.py','test_portable_damage_accum_core.py','test_portable_model_gap_audit.py','test_portable_readiness_semantics.py','test_portable_parent_fixed.py'])
SUITES['saved-core-report-audit']=dict(SUITES['damage-accum-core'],tests=['test_portable_saved_core_report.py','test_portable_compile_cache.py'],support_files=['research/portable-damage-accum-core-short-expected.json','tests/fixtures/cuda-core-report-v4/generated/damage_accum_probe.cu','tests/fixtures/cuda-core-report-v4/generated/damage_accum_probe.metal'])
SUITES['destructible-target-core']['tests'].append('test_portable_authored_case_purity.py')
SUITES['destructible-world']=dict(SUITES['destructible-target-core'],script='research/verify-destructible-world-short.py',golden='research/portable-destructible-world-short-expected.json',source='gpu/destructible_world_probe.slang',inputs=33,native=21,development_only=False,tests=['test_destructible_world.py','test_destructible_target_state.py'])
SUITES['destructible-counter']=dict(SUITES['destructible-world'],script='research/verify-destructible-counter-short.py',golden='research/portable-destructible-counter-short-expected.json',source='gpu/destructible_counter_probe.slang',inputs=18,native=13,development_only=False,tests=['test_destructible_counter.py','test_destructible_world.py','test_target_counter_runtime.py','test_portable_authored_case_purity.py','test_portable_readiness_semantics.py','test_destructible_target_state.py'])
SUITES['destructible-attack']=dict(SUITES['destructible-counter'],script='research/verify-destructible-attack-short.py',golden='research/portable-destructible-attack-short-expected.json',source='gpu/destructible_attack_probe.slang',inputs=15,native=9,development_only=False,tests=['test_destructible_attack.py','test_destructible_counter.py','test_destructible_world.py','test_target_counter_runtime.py'])
SUITES['destructible-skill']=dict(SUITES['destructible-attack'],script='research/verify-destructible-skill-short.py',golden='research/portable-destructible-skill-short-expected.json',source='gpu/destructible_skill_probe.slang',inputs=18,native=10,development_only=False,support_files=[*SUITES['destructible-attack'].get('support_files',()),'research/portable-destructible-attack-short-expected.json'],tests=['test_destructible_skill.py','test_destructible_attack.py','test_destructible_counter.py','test_destructible_world.py','test_target_counter_runtime.py','test_portable_readiness_semantics.py'])
SUITES['destructible-frame']=dict(SUITES['destructible-skill'],script='research/verify-destructible-frame-short.py',golden='research/portable-destructible-frame-short-expected.json',source='gpu/destructible_frame_probe.slang',inputs=26,native=17,development_only=False,tests=['test_destructible_frame.py',*SUITES['destructible-skill']['tests']])
SUITES['destructible-frame']['tests'].append('test_portable_packet_stage.py')
SUITES['destructible-frame']['tests'].append('test_destructible_battle.py')
SUITES['destructible-battle']=dict(SUITES['destructible-frame'],script='research/verify-destructible-battle-short.py',golden='research/portable-destructible-battle-short-expected.json',source='gpu/destructible_battle_entry.slang',inputs=44,native=31,development_only=False,output_words=1048576)
SUITES['destructible-battle']['tests']=SUITES['destructible-frame']['tests']+['test_portable_file_transport.py','test_portable_resident_transport.py','test_portable_world_reload.py','test_portable_seal.py']
SUITES['destructible-battle']['tests'].append('test_portable_readback_blocks.py')
SUITES['destructible-battle']['support_files']=[*SUITES['destructible-frame'].get('support_files',()),'research/destructible-counter-battle-evidence/prior25-golden.json']
SUITES['destructible-original-battle']=dict(SUITES['destructible-battle'],script='research/verify-destructible-original-battle-short.py',golden='research/portable-destructible-original-battle-short-expected.json',inputs=8,native=8,development_only=False,tests=[*SUITES['destructible-battle']['tests'],'test_world_authored_roster.py','test_destructible_damage_policy.py','test_portable_storage_budget.py'],support_files=[*SUITES['destructible-battle']['support_files'],'research/portable-destructible-battle-short-expected.json','research/portable-world-projectile-chain-retention-short-expected.json'])
SUITES['destructible-modifier']=dict(script='research/verify-destructible-modifier-short.py',golden='research/portable-destructible-modifier-short-expected.json',source='gpu/destructible_modifier_probe.slang',inputs=29,native=20,development_only=False,output_words=159744,tests=['test_destructible_modifier_gpu.py','test_destructible_damage_policy.py','test_portable_storage_budget.py','test_portable_seal.py','test_portable_readiness_semantics.py'],support_files=['research/portable-destructible-battle-short-expected.json','research/portable-world-projectile-chain-retention-short-expected.json'])
SUITES['destructible-modifier-battle']=dict(SUITES['destructible-original-battle'],script='research/verify-destructible-modifier-battle-short.py',golden='research/portable-destructible-modifier-battle-short-expected.json',source='gpu/destructible_modifier_battle_entry.slang',inputs=18,native=12,development_only=False,tests=list(dict.fromkeys([*SUITES['destructible-original-battle']['tests'],'test_destructible_modifier_gpu.py','test_destructible_modifier_battle.py'])),support_files=[*SUITES['destructible-original-battle']['support_files'],'research/portable-destructible-original-battle-short-expected.json','research/portable-destructible-modifier-short-expected.json'])
SUITES['destructible-modifier-battle']['tests'].append('test_destructible_shield_battle.py')
SUITES['destructible-shield-battle']=dict(SUITES['destructible-modifier-battle'],script='research/verify-destructible-shield-battle-short.py',golden='research/portable-destructible-shield-battle-short-expected.json',source='gpu/destructible_shield_battle_entry.slang',inputs=88,native=58,development_only=False,tests=[*SUITES['destructible-modifier-battle']['tests'],'test_destructible_shield_gpu.py'],support_files=[*SUITES['destructible-modifier-battle']['support_files'],'research/portable-destructible-modifier-battle-short-expected.json'])
SUITES['destructible-hit-shield']=dict(SUITES['destructible-shield-battle'],script='research/verify-destructible-hit-shield-short.py',golden='research/portable-destructible-hit-shield-short-expected.json',inputs=111,native=76,development_only=False,tests=[*SUITES['destructible-shield-battle']['tests'],'test_destructible_hit_shield.py'],support_files=[*SUITES['destructible-shield-battle']['support_files'],'research/portable-destructible-shield-battle-short-expected.json'])
SUITES['destructible-hit-shield']['tests'].append('test_destructible_weapon_shield.py')
SUITES['destructible-weapon-shield']=dict(SUITES['destructible-hit-shield'],script='research/verify-destructible-weapon-shield-short.py',golden='research/portable-destructible-weapon-shield-short-expected.json',source='gpu/destructible_weapon_shield_entry.slang',inputs=141,native=98,development_only=False,tests=[*SUITES['destructible-hit-shield']['tests'],'test_destructible_weapon_gpu.py'],support_files=[*SUITES['destructible-hit-shield']['support_files'],'research/portable-destructible-hit-shield-short-expected.json'])
SUITES['destructible-weapon-rosters']=dict(SUITES['destructible-weapon-shield'],script='research/verify-destructible-weapon-rosters-short.py',golden='research/portable-destructible-weapon-rosters-short-expected.json',inputs=2,native=2,development_only=False,tests=['test_destructible_weapon_rosters.py','test_portable_readiness_semantics.py','test_destructible_skill_rosters.py'],support_files=[*SUITES['destructible-weapon-shield']['support_files'],SUITES['destructible-weapon-shield']['golden']])
SUITES['destructible-skill-rosters']=dict(SUITES['destructible-weapon-rosters'],script='research/verify-destructible-skill-rosters-short.py',golden='research/portable-destructible-skill-rosters-short-expected.json',source='gpu/destructible_roster_skill_entry.slang',inputs=16,native=4,development_only=True,cpu_test_timeout=90,tests=[*SUITES['destructible-weapon-rosters']['tests'],'test_destructible_weapon_gpu.py','test_destructible_skill_gpu.py'])
SUITES['destructible-skill-retention']=dict(SUITES['destructible-skill-rosters'],script='research/verify-destructible-skill-retention-short.py',golden='research/portable-destructible-skill-retention-short-expected.json',inputs=157,native=102)
SUITES['destructible-skill-misato-retention']=dict(SUITES['destructible-skill-rosters'],script='research/verify-destructible-weapon-rosters-short.py',golden='research/portable-destructible-skill-misato-short-expected.json',inputs=2,native=2)
for _skill_sealed in ('destructible-skill-retention','destructible-skill-misato-retention'):SUITES[_skill_sealed]['development_only']=False
SUITES['destructible-aoe-burst-rosters']=dict(SUITES['destructible-skill-rosters'],script='research/verify-destructible-aoe-burst-rosters-short.py',golden='research/portable-destructible-aoe-burst-rosters-short-expected.json',inputs=18,native=16,development_only=False)
SUITES['destructible-aoe-burst-rosters']['tests']=[*SUITES['destructible-skill-rosters']['tests'],'test_destructible_aoe_burst_rosters.py']
SUITES['destructible-body-lifesteal']=dict(SUITES['destructible-aoe-burst-rosters'],script='research/verify-destructible-body-lifesteal-short.py',golden='research/portable-destructible-body-lifesteal-short-expected.json',source='gpu/destructible_roster_lifesteal_entry.slang',inputs=13,native=10,development_only=False)
SUITES['destructible-body-lifesteal']['tests']=[*SUITES['destructible-skill-rosters']['tests'],'test_destructible_body_lifesteal.py']
SUITES['destructible-body-lifesteal-retention']=dict(SUITES['destructible-body-lifesteal'],script='research/verify-destructible-body-lifesteal-retention-short.py',golden='research/portable-destructible-body-lifesteal-retention-short-expected.json',inputs=31,native=26,development_only=False)
SUITES['destructible-body-lifesteal-retention']['tests']=[*SUITES['destructible-body-lifesteal']['tests'],'test_destructible_aoe_burst_rosters.py']
SUITES['destructible-body-accum']=dict(SUITES['destructible-body-lifesteal'],script='research/verify-destructible-body-accum-short.py',golden='research/portable-destructible-body-accum-short-expected.json',source='gpu/destructible_roster_accum_entry.slang',inputs=18,native=14,development_only=True)
SUITES['destructible-body-accum']['tests']=['test_destructible_body_accum.py']
SUITES['destructible-body-accum-retention']=dict(SUITES['destructible-body-accum'],script='research/verify-destructible-body-accum-retention-short.py',golden='research/portable-destructible-body-accum-retention-short-expected.json',inputs=49,native=40,tests=[*SUITES['destructible-body-lifesteal-retention']['tests'],'test_destructible_body_accum.py'])
SUITES['destructible-body-accum-retention']['development_only']=False
SUITES['destructible-body-heal-share']=dict(SUITES['destructible-body-accum'],script='research/verify-destructible-body-heal-share-short.py',golden='research/portable-destructible-body-heal-share-short-expected.json',inputs=12,native=12,tests=['test_destructible_body_heal_share.py','test_portable_heal_share_reference.py'])
SUITES['destructible-body-heal-share-retention']=dict(SUITES['destructible-body-heal-share'],script='research/verify-destructible-body-heal-share-retention-short.py',golden='research/portable-destructible-body-heal-share-retention-short-expected.json',inputs=61,native=52,tests=[*SUITES['destructible-body-accum-retention']['tests'],'test_destructible_body_heal_share.py','test_portable_heal_share_reference.py'])
SUITES['destructible-body-heal-share-retention']['development_only']=False
SUITES['destructible-body-heal-share-retention'].update(parent_oracle_reuse=True,cpu_test_timeout=120)
SUITES['destructible-body-heal-share-retention']['tests']+=['test_portable_parent_oracles.py','test_destructible_parent_oracles.py']
SUITES['destructible-body-heal-share-retention']['tests'].append('test_battle_attack_group_runtime.py')
SUITES['attack-group-battle']=dict(output_words=1048576,upstream_documents=['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'],script='research/verify-world-attack-group-battle-short.py',golden='research/portable-world-attack-group-battle-short-expected.json',source='gpu/world_attack_group_entry.slang',inputs=32,native=22,development_only=False,tests=['test_battle_attack_group_runtime.py','test_attack_group_runtime.py','test_portable_battle_attack_group.py','test_battle_native_route.py'])
SUITES['attack-group-native-route']=dict(SUITES['attack-group-battle'],script='research/verify-world-attack-group-native-route-short.py',golden='research/portable-world-attack-group-native-route-short-expected.json',inputs=53,native=42,development_only=False)
SUITES['attack-group-long']=dict(SUITES['attack-group-native-route'],script='research/verify-world-attack-group-long-short.py',golden='research/portable-world-attack-group-long-short-expected.json',inputs=60,native=48,development_only=False)
SUITES['attack-group-long']['tests']=[*SUITES['attack-group-native-route']['tests'],'test_long_group_history.py']
SUITES['attack-group-mixed']=dict(SUITES['attack-group-long'],script='research/verify-world-attack-group-mixed-short.py',golden='research/portable-world-attack-group-mixed-short-expected.json',inputs=81,native=68,development_only=False,tests=[*SUITES['attack-group-long']['tests'],'test_mixed_attack_groups.py'])
SUITES['attack-group-mixed']['tests']+=['test_impact_runtime.py','test_coordinate_skill_reference.py','test_portable_model_gap_audit.py','test_portable_coordinate_scene.py']
SUITES['leftmost-retention']=dict(SUITES['leftmost'],script='research/verify-world-leftmost-retention-short.py',golden='research/portable-world-leftmost-retention-short-expected.json',inputs=74,native=59,tests=SUITES['leftmost']['tests']+['test_portable_leftmost_replay.py','test_portable_duration_scaling_gpu.py','test_portable_gpu_replay.py','test_portable_reference_migration.py'])
SUITES['cache-preflight-regression']=dict(SUITES['duration-scaling'],tests=SUITES['duration-scaling']['tests']+['test_portable_cache_probe.py','test_portable_required_cache_preflight.py','test_portable_compile_cache.py','test_portable_cuda_artifact.py','test_portable_compile_cli.py','test_portable_generation_cache.py','test_portable_generation_request.py','test_portable_gpu_cli.py','test_portable_gpu_replay.py','test_portable_compiler_diagnostic.py'])
SUITES['squad-stage-rosters']=dict(SUITES['squad-stage'],script='research/verify-world-squad-stage-rosters-short.py',golden='research/portable-world-squad-stage-rosters-short-expected.json',inputs=7,native=7)
SUITES['scratch-layout']=dict(script='research/verify-scratch-layout-short.py',golden='research/portable-scratch-layout-short-expected.json',source='gpu/scratch_layout_probe.slang',inputs=8,native=6,development_only=False,tests=['test_portable_scratch_layout.py','test_portable_scratch_layout_migration.py','test_portable_generation_request.py'])
SUITES['ordered-history']=dict(script='research/verify-ordered-history-short.py',golden='research/portable-ordered-history-shared-sha-short-expected.json',source='gpu/ordered_history_probe.slang',inputs=13,native=10,development_only=False,tests=['test_portable_ordered_history.py','test_portable_generation_request.py'])
SUITES['late-attack-random']['tests']+=['test_portable_ordered_history.py','test_portable_generation_request.py']
SUITES['state-focus-rosters']['tests']=list(SUITES['late-attack-random']['tests'])
SUITES['ordered-history-battles']=dict(SUITES['state-focus-rosters'],script='research/verify-world-ordered-history-battles-short.py',golden='research/portable-world-ordered-history-battles-short-expected.json',inputs=25,native=17,tests=SUITES['state-focus-rosters']['tests']+['test_portable_ally_random_gpu.py','test_portable_eager_cover_migration.py','test_portable_query_diagnostic.py','test_portable_scratch_layout.py'],support_files=['research/portable-world-ally-random-short-expected.json'])
SUITES['native-query-diagnostic']=dict(SUITES['ordered-history-battles'],script='research/verify-world-native-query-diagnostic-short.py',source='gpu/world_native_query_diagnostic_entry.slang',golden='research/portable-native-query-diagnostic-short-expected.json',inputs=1,native=1,tests=SUITES['ordered-history-battles']['tests'])
SUITES['native-query-window']=dict(SUITES['native-query-diagnostic'],source='gpu/world_native_query_window_entry.slang')
SUITES['ally-random-diagnostic']=dict(SUITES['ally-random-gpu'],source='gpu/world_accuracy_admission_entry.slang')
SUITES['undying-predicate-rosters']=dict(SUITES['undying-predicate'],script='research/verify-world-undying-predicate-rosters-short.py',golden='research/portable-world-undying-predicate-rosters-short-expected.json',inputs=3,native=3)
SUITES['manual-swap-rosters']=dict(SUITES['manual-swap'],script='research/verify-world-manual-swap-rosters-short.py',golden='research/portable-world-manual-swap-rosters-short-expected.json',inputs=2,native=2)
SUITES['ammo-equivalent-rosters-diagnostic']=dict(SUITES['ammo-equivalent-rosters'],source='gpu/world_skill_hp_basis_admission_entry.slang',development_only=True)
SUITES['lost-hp-attack-revival']=dict(SUITES['lost-hp-attack'],script='research/verify-world-lost-hp-attack-revival-short.py',golden='research/portable-world-lost-hp-attack-revival-short-expected.json',inputs=3,native=3)
SUITES['lost-hp-attack-rosters']=dict(SUITES['lost-hp-attack'],script='research/verify-world-lost-hp-attack-rosters-short.py',golden='research/portable-world-lost-hp-attack-rosters-short-expected.json',inputs=2,native=2,tests=['test_portable_lost_hp_attack.py','test_portable_definition_view.py','test_portable_real_binding_proof.py'])
SUITES['skill-hp-basis']=dict(script='research/verify-world-skill-hp-basis-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-skill-hp-basis-short-expected.json',inputs=37,native=26,development_only=False,tests=['test_portable_skill_hp_basis_reference.py','test_portable_skill_hp_basis.py','test_damage_basis_specs.py','test_portable_definition_view.py','test_portable_query_boundaries.py','test_portable_weapon_phases.py','test_portable_seal.py','test_portable_cpu_batch.py'])
SUITES['skill-hp-basis-rosters']=dict(SUITES['skill-hp-basis'],script='research/verify-world-skill-hp-basis-rosters-short.py',golden='research/portable-world-skill-hp-basis-rosters-short-expected.json',inputs=4,native=4,tests=['test_portable_skill_hp_basis.py','test_portable_definition_view.py','test_portable_real_binding_proof.py'])
SUITES['skill-hp-basis-rosters-diagnostic']=dict(SUITES['skill-hp-basis-rosters'],source='gpu/world_skill_hp_basis_admission_entry.slang',development_only=True)
SUITES['skill-hp-basis-protection']=dict(SUITES['skill-hp-basis'],script='research/verify-world-skill-hp-basis-protection-short.py',golden='research/portable-world-skill-hp-basis-protection-short-expected.json',inputs=4,native=4)
SUITES['mode-capacity']=dict(script='research/verify-world-mode-capacity-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-mode-capacity-short-expected.json',inputs=32,native=26,development_only=False,tests=['test_portable_mode_capacity_reference.py','test_portable_mode_capacity.py','test_portable_definition_view.py','test_portable_weapon_phases.py','test_portable_references.py','test_portable_combat.py','test_portable_seal.py','test_portable_query_boundaries.py'])
SUITES['mode-capacity-instant']=dict(SUITES['mode-capacity'],script='research/verify-world-mode-capacity-instant-short.py',golden='research/portable-world-mode-capacity-instant-short-expected.json',inputs=3,native=3)
SUITES['mode-capacity-rosters']=dict(script='research/verify-world-mode-capacity-rosters-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-mode-capacity-rosters-short-expected.json',inputs=2,native=2,development_only=False,tests=['test_portable_mode_capacity_reference.py','test_portable_mode_capacity.py','test_portable_definition_view.py','test_portable_real_binding_proof.py'])
SUITES['ally-burst']=dict(script='research/verify-world-ally-burst-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-ally-burst-short-expected.json',inputs=16,native=15,development_only=False,tests=['test_portable_ally_burst.py','test_portable_definition_view.py','test_portable_burst_recipients.py'])
SUITES['ally-burst-rosters']=dict(script='research/verify-world-ally-burst-rosters-short.py',source='gpu/world_entry_reload_resident_entry.slang',golden='research/portable-world-ally-burst-rosters-short-expected.json',inputs=2,native=2,development_only=False,tests=['test_portable_ally_burst.py','test_portable_definition_view.py','test_portable_real_binding_proof.py'])
SUITES['parts-skill-world']=dict(script='research/verify-world-parts-skill-short.py',source='gpu/world_entry_reload_resident_entry.slang',
    golden='research/portable-world-parts-skill-short-expected.json',inputs=63,native=59,development_only=False,
    tests=['test_portable_physical_interrupt.py','test_portable_parts_skill_gpu.py','test_portable_parts_skill_reference.py','test_portable_parts_skill_extra_reference.py','test_portable_parts_skill_lifecycle_reference.py','test_portable_damage_factors.py','test_portable_resident_layout.py','test_portable_reference_migration.py','test_portable_gpu_replay.py','test_portable_interrupt_sources.py','test_portable_actor_pool_input.py','test_portable_actor_registry_input.py','test_impact_runtime.py'])
SUITES['interrupt-packet-codec']=dict(script='research/verify-interrupt-packet-codec-short.py',source='gpu/interrupt_packet_codec_probe.slang',
    golden='research/portable-interrupt-packet-codec-short-expected.json',inputs=154,native=140,development_only=False,
    tests=['test_portable_interrupt_packet_codec.py'])
SUITES['coordinate-math']=dict(script='research/verify-coordinate-math-short.py',source='gpu/coordinate_math_probe.slang',golden='research/portable-coordinate-math-short-expected.json',inputs=1026,native=1024,output_words=8,development_only=False,tests=['test_coordinate_math.py'])
SUITES['coordinate-shape']=dict(script='research/verify-coordinate-shape-short.py',source='gpu/coordinate_shape_probe.slang',golden='research/portable-coordinate-shape-short-expected.json',inputs=158,native=150,output_words=8,development_only=False,tests=['test_coordinate_math.py','test_coordinate_shape.py'])
SUITES['coordinate-scene']=dict(script='research/verify-coordinate-scene-short.py',source='gpu/coordinate_scene_probe.slang',golden='research/portable-coordinate-scene-short-expected.json',inputs=21,native=10,output_words=32768,development_only=False,tests=['test_portable_coordinate_scene.py','test_coordinate_skill_reference.py','test_impact_runtime.py'])
SUITES['coordinate-world-pool']=dict(script='research/verify-coordinate-world-pool-short.py',source='gpu/world_coordinate_pool_entry.slang',golden='research/portable-coordinate-world-pool-short-expected.json',inputs=16,native=11,output_words=1048576,development_only=False,tests=['test_portable_coordinate_scene.py','test_coordinate_skill_reference.py','test_impact_runtime.py','test_coordinate_world_pool.py'])
SUITES['coordinate-skills']=dict(script='research/verify-coordinate-skill-short.py',source='gpu/world_coordinate_skill_entry.slang',golden='research/portable-coordinate-skill-short-expected.json',inputs=24,native=19,output_words=1048576,development_only=False,tests=['test_coordinate_packets.py','test_coordinate_skill_reference.py','test_impact_runtime.py','test_coordinate_world_pool.py','test_portable_coordinate_scene.py'])
SUITES['coordinate-dot']=dict(SUITES['coordinate-skills'],script='research/verify-coordinate-dot-short.py',golden='research/portable-coordinate-dot-short-expected.json',inputs=35,native=28,development_only=False,tests=[*SUITES['coordinate-skills']['tests'],'test_coordinate_dot.py'])
SUITES['coordinate-area']=dict(SUITES['coordinate-dot'],script='research/verify-coordinate-area-short.py',source='gpu/world_coordinate_area_entry.slang',golden='research/portable-coordinate-area-short-expected.json',inputs=52,native=42,development_only=False,tests=[*SUITES['coordinate-dot']['tests'],'test_coordinate_math.py','test_coordinate_area.py'])
SUITES['coordinate-pending']=dict(SUITES['coordinate-area'],script='research/verify-coordinate-pending-short.py',source='gpu/world_coordinate_pending_entry.slang',golden='research/portable-coordinate-pending-short-expected.json',inputs=60,native=50,development_only=False,tests=[*SUITES['coordinate-area']['tests'],'test_coordinate_pending.py'])
SUITES['coordinate-full-burst']=dict(SUITES['coordinate-pending'],script='research/verify-coordinate-full-burst-short.py',source='gpu/world_coordinate_full_burst_entry.slang',golden='research/portable-coordinate-full-burst-short-expected.json',inputs=76,native=63,development_only=False,tests=[*SUITES['coordinate-pending']['tests'],'test_coordinate_full_burst.py'])
SUITES['coordinate-generation']=dict(SUITES['coordinate-full-burst'],script='research/verify-coordinate-generation-short.py',golden='research/portable-coordinate-generation-short-expected.json',inputs=88,native=75,development_only=False,tests=[*SUITES['coordinate-full-burst']['tests'],'test_coordinate_generation.py'])
SUITES['coordinate-composed']=dict(SUITES['coordinate-generation'],script='research/verify-coordinate-composed-short.py',source='gpu/world_coordinate_composed_entry.slang',golden='research/portable-coordinate-composed-short-expected.json',inputs=97,native=81,output_words=1310720,development_only=False,upstream_documents=['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'],tests=[*SUITES['coordinate-generation']['tests'],'test_coordinate_composed.py','test_coordinate_physical_reference.py','test_coordinate_physical_frontier.py'])
SUITES['coordinate-arcs']=dict(script='research/verify-coordinate-arcs-short.py',source='gpu/coordinate_arc_probe.slang',golden='research/portable-coordinate-arcs-short-expected.json',inputs=135,native=126,output_words=4100,development_only=False,upstream_documents=['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'],tests=['test_coordinate_arcs.py','test_coordinate_physical_frontier.py'])
SUITES['coordinate-composed']['support_files']=[*SUITES['coordinate-generation'].get('support_files',[]),'research/portable-coordinate-arcs-short-expected.json']
SUITES['coordinate-arc-scalar']=dict(script='research/verify-coordinate-arc-scalar-short.py',source='gpu/coordinate_arc_scalar_probe.slang',golden='research/portable-coordinate-arc-scalar-short-expected.json',inputs=640,native=632,output_words=4104,development_only=False,tests=['test_coordinate_arc_scalar.py','test_portable_model_gap_audit.py','test_coordinate_physical_frontier.py'],upstream_documents=['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'],support_files=['research/portable-coordinate-arcs-short-expected.json'])
SUITES['coordinate-numeric']=dict(script='research/verify-coordinate-numeric-short.py',source='gpu/coordinate_numeric_probe.slang',golden='research/portable-coordinate-numeric-short-expected.json',inputs=2783,native=2771,output_words=16,development_only=False,tests=['test_coordinate_numeric_v1.py'])
SUITES['coordinate-geometry']=dict(script='research/verify-coordinate-geometry-short.py',source='gpu/coordinate_geometry_probe.slang',golden='research/portable-coordinate-geometry-short-expected.json',inputs=1224,native=1209,output_words=4160,development_only=False,tests=['test_coordinate_geometry_v1.py','test_coordinate_numeric_v1.py'])
SUITES['coordinate-power']=dict(script='research/verify-coordinate-power-short.py',source='gpu/coordinate_power_probe.slang',golden='research/portable-coordinate-power-short-expected.json',inputs=909,native=898,output_words=8,development_only=False,tests=['test_coordinate_power_v1.py','test_portable_numeric_design.py'])
SUITES['coordinate-landing']=dict(script='research/verify-coordinate-landing-short.py',source='gpu/coordinate_landing_probe.slang',golden='research/portable-coordinate-landing-short-expected.json',inputs=40,native=26,output_words=13796,development_only=False,tests=['test_coordinate_landing_v1.py','test_coordinate_power_v1.py','test_portable_numeric_design.py'])
SUITES['coordinate-landing']['tests'] += ['test_coordinate_physical_common.py', 'test_coordinate_physical_reference.py', 'test_coordinate_physical_frontier.py']
SUITES['coordinate-landing']['upstream_documents'] = ['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md']
SUITES['coordinate-landing']['support_files'] = ['research/portable-coordinate-arcs-short-expected.json']
SUITES['coordinate-physical']=dict(script='research/verify-coordinate-physical-short.py',source='gpu/world_coordinate_physical_entry.slang',golden='research/portable-coordinate-physical-short-expected.json',inputs=23,native=17,output_words=1310720,development_only=False,tests=['test_coordinate_physical_gpu.py','test_coordinate_physical_common.py','test_coordinate_physical_reference.py','test_portable_damage_factors.py'])
SUITES['coordinate-physical']['upstream_documents']=['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md']
SUITES['coordinate-physical']['support_files']=['research/portable-coordinate-arcs-short-expected.json']
SUITES['coordinate-physical']['tests'].append('test_coordinate_physical_frontier.py')
SUITES['packet-integer']=dict(script='research/verify-packet-integer-short.py',source='gpu/packet_integer_probe.slang',golden='research/portable-packet-integer-short-expected.json',inputs=305,native=294,output_words=8,development_only=False,tests=['test_packet_integer_sum.py','test_portable_numeric_design.py'])
SUITES['coordinate-quantity']=dict(SUITES['coordinate-physical'],script='research/verify-coordinate-quantity-short.py',golden='research/portable-coordinate-quantity-short-expected.json',inputs=31,native=25,development_only=False,tests=[*SUITES['coordinate-physical']['tests'],'test_packet_integer_sum.py','test_coordinate_quantity.py'])
SUITES['coordinate-quantity']['tests'].append('test_coordinate_accumulation_policy.py')
SUITES['coordinate-quantity']['support_files']=[*SUITES['coordinate-quantity']['support_files'],
    'research/portable-packet-integer-short-expected.json',
    'research/portable-compiler-full--coordinate-quantity-source-certificate.json']
SUITES['coordinate-accum-emission']=dict(SUITES['coordinate-quantity'],script='research/verify-coordinate-accum-emission-short.py',golden='research/portable-coordinate-accum-emission-short-expected.json',inputs=84,native=78,development_only=False,tests=[*SUITES['coordinate-quantity']['tests'],'test_coordinate_accum_emission.py','test_portable_damage_accum_battle.py','test_portable_damage_accum_core.py'])
SUITES['coordinate-accum-emission']['support_files']=[*SUITES['coordinate-quantity']['support_files'],'research/portable-coordinate-quantity-short-expected.json','research/portable-compiler-full--coordinate-accum-emission-source-certificate.json']
SUITES['coordinate-core']=dict(SUITES['coordinate-accum-emission'],script='research/verify-coordinate-core-short.py',source='gpu/world_coordinate_core_entry.slang',golden='research/portable-coordinate-core-short-expected.json',inputs=120,native=106,development_only=False,tests=[*SUITES['coordinate-accum-emission']['tests'],'test_coordinate_core.py'])
SUITES['coordinate-core']['support_files']=[*SUITES['coordinate-accum-emission']['support_files'],'research/portable-coordinate-accum-emission-short-expected.json','research/portable-compiler-full--coordinate-core-source-certificate.json']
SUITES['skill-part-codec']=dict(script='research/verify-skill-part-codec-short.py',source='gpu/skill_part_codec_probe.slang',
    golden='research/portable-skill-part-codec-short-expected.json',inputs=4,native=3,development_only=False,
    tests=['test_portable_skill_part_codec.py'])
SUITES['heal-share-plan']=dict(script='research/verify-heal-share-plan-short.py',source='gpu/heal_share_plan_probe.slang',
    golden='research/portable-heal-share-plan-short-expected.json',inputs=10,native=8,development_only=False,
    tests=['test_portable_heal_share_plan.py'])
SUITES['heal-share-world']=dict(script='research/verify-world-heal-share-short.py',source='gpu/world_entry_reload_resident_entry.slang',
    golden='research/portable-world-heal-share-short-expected.json',inputs=53,native=43,development_only=True,
    tests=['test_portable_heal_share_gpu.py','test_portable_heal_share_plan.py','test_portable_resident_layout.py'])
SUITES['heal-share-diagnostic']=dict(SUITES['heal-share-world'],script='research/verify-world-heal-share-diagnostic-short.py',source='gpu/world_heal_share_diagnostic_entry.slang',
    golden='research/portable-world-heal-share-diagnostic-short-expected.json',development_only=False,tests=SUITES['heal-share-world']['tests']+['test_portable_heal_share_trace.py'])
SUITES['heal-share-regression']=dict(SUITES['entry-reload-regression'],script='research/verify-world-heal-share-regression-short.py',
    golden='research/portable-world-heal-share-regression-short-expected.json',inputs=849,native=676,development_only=False,
    tests=SUITES['entry-reload-regression']['tests']+['test_portable_heal_share_gpu.py','test_portable_heal_share_trace.py'])
SUITES['heal-share-regression']['tests'].append('test_portable_ally_burst.py')
for mode_capacity_test in ('test_portable_mode_capacity_reference.py','test_portable_mode_capacity.py','test_portable_seal.py'):
    if mode_capacity_test not in SUITES['heal-share-regression']['tests']:SUITES['heal-share-regression']['tests'].append(mode_capacity_test)
SUITES['heal-share-rosters']=dict(script='research/verify-world-heal-share-rosters-short.py',source='gpu/world_entry_reload_resident_entry.slang',
    golden='research/portable-world-heal-share-rosters-short-expected.json',inputs=4,native=4,development_only=False,
    tests=['test_portable_heal_share_gpu.py','test_portable_real_binding_proof.py','test_portable_linked_artifact.py'])
SUITES['skill-hp-basis-retention']=dict(SUITES['heal-share-regression'],script='research/verify-world-skill-hp-basis-retention-short.py',golden='research/portable-world-skill-hp-basis-retention-short-expected.json',inputs=971,native=787,development_only=False,tests=list(dict.fromkeys(SUITES['heal-share-regression']['tests']+['test_portable_skill_hp_basis_retention.py','test_portable_skill_hp_basis.py','test_portable_physical_interrupt.py','test_portable_query_boundaries.py'])))
SUITES['skill-hp-basis-retention']['cpu_test_timeout']=90
SUITES['skill-hp-basis-retention']['support_files']=[SUITES[name]['golden'] for name in ('heal-share-regression','parts-skill-world','heal-share-rosters','ally-burst','ally-burst-rosters','mode-capacity','mode-capacity-instant','mode-capacity-rosters')]
SUITES['lost-hp-attack-retention']=dict(SUITES['skill-hp-basis-retention'],script='research/verify-world-lost-hp-attack-retention-short.py',golden='research/portable-world-lost-hp-attack-retention-short-expected.json',inputs=1016,native=821,development_only=False,tests=list(dict.fromkeys(SUITES['skill-hp-basis-retention']['tests']+['test_portable_lost_hp_attack_reference.py','test_portable_lost_hp_attack.py','test_portable_lost_hp_attack_retention.py'])))
SUITES['lost-hp-attack-retention']['support_files']=list(dict.fromkeys(SUITES['skill-hp-basis-retention']['support_files']+[SUITES[name]['golden'] for name in ('skill-hp-basis-retention','skill-hp-basis','skill-hp-basis-protection','skill-hp-basis-rosters')]))
SUITES['pellet-shot-rosters']=dict(SUITES['pellet-shot'],script='research/verify-world-pellet-shot-rosters-short.py',golden='research/portable-world-pellet-shot-rosters-short-expected.json',inputs=2,native=2,tests=['test_portable_pellet_shot.py','test_portable_definition_view.py','test_portable_real_binding_proof.py'])
SUITES['pellet-shot-retention']=dict(SUITES['lost-hp-attack-retention'],script='research/verify-world-pellet-shot-retention-short.py',golden='research/portable-world-pellet-shot-retention-short-expected.json',inputs=1050,native=847,development_only=False,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['lost-hp-attack-retention']['tests']+['test_portable_pellet_shot_reference.py','test_portable_pellet_shot.py','test_portable_pellet_shot_retention.py'])))
SUITES['pellet-shot-retention']['support_files']=list(dict.fromkeys(SUITES['lost-hp-attack-retention']['support_files']+[SUITES[name]['golden'] for name in ('lost-hp-attack-retention','lost-hp-attack','lost-hp-attack-revival','lost-hp-attack-rosters')]))
SUITES['ammo-equivalent-retention']=dict(SUITES['pellet-shot-retention'],script='research/verify-world-ammo-equivalent-retention-short.py',golden='research/portable-world-ammo-equivalent-retention-short-expected.json',inputs=1088,native=870,development_only=False,cpu_test_timeout=120,tests=list(dict.fromkeys(SUITES['pellet-shot-retention']['tests']+['test_portable_manual_swap_reference.py','test_portable_ammo_equivalent_reference.py','test_portable_ammo_equivalent.py','test_portable_ammo_equivalent_retention.py','test_portable_readiness_semantics.py'])))
SUITES['ammo-equivalent-retention']['support_files']=list(dict.fromkeys(SUITES['pellet-shot-retention']['support_files']+[SUITES[name]['golden'] for name in ('pellet-shot-retention','pellet-shot','pellet-shot-rosters')]))
SUITES['manual-swap-retention']=dict(SUITES['ammo-equivalent-retention'],script='research/verify-world-manual-swap-retention-short.py',golden='research/portable-world-manual-swap-retention-short-expected.json',inputs=1137,native=902,development_only=False,parent_oracle_reuse=True,tests=list(dict.fromkeys(SUITES['ammo-equivalent-retention']['tests']+['test_portable_accuracy_predicate_reference.py','test_portable_parent_oracles.py','test_portable_manual_swap.py','test_portable_manual_swap_retention.py'])))
SUITES['manual-swap-retention']['support_files']=list(dict.fromkeys(SUITES['ammo-equivalent-retention']['support_files']+[SUITES[name]['golden'] for name in ('ammo-equivalent-retention','ammo-equivalent','ammo-equivalent-rosters','ammo-equivalent-catalogue')]))
SUITES['accuracy-predicate-retention']=dict(SUITES['manual-swap-retention'],script='research/verify-world-accuracy-predicate-retention-short.py',golden='research/portable-world-accuracy-predicate-retention-short-expected.json',inputs=1169,native=927,development_only=False,cpu_test_timeout=180,tests=list(dict.fromkeys(SUITES['manual-swap-retention']['tests']+['test_portable_accuracy_predicate.py','test_portable_accuracy_predicate_retention.py','test_portable_sparse_raw.py'])))
SUITES['accuracy-predicate-retention']['support_files']=list(dict.fromkeys(SUITES['manual-swap-retention']['support_files']+[SUITES[name]['golden'] for name in ('manual-swap-retention','manual-swap','manual-swap-rosters')]))
SUITES['undying-predicate-retention']=dict(SUITES['accuracy-predicate-retention'],script='research/verify-world-undying-predicate-retention-short.py',golden='research/portable-world-undying-predicate-retention-short-expected.json',inputs=1203,native=955,development_only=False,cpu_test_timeout=180,tests=list(dict.fromkeys(SUITES['accuracy-predicate-retention']['tests']+['test_portable_undying_predicate_reference.py','test_portable_undying_predicate.py','test_portable_undying_predicate_retention.py','test_portable_state_predicate_reference.py','test_portable_ally_random_reference.py','test_portable_state_work_routing.py'])))
SUITES['undying-predicate-retention']['support_files']=list(dict.fromkeys(SUITES['accuracy-predicate-retention']['support_files']+[SUITES[name]['golden'] for name in ('accuracy-predicate-retention','accuracy-predicate','accuracy-predicate-rosters')]))
SUITES['ally-random-retention']=dict(SUITES['undying-predicate-retention'],script='research/verify-world-ally-random-retention-short.py',golden='research/portable-world-ally-random-retention-short-expected.json',inputs=1234,native=980,development_only=True,tests=SUITES['undying-predicate-retention']['tests']+['test_portable_ally_random_gpu.py','test_portable_ally_random_retention.py'])
SUITES['ally-random-retention']['support_files']=list(dict.fromkeys(SUITES['undying-predicate-retention']['support_files']+[SUITES[name]['golden'] for name in ('undying-predicate-retention','undying-predicate','undying-predicate-rosters')]))
SUITES['state-focus-retention']=dict(SUITES['ally-random-retention'],script='research/verify-world-state-focus-retention-short.py',golden='research/portable-world-state-focus-retention-short-expected.json',inputs=1264,native=1000,development_only=True,tests=SUITES['ally-random-retention']['tests']+['test_portable_state_focus.py','test_portable_state_focus_retention.py'])
SUITES['state-focus-retention']['support_files']=list(dict.fromkeys(SUITES['ally-random-retention']['support_files']+[SUITES[name]['golden'] for name in ('ally-random-retention','ally-random-gpu')]))
SUITES['ordered-history-retention']=dict(SUITES['state-focus-retention'],script='research/verify-world-ordered-history-retention-short.py',golden='research/portable-world-ordered-history-retention-short-expected.json',inputs=1355,native=1071,tests=list(dict.fromkeys(SUITES['state-focus-retention']['tests']+SUITES['ordered-history-battles']['tests']+['test_portable_eager_cover_migration.py'])))
SUITES['interrupt-aim-retention']=dict(SUITES['ordered-history-retention'],script='research/verify-world-interrupt-aim-retention-short.py',golden='research/portable-world-interrupt-aim-retention-short-expected.json',inputs=1385,native=1101,development_only=True,tests=list(dict.fromkeys(SUITES['ordered-history-retention']['tests']+SUITES['interrupt-aim']['tests']+SUITES['mixed-query']['tests'])))
SUITES['interrupt-aim-retention']['support_files']=list(dict.fromkeys(SUITES['ordered-history-retention']['support_files']+['research/portable-interrupt-aim-rejection-stage.json']))
SUITES['aimed-factors-retention']=dict(SUITES['interrupt-aim-retention'],script='research/verify-world-aimed-factor-retention-short.py',golden='research/portable-world-aimed-factor-retention-short-expected.json',inputs=1393,native=1109,development_only=True)
SUITES['aimed-area-retention']=dict(SUITES['aimed-factors-retention'],script='research/verify-world-aimed-area-retention-short.py',golden='research/portable-world-aimed-area-retention-short-expected.json',inputs=1405,native=1121,development_only=True)
SUITES['squad-stage-retention']=dict(SUITES['aimed-area-retention'],script='research/verify-world-squad-stage-retention-short.py',golden='research/portable-world-squad-stage-retention-short-expected.json',inputs=1442,native=1144,development_only=True)
SUITES['partial-charge-retention']=dict(SUITES['squad-stage-retention'],source='gpu/world_partial_charge_entry.slang',script='research/verify-world-partial-charge-retention-short.py',golden='research/portable-world-partial-charge-retention-short-expected.json',inputs=1516,native=1192,development_only=True)
SUITES['partial-query-retention']=dict(SUITES['partial-charge-retention'],script='research/verify-world-partial-query-retention-short.py',golden='research/portable-world-partial-query-retention-short-expected.json',inputs=1533,native=1209)
SUITES['not-core-retention']=dict(SUITES['partial-query-retention'],source='gpu/world_not_core_entry.slang',script='research/verify-world-not-core-retention-short.py',golden='research/portable-world-not-core-retention-short-expected.json',inputs=1565,native=1236)
SUITES['duration-scaling-retention']=dict(SUITES['not-core-retention'],source='gpu/world_duration_scaling_entry.slang',script='research/verify-world-duration-scaling-retention-short.py',golden='research/portable-world-duration-scaling-retention-short-expected.json',inputs=1612,native=1276)
SUITES['compiler-commands']=dict(script=None,source='gpu/compiler_commands_entry.slang',
    golden='research/portable-compiler-commands-heal-share-source-certificate.json',inputs=0,native=0,compiler_only=True,
    support_files=['research/portable-world-heal-share-regression-short-expected.json'],
    tests=['test_portable_compile_cli.py','test_portable_compile_cache.py','test_portable_generation_cache.py','test_portable_offline_assembly.py','test_portable_phase_codegen.py','test_portable_compiler_diagnostic.py','test_portable_ptx_stats.py','test_portable_ptx_callgraph.py','test_portable_ptx_partition.py','test_portable_partition_object.py','test_portable_module_object.py','test_portable_device_linker.py','test_portable_native_process.py','test_portable_job_limits.py','test_portable_native_output_probe.py','test_portable_jit_link.py','test_portable_jit_link_capture.py','test_portable_linked_artifact.py'])

SUITES['compiler-full']=dict(SUITES['compiler-commands'],
    source=SUITES['heal-share-regression']['source'],
    golden='research/portable-compiler-full-heal-share-source-certificate.json')

# These scoped source baselines have explicit independent Metal seals.
# Sealed package eligibility is scoped proof, not UI or full-catalog admission.
for _sealed_suite in ('max-ammo-scaling','max-ammo-scaling-retention','max-ammo-scaling-rosters','heal-charge-lifetime','heal-charge-lifetime-retention','heal-charge-rosters','damage-accum-battle','damage-accum-retention','damage-accum-rosters'):
    SUITES[_sealed_suite]['development_only']=False

# Full-source diagnostics are derived from registered full-world battle suites.
# Registry choices, rather than mutable certificate fields, select full vs commands.
from portable_compiler_certificate import alias as compiler_alias
for _baseline,_config in list(SUITES.items()):
    if _config.get('compiler_only') or not _config.get('script') or not _config['source'].startswith('gpu/world_') or not _config['source'].endswith('_entry.slang'):continue
    SUITES[compiler_alias(_baseline)]=dict(SUITES['compiler-full'],source=_config['source'],
        golden='research/portable-'+compiler_alias(_baseline)+'-source-certificate.json',
        support_files=[_config['golden']],compiler_baseline_suite=_baseline,
        tests=SUITES['compiler-full']['tests']+['test_portable_compiler_certificate.py','test_portable_seal.py'])

# Controller validation has no numeric program to execute. Keep its CPU work
# separate from a selected suite's battle/native preflight.
SMOKE_TESTS = ['test_portable_windows_cleanup.py','test_portable_gpu_cli.py',
               'test_portable_compile_cache.py','test_portable_cuda_artifact.py','test_portable_module_check.py','test_portable_weapon_phases.py','test_portable_offline_assembly.py','test_portable_readback_stream.py','test_portable_regression_compact.py','test_portable_file_transport.py','test_portable_cpu_batch.py','test_portable_query_boundaries.py','test_portable_ptx_stats.py','test_portable_compiler_diagnostic.py']
SMOKE_TESTS.append('test_portable_compiler_certificate.py')
SMOKE_TESTS.append('test_portable_generation_cache.py')
SMOKE_TESTS.append('test_portable_metal_cache.py')
SMOKE_TESTS.append('test_portable_generation_separation.py')
SMOKE_TESTS.append('test_portable_definition_view.py')
SMOKE_TESTS.append('test_portable_ptx_callgraph.py')
SMOKE_TESTS.append('test_portable_ptx_partition.py')
SMOKE_TESTS.append('test_portable_partition_object.py')
SMOKE_TESTS.append('test_portable_module_object.py')
SMOKE_TESTS.append('test_portable_object_recovery.py')
SMOKE_TESTS.append('test_portable_device_linker.py')
SMOKE_TESTS.append('test_portable_native_process.py')
SMOKE_TESTS.append('test_portable_job_limits.py')
SMOKE_TESTS.append('test_portable_native_output_probe.py')
SMOKE_TESTS.append('test_portable_jit_link.py')
SMOKE_TESTS.append('test_portable_jit_link_capture.py')
SMOKE_TESTS.append('test_portable_linked_artifact.py')
SMOKE_TESTS.append('test_portable_packet_stage.py')
SMOKE_TESTS.append('test_portable_generation_gate.py')
SMOKE_TESTS.append('test_portable_readback_blocks.py')
SMOKE_TESTS.append('test_portable_sparse_raw.py')
SMOKE_TESTS.append('test_portable_scope_snapshot_audit.py')
SMOKE_TESTS.append('test_portable_authored_case_purity.py')
SMOKE_TESTS.append('test_portable_prepared_input.py')
SMOKE_TESTS.append('test_portable_arena_specs.py')
SMOKE_TESTS.append('test_portable_package_projection.py')
SMOKE_TESTS.append('test_portable_storage_budget.py')
SUITES['destructible-counter']['tests'].append('test_portable_prepared_input.py')
SUITES['destructible-counter']['tests'].append('test_portable_packet_stage.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    """Atomic durable publication, including failures and partial-run status."""
    path = Path(path)
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


def safe_name(name):
    p = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('Unsafe artifact path')
    return name


def file_records(root, names):
    records = []
    for name in sorted(names):
        safe_name(name)
        p = root/name
        try:info=p.lstat()
        except OSError as error:raise ValueError('Expected regular artifact: '+name) from error
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Expected regular artifact: '+name)
        from portable_capture_storage import file_digest
        records.append(dict(path=name, bytes=info.st_size, sha256=file_digest(p)))
    return records


def check_records(root, records):
    names = [safe_name(r['path']) for r in records]
    if len(names) != len(set(names)) or file_records(root, names) != sorted(records, key=lambda r:r['path']):
        raise ValueError('Artifact bytes/SHA/size mismatch')


def capture_status(capture):
    """Display saved progress without inferring process liveness or success."""
    observations={}
    summarize=module(ROOT/'research/portable_phase_audit.py').summarize
    for name in ('phases.jsonl','audit-phases.jsonl','preparation.jsonl'):
        path=capture/name
        if path.exists():
            summary=summarize(path)
            observations[name]=dict(events=summary['events'],last_event=summary['last_event'],timed_calls=summary['timed_calls'],timing_scope=summary['timing_scope'])
    run=capture/('run.json' if (capture/'run.json').exists() else 'recipe.json')
    result=capture/('result.json' if (capture/'result.json').exists() else 'stage-result.json')
    return dict(run=load(run),result=load(result) if result.exists() else None,
                observations=observations,liveness_verified=False,journal_integrity_verified=False,
                scope='Saved journal observations only; entered/returned events do not establish current liveness or calculation success')


def package_id(manifest):
    body = {k:v for k,v in manifest.items() if k != 'package_id'}
    return sha(json.dumps(body, sort_keys=True, separators=(',', ':')).encode())


def historical_compiler_layout(root,m):
    """Resolve old certificate/baseline from hash-checked immutable records.

    Never use the latest suite's file names to reinterpret a saved producer.
    This only admits compiler-source-only packages, not historical battle runs.
    """
    if not compiler_only(m) or m.get('purpose')!='compiler-diagnostic':
        raise ValueError('Historical producer must be a compiler-source-only package')
    golden=m['golden'];records=m['files']
    candidates=[r['path'] for r in records if r['path'].startswith('research/') and r['path'].endswith('.json')]
    certificates=[name for name in candidates if load(root/name)==golden]
    baselines=[r['path'] for r in records if r['path'] in candidates and r['sha256']==golden.get('baseline_golden_sha256')]
    if len(certificates)!=1:raise ValueError('Historical compiler certificate must have one immutable owner')
    if len(baselines)!=1:raise ValueError('Compiler shared baseline absent or ambiguous in historical payload')
    return certificates[0],baselines[0]


def compiler_baseline_sources(m):
    sources=m['golden']['source_sha256']
    # A full entry is already in the Metal baseline; commands adds one wrapper.
    # Choose by registered suite, never by a mutable certificate field.
    if full_compiler(m):return sources
    return {k:v for k,v in sources.items() if k!=SUITES[m['suite']]['source']}


def verify_package(root,*,historical_compiler=False):
    m = load(root/'gpu-package.json')
    if m['schema'] != SCHEMA or m['package_id'] != package_id(m) or m['suite'] not in SUITES:
        raise ValueError('Invalid package identity/schema/suite')
    if m.get('purpose','sealed') not in ('sealed','development','compiler-diagnostic') or (not is_development(m) and m.get('selected_cases')):
        raise ValueError('Invalid package purpose/case selection')
    if compiler_only(m)!=(m.get('purpose')=='compiler-diagnostic'):raise ValueError('Compiler diagnostic purpose mismatch')
    check_records(root, m['files'])
    historical_layout=historical_compiler_layout(root,m) if historical_compiler else None
    golden = m['golden'] if is_development(m) else load(root/(historical_layout[0] if historical_layout else SUITES[m['suite']]['golden']))
    if golden != m['golden']:
        raise ValueError('Package golden mismatch')
    if compiler_only(m):
        if golden.get('proof_kind')!='compiler-source-only' or golden.get('calculation_verified') is not False or golden.get('executable_battle_verified') is not False or golden.get('entries')!=[]:
            raise ValueError('Compiler diagnostic cannot claim a battle proof')
        if not historical_layout and not set(SUITES[m['suite']]['support_files'])<={r['path'] for r in m['files']}:raise ValueError('Compiler shared baseline absent from payload')
        declared=SUITES[m['suite']].get('compiler_baseline_suite')
        if declared is not None and golden.get('baseline_suite')!=declared:raise ValueError('Compiler baseline suite mismatch')
        baseline_path=root/(historical_layout[1] if historical_layout else SUITES[m['suite']]['support_files'][0])
        baseline=load(baseline_path)
        if sha(baseline_path.read_bytes())!=golden['baseline_golden_sha256'] or compiler_baseline_sources(m)!=baseline['source_sha256'] or (full_compiler(m) and golden['generated_normalized']!=baseline['generated_normalized']):
            raise ValueError('Compiler diagnostic changed the shared baseline')
    sources=golden['source_sha256'];records={r['path']:r['sha256'] for r in m['files']}
    if not sources or SUITES[m['suite']]['source'] not in sources:raise ValueError('Package GPU source closure missing')
    missing=set(sources)-set(records)
    if missing:raise ValueError('GPU source missing from immutable payload: '+', '.join(sorted(missing)))
    if any(records[name]!=digest for name,digest in sources.items()):raise ValueError('GPU source record differs from golden')
    if 'payload_projection' in m:
        from portable_package_projection import validate
        validate(m['payload_projection'],m['files'],m['suite'],SUITES[m['suite']],SMOKE_TESTS)
    return m


def make_package(suite, output, *, develop=False, cases=(), compact=False):
    """Whitelist code + required public data; never reports/raw/settings/tools."""
    if SUITES[suite].get('compiler_only') and (develop or cases):raise ValueError('Compiler diagnostic has no battle development/cases')
    if SUITES[suite].get('development_only') and not develop:
        raise ValueError('This suite requires --develop until an explicit Metal seal is registered')
    if compact:
        from portable_package_projection import SUPPORTED_SUITES
        if suite not in SUPPORTED_SUITES:raise ValueError('Compact profile not validated for this suite')
    tracked = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0')
    names = []
    for name in filter(None, tracked):
        p = PurePosixPath(name)
        if ((p.parts[0] in ('app','gpu','scripts','research','tests') and p.suffix in ('.py','.slang','.swift'))
            or (p.parts[0]=='app' and p.suffix=='.cu')
            or (p.parts[:2]==('tests','fixtures') and p.suffix=='.json')
            or name=='research/portable-mode-session-contract.json'
            or name=='research/portable-world-counter-landing-short-expected.json'
            # Shared controller tests bind the full-entry certificate to this Metal baseline.
            or name in ('research/portable-compiler-full-heal-share-source-certificate.json','research/portable-world-heal-share-regression-short-expected.json','research/portable-compiler-full--attack-group-long-source-certificate.json','research/portable-world-attack-group-long-short-expected.json','research/portable-compiler-full--attack-group-mixed-source-certificate.json','research/portable-world-attack-group-mixed-short-expected.json')
            or (p.parts[0]=='data' and p.suffix=='.json') or name==SUITES[suite]['golden'] or name in SUITES[suite].get('support_files',())):
            names.append(name)
    # Declared public pinned documents are data inputs to source audits.
    # They are frozen and licensed with the same upstream snapshot as Python.
    for name in SUITES[suite].get('upstream_documents',()):
        p=PurePosixPath(safe_name(name));path=ROOT/name
        if p.parts[:4]!=('research','upstream','nikke-calc-master','docs') or p.suffix!='.md' or not path.is_file() or path.is_symlink():
            raise ValueError('Invalid upstream audit document: '+name)
        if name not in names:names.append(name)
    # Include this CLI even before its first commit during local development.
    if 'scripts/nikke_gpu.py' not in names:
        names.append('scripts/nikke_gpu.py')
    for pattern in SUITES[suite]['tests']:
        if 'tests/'+pattern not in names:
            raise ValueError('Required CPU test is missing from tracked payload: '+pattern)
    required=[*SUITES[suite].get('support_files',())]
    if not SUITES[suite].get('compiler_only') and SUITES[suite].get('script'):
        required.append(SUITES[suite]['script'])
    missing_required=set(required)-set(names)
    if missing_required:raise ValueError('Declared suite file missing from tracked payload: '+', '.join(sorted(missing_required)))
    from portable_backend import source_hashes
    gpu_sources=source_hashes(SUITES[suite]['source'])
    missing=set(gpu_sources)-set(names)
    if missing:raise ValueError('GPU source missing from tracked payload: '+', '.join(sorted(missing)))
    upstream = ROOT/'research/upstream/nikke-calc-master'
    for folder in ('calculator','runner','scraper','data'):
        names.extend(p.relative_to(ROOT).as_posix() for p in (upstream/folder).rglob('*')
                     if p.is_file() and not p.is_symlink() and p.suffix in ('.py','.json'))
    license_path = upstream/'LICENSE'
    if not license_path.is_file() or not (upstream/'data/parsed_nikke.json').is_file():
        raise ValueError('Pinned upstream source/data must be installed first')
    names.append(license_path.relative_to(ROOT).as_posix())
    contract_name='research/portable-mode-session-contract.json'
    if contract_name in names:
        contract=load(ROOT/contract_name)
        for key,digest in [('primary_source','primary_source_sha256'),('pinned_cpu_source','pinned_cpu_sha256')]:
            name=safe_name(contract[key])
            if not name.startswith('research/upstream/nikke-calc-master/'):raise ValueError('CPU contract source must remain in pinned upstream')
            if sha((ROOT/name).read_bytes())!=contract[digest]:raise ValueError('Pinned CPU contract source changed: '+name)
            if name not in names:names.append(name)
    from portable_cpu_tests import validate_dependency_files
    validate_dependency_files(ROOT,[*SUITES[suite]['tests'],*SMOKE_TESTS],included=set(names))
    records = file_records(ROOT, names)
    projection=None
    if compact:
        from portable_package_projection import project,roots_for
        selected,projection=project(ROOT,names,roots_for(SUITES[suite],SMOKE_TESTS),
                                    suite_tests={key:config['tests'] for key,config in SUITES.items()})
    if cases and not develop:
        raise ValueError('--case requires --develop')
    golden = development_baseline(suite, cases) if develop else load(ROOT/SUITES[suite]['golden'])
    if golden['source_sha256']!=gpu_sources:raise ValueError('Golden GPU source closure is stale')
    # Early stale-golden detection, without importing native engine or building.
    for name, digest in golden['source_sha256'].items():
        if sha((ROOT/name).read_bytes()) != digest:
            raise ValueError('Golden GPU source is stale: '+name)
    if file_records(ROOT,names)!=records:
        raise ValueError('Package sources changed during native baseline preparation')
    m = dict(schema=SCHEMA, suite=suite,
             source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             working_tree_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
             files=records, golden=golden, purpose='compiler-diagnostic' if SUITES[suite].get('compiler_only') else 'development' if develop else 'sealed', selected_cases=list(cases), runtime_requirements=['Python dependencies from the existing venv', 'Slang 2026.20', 'CUDA toolkit/driver on Windows or Swift/Metal on macOS'])
    if projection is not None:
        selected=set(selected)
        m['files']=[row for row in records if row['path'] in selected]
        m['payload_projection']=projection
    m['package_id'] = package_id(m)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('gpu-package.json', json.dumps(m, ensure_ascii=False, indent=2))
        for row in m['files']:
            archive.writestr(row['path'], (ROOT/row['path']).read_bytes())
    return dict(package_id=m['package_id'], files=len(m['files']), bytes=Path(output).stat().st_size,
                archive_sha256=sha(Path(output).read_bytes()), source_commit=m['source_commit'])


def unpack(archive, destination):
    # Validate every member before creating a destination. Never extractall().
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate package members')
        for name in names:
            safe_name(name)
        m = json.loads(z.read('gpu-package.json'))
        if m.get('schema')!=SCHEMA or not isinstance(m.get('suite'),str) or not m['suite']:
            raise ValueError('Unsupported package schema or missing suite identity')
        listed=[row['path'] for row in m['files']]
        if len(listed)!=len(set(listed)):
            raise ValueError('Duplicate package artifact records')
        if m['package_id'] != package_id(m) or set(names) != {'gpu-package.json', *(r['path'] for r in m['files'])}:
            raise ValueError('Unlisted package members or identity mismatch')
        for row in m['files']:
            raw = z.read(row['path'])
            if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
                raise ValueError('Package member integrity failure')
        destination.mkdir(parents=True, exist_ok=False)
        for name in names:
            p = destination/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(name))
    # Transfer integrity is independent of this bootstrap CLI's suite registry.
    # The extracted package's own CLI performs semantic preflight before run.
    check_records(destination,m['files'])
    return m['package_id']


def module(path):
    spec = importlib.util.spec_from_file_location('gpu_suite_adapter', path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def open_suite(m):
    if compiler_only(m):raise ValueError('Compiler diagnostic has no battle adapter')
    adapter=module(ROOT/SUITES[m['suite']]['script'])
    if getattr(adapter,'STRICT_WIRE_DIMENSIONS',False):
        expected=adapter.suite.OUTPUT;configured=SUITES[m['suite']].get('output_words',786432)
        if type(expected) is not int or expected<1 or type(configured) is not int or configured!=expected:
            raise ValueError('Adapter output words disagree with transport allocation')
    return adapter


def is_development(m):
    return m.get('purpose', 'sealed') == 'development'


def compiler_only(m):
    return SUITES.get(m.get('suite'),{}).get('compiler_only') is True

def full_compiler(m):
    from portable_compiler_certificate import full_family
    config=SUITES.get(m.get('suite'),{})
    return config.get('compiler_only') is True and full_family(m.get('suite'),config.get('compiler_baseline_suite'))


def prepare_entries(adapter, m):
    entries, data = adapter.prepare()
    if is_development(m) and hasattr(adapter, 'development_entries'):
        entries = entries + adapter.development_entries()
        data = None
    selected = m.get('selected_cases', [])
    if not selected and data is not None:
        return entries, data
    names = [row[0] for row in entries]
    if len(set(selected)) != len(selected) or not set(selected) <= set(names):
        raise ValueError('Unknown or duplicate selected cases')
    entries = [row for row in entries if not selected or row[0] in selected]
    packed = array.array('I', [len(entries)])
    for _, words, _ in entries:
        packed.extend(words)
    if sys.byteorder != 'little': packed.byteswap()
    return entries, packed.tobytes()


def development_baseline(suite, cases):
    """Freeze inputs and native oracles without treating new GPU output as truth."""
    with forbid_gpu():
        m = dict(suite=suite, purpose='development', selected_cases=list(cases))
        adapter = open_suite(m)
        entries, data = prepare_entries(adapter, m)
        from portable_backend import source_hashes
        iw = adapter.suite.INPUT * 4
        return dict(input_sha256=sha(data), source_sha256=source_hashes(SUITES[suite]['source']),
                    entries=[dict(name=name, input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),
                                  native_sha256=native_hash(adapter, domain))
                             for i,(name,words,domain) in enumerate(entries)])


def native_value(adapter, domain):
    if domain is None:
        value = dict(status=64)
    elif hasattr(adapter,'native_reference'):
        value = adapter.native_reference(domain)
    else:
        value = dict(zip(('battle','skill_trace'), adapter.suite.inspect_native(domain[0])))
    return value


def native_hash(adapter, domain):
    return adapter.cross.digest(native_value(adapter,domain))


@contextlib.contextmanager
def forbid_gpu():
    import portable_backend
    import portable_slang_generation
    def stop(*args, **kwargs):
        raise RuntimeError('GPU build/execute forbidden in CPU/audit stage')
    with patch.object(portable_backend,'build',stop), patch.object(portable_backend,'execute',stop), patch.object(portable_backend,'execute_batches',stop),patch.object(portable_slang_generation,'build',stop),patch.object(portable_slang_generation,'_build_resident',stop):
        yield


PREPARED_INPUT_PROTOCOL='prepared-v1'


def transport_input_receipt(m,data,input_words):
    """Bind framing and every row to the immutable package's input baseline."""
    count=len(m['golden']['entries'])
    if type(input_words) is not int or input_words<1 or count<1 or len(data)!=4+count*input_words*4 or int.from_bytes(data[:4],'little')!=count:
        raise ValueError('Invalid prepared transport input framing')
    digest=sha(data)
    if digest!=m['golden']['input_sha256']:raise ValueError('Prepared transport input differs from golden')
    for i,row in enumerate(m['golden']['entries']):
        if sha(data[4+i*input_words*4:4+(i+1)*input_words*4])!=row['input_sha256']:
            raise ValueError('Prepared transport input row differs from golden')
    return dict(schema=1,package_id=m['package_id'],input_count=count,input_words=input_words,input_bytes=len(data),input_sha256=digest)


def capture_storage_preflight(m,capture,*,prepared=False):
    """Budget the exact uncompressed payload, before input/claim allocations."""
    from portable_capture_storage import space_status
    with forbid_gpu():adapter=open_suite(m)
    count=len(m['golden']['entries']);iw=adapter.suite.INPUT;ow=SUITES[m['suite']].get('output_words',786432)
    if any(type(v) is not int or v<1 for v in (count,iw,ow)):raise ValueError('Invalid storage shape')
    input_bytes=4+count*iw*4;output_bytes=count*ow*4
    if prepared:
        path=capture/'input.bin'
        if path.is_symlink() or not path.is_file() or path.stat().st_size!=input_bytes:raise ValueError('Prepared storage input size differs')
    budget=space_status(capture,output_bytes+(0 if prepared else input_bytes))
    report=dict(budget,input_bytes=input_bytes,output_bytes=output_bytes,prepared_input_present=prepared,gpu_calls=0,calculation_verified=False)
    write(capture/('storage-before-gpu.json' if prepared else 'storage.json'),report)
    if not budget['passed']:raise ValueError('Insufficient space for uncompressed input/readback and reserve; see storage receipt')
    return report


def publish_transport_input(m,capture,data,input_words):
    receipt=transport_input_receipt(m,data,input_words)
    for name in ('input.bin','input-preflight.json'):
        p=capture/name
        if p.exists() or p.is_symlink():raise ValueError('Fresh prepared transport input required')
    with (capture/'input.bin').open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    write(capture/'input-preflight.json',receipt)
    return receipt


def read_prepared_transport_input(m,capture):
    for name in ('input.bin','input-preflight.json','cpu.json'):
        p=capture/name
        if p.is_symlink() or not p.is_file():raise ValueError('Prepared transport input/gate missing or linked: '+name)
    receipt=load(capture/'input-preflight.json');cpu=load(capture/'cpu.json')
    if not isinstance(receipt,dict) or not isinstance(cpu,dict):raise ValueError('Invalid prepared transport input metadata')
    data=(capture/'input.bin').read_bytes()
    expected=transport_input_receipt(m,data,receipt.get('input_words'))
    exact=lambda a,b:json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
    if not exact(receipt,expected):
        raise ValueError('Prepared transport input receipt mismatch')
    if cpu.get('passed') is not True or cpu.get('input_sha256')!=receipt['input_sha256'] or not exact(cpu.get('input_count'),receipt['input_count']) or not exact(cpu.get('gpu_calls'),dict(build=0,execute=0)) or not exact(cpu.get('transport_input'),receipt):
        raise ValueError('Prepared transport input CPU gate mismatch')
    return data,receipt['input_words']


def prepare_legacy_child_input(m,capture):
    adapter=open_suite(m);entries,data=prepare_entries(adapter,m)
    if sha(data)!=m['golden']['input_sha256']:raise ValueError('Input changed after preflight')
    (capture/'input.bin').write_bytes(data)
    return data,adapter.suite.INPUT


def cpu_input_mismatch(m,entries,data,input_words,capture):
    """Diagnose existing static bytes only; never evaluate an oracle or retry."""
    if capture is None:return
    expected=m['golden']['entries'];iw=input_words*4;rows=[];count=0
    for i in range(max(len(entries),len(expected))):
        actual=entries[i] if i<len(entries) else None;baseline=expected[i] if i<len(expected) else None
        digest=sha(data[4+i*iw:4+(i+1)*iw]) if actual is not None else None
        if actual is not None and baseline is not None and actual[0]==baseline['name'] and digest==baseline['input_sha256']:continue
        count+=1
        if len(rows)<64:rows.append(dict(index=i,actual_name=actual[0] if actual else None,expected_name=baseline['name'] if baseline else None,actual_sha256=digest,expected_sha256=baseline['input_sha256'] if baseline else None))
    report=dict(schema=1,passed=False,stage='CPU input preflight',input_words=input_words,input_bytes=len(data),actual_input_count=len(entries),expected_input_count=len(expected),framing_valid=len(data)==4+len(entries)*iw and len(data)>=4 and int.from_bytes(data[:4],'little')==len(entries),actual_input_sha256=sha(data),expected_input_sha256=m['golden']['input_sha256'],row_mismatch_count=count,first_mismatched_rows=rows,rows_truncated=count>len(rows),python_version=sys.version.split()[0],platform=sys.platform,gpu_calls=0,diagnostic_native_oracle_calls=0,calculation_verified=False,raw_input_included=False,scope='Static-byte diagnosis only; earlier preflight work is not inferred')
    with (Path(capture)/'cpu-input-mismatch.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')


def cpu_preflight(m,*,parent_oracles=None,input_capture=None):
    started = time.perf_counter()
    (ROOT/'research/portable-build').mkdir(parents=True,exist_ok=True)
    # Patch before importing the adapter, so its from-import aliases are blocked.
    with forbid_gpu():
        adapter = open_suite(m)
        entries, data = prepare_entries(adapter, m)
        golden = m['golden']
        if sha(data) != golden['input_sha256'] or len(entries) != len(golden['entries']):
            cpu_input_mismatch(m,entries,data,adapter.suite.INPUT,input_capture)
            raise ValueError('Input differs from golden')
        iw = adapter.suite.INPUT*4
        if parent_oracles is not None:parent_oracles.prepare(adapter,entries)
        for i,(name,words,domain) in enumerate(entries):
            expected = golden['entries'][i]
            if name != expected['name'] or sha(data[4+i*iw:4+(i+1)*iw]) != expected['input_sha256']:
                cpu_input_mismatch(m,entries,data,adapter.suite.INPUT,input_capture)
                raise ValueError('First CPU/input mismatch: '+name)
            before=parent_oracles.before(i) if parent_oracles is not None else None
            value=native_value(adapter,domain)
            if adapter.cross.digest(value) != expected['native_sha256']:
                raise ValueError('First CPU/input mismatch: '+name)
            if parent_oracles is not None:parent_oracles.remember(i,before,value,adapter.cross.digest)
        if parent_oracles is not None:parent_oracles.finish()
    from portable_typed_cuda_proof_audit import verify_cpu_gpu_calls
    calls = dict(build=0,execute=0); verify_cpu_gpu_calls(calls)
    result=dict(passed=True, input_count=len(entries), native_oracles=sum(domain is not None for _,_,domain in entries),
                input_sha256=sha(data), gpu_calls=calls, elapsed_seconds=time.perf_counter()-started)
    if input_capture is not None:result['transport_input']=publish_transport_input(m,input_capture,data,adapter.suite.INPUT)
    result['elapsed_seconds']=time.perf_counter()-started
    return result


NATIVE_SMOKE_SCRIPT='app/portable_native_output_probe.py'


def native_smoke_child(capture):
    from portable_native_process import SuspendedNativeProcess,BELOW_NORMAL
    from portable_partition_object import verify_native_child
    import portable_offline_assembler as assembler
    from portable_phase_audit import Journal
    executable=str(Path(sys.executable).resolve());before=sha(Path(executable).read_bytes())
    from portable_native_output_probe import PROBE_NAME
    script=(ROOT/NATIVE_SMOKE_SCRIPT).resolve();script_sha=sha(script.read_bytes())
    argv=[executable,'-I','-S',str(script),str((capture/PROBE_NAME).resolve())];process=None
    journal=Journal(capture/'native-smoke-phases.jsonl');started=time.perf_counter()
    try:
        with (capture/'native-smoke.stdout.log').open('xb') as stdout,(capture/'native-smoke.stderr.log').open('xb') as stderr:
            process=SuspendedNativeProcess(argv,cwd=capture,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,shell=False,creationflags=BELOW_NORMAL)
            inspection,launch=verify_native_child(process,assembler.inspect_process,journal,'native_smoke',suspended=True)
            code=process.wait(timeout=10)
        try:probe=json.loads((capture/'native-smoke.stdout.log').read_bytes())
        except (ValueError,UnicodeError):probe=None
        # Retain the actual child return and I/O error even if it cannot create a file.
        write(capture/'native-smoke.json',dict(python_executable=executable,python_sha256=before,script_sha256=script_sha,argv=argv,inspection=inspection,native_launch=launch,return_code=code,output_probe=probe,elapsed_seconds=time.perf_counter()-started,gpu_calls=0))
        if code!=0:raise RuntimeError('Native output probe failed: '+str(probe))
        if sha(Path(executable).read_bytes())!=before or sha(script.read_bytes())!=script_sha:raise RuntimeError('Native smoke Python/script changed')
    except BaseException as error:
        journal.emit('native_smoke_failure','raised',exception=type(error).__name__)
        if process is not None and process.poll() is None:process.terminate();process.wait(timeout=5)
        raise
    finally:
        if process is not None:process.close()


def audit_native_smoke(capture,harness_pid):
    from portable_native_process import validate_launch
    from portable_offline_assembler import contained
    record=load(capture/'native-smoke.json');snapshot=record['inspection']
    validate_launch(record['native_launch'])
    if not contained(snapshot,harness_pid,snapshot['child_pid']) or snapshot.get('job_memory_limit_bytes')!=2147483648:raise ValueError('Native smoke inherited Job not verified')
    from portable_native_output_probe import PROBE_NAME,validate_probe
    script=(ROOT/NATIVE_SMOKE_SCRIPT).resolve()
    if record['argv']!=[record['python_executable'],'-I','-S',str(script),str((capture/PROBE_NAME).resolve())] or record['script_sha256']!=sha(script.read_bytes()) or record['return_code']!=0 or record['gpu_calls']!=0:raise ValueError('Native smoke command/return mismatch')
    try:emitted=json.loads((capture/'native-smoke.stdout.log').read_bytes())
    except (ValueError,UnicodeError) as error:raise ValueError('Native smoke output mismatch') from error
    if emitted!=record['output_probe'] or (capture/'native-smoke.stderr.log').read_bytes()!=b'':raise ValueError('Native smoke output mismatch')
    validate_probe(record['output_probe'],(capture/PROBE_NAME).read_bytes())
    return True


def child(capture, backend, smoke=False, compile_only=False, module_only=False, assemble_only=False,partition_object_only=False,module_object_only=False,link_object_only=False,jit_link_object_only=False):
    deadline = time.monotonic()+60
    while not (capture/'start.json').exists():
        if time.monotonic() >= deadline:
            raise RuntimeError('Containment gate not released; GPU not started')
        time.sleep(.02)
    if sum(map(bool,(compile_only,module_only,assemble_only,partition_object_only,module_object_only,link_object_only,jit_link_object_only)))>1:raise ValueError('Compile, module and assembly modes are exclusive')
    if smoke:
        if compile_only or module_only or assemble_only or partition_object_only or module_object_only or link_object_only or jit_link_object_only:raise ValueError('Compiler and smoke modes are exclusive')
        if os.name=='nt':native_smoke_child(capture)
        write(capture/'smoke.json',dict(pid=os.getpid(),ppid=os.getppid(),gpu_calls=0)); return
    from portable_phase_audit import Journal
    m = Journal(capture/'preparation.jsonl').invoke('gpu_child_verify_package',verify_package,ROOT)
    if jit_link_object_only:
        jit_link_child(m,capture,backend);return
    if link_object_only:
        partition_object_child(m,capture,backend,link_object=True);return
    if module_object_only:
        partition_object_child(m,capture,backend,module_object=True);return
    if partition_object_only:
        partition_object_child(m,capture,backend);return
    if assemble_only:
        assemble_child(m,capture,backend);return
    if compile_only:
        compile_child(m,capture,backend);return
    if module_only:
        module_child(m,capture,backend);return
    protocol=load(capture/'run.json').get('input_protocol','legacy') if (capture/'run.json').exists() else 'legacy'
    if protocol==PREPARED_INPUT_PROTOCOL:
        data,input_words=Journal(capture/'preparation.jsonl').invoke('gpu_child_prepared_input',read_prepared_transport_input,m,capture)
    elif protocol=='legacy':
        data,input_words=Journal(capture/'preparation.jsonl').invoke('gpu_child_legacy_input',prepare_legacy_child_input,m,capture)
    else:raise ValueError('Unknown transport input protocol')
    import portable_backend
    from portable_phase_audit import Journal, observe
    journal = Journal(capture/'phases.jsonl')
    with saved_linked_provider(m,capture,backend,journal),observe(portable_backend,journal):
        raw,evidence = journal.invoke('shared_gpu_execute',portable_backend.execute,
                                     SUITES[m['suite']]['source'],'portableEvents',data,
                                     input_words,SUITES[m['suite']].get('output_words',786432),backend,readback_path=capture/'readback.bin')
    if raw is not None:raise ValueError('File transport returned an unexpected whole readback')
    # Raw/evidence are durable before any comparison, so failures remain inspectable.
    write(capture/'evidence.json',evidence)
    copy_generated(capture,m['suite'])
    # Finish the contained transport before CPU comparison. The parent audits
    # the saved bytes independently; child exit0 alone never proves calculation.


def readback_parts(path,count,block_size,expected_digest):
    """Bounded second pass: hash the exact bytes consumed by every comparator."""
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for _ in range(count):
            part=stream.read(block_size)
            if len(part)!=block_size:raise ValueError('Readback changed during comparison: short block')
            h.update(part)
            yield part
        if stream.read(1) or h.hexdigest()!=expected_digest:
            raise ValueError('Readback changed during comparison: size/SHA mismatch')


def stream_input_fingerprints(path,count,stride):
    digest=hashlib.sha256();rows=[]
    with Path(path).open('rb') as stream:
        head=stream.read(4)
        if len(head)!=4 or int.from_bytes(head,'little')!=count:raise ValueError('Saved input count mismatch')
        digest.update(head)
        for _ in range(count):
            part=stream.read(stride)
            if len(part)!=stride:raise ValueError('Saved input truncated')
            digest.update(part);rows.append(sha(part))
        if stream.read(1):raise ValueError('Saved input has trailing bytes')
    return digest.hexdigest(),rows


def compare_readback(m, capture, adapter=None,*,parent_oracles=None):
    """Re-run existing native comparators; no GPU builds/executes allowed."""
    (ROOT/'research/portable-build').mkdir(parents=True, exist_ok=True)
    with forbid_gpu():
        fallback_receipt=None
        if parent_oracles is not None and not parent_oracles.usable:
            parent_oracles.check(m,capture);parent_oracles.check(verify_package(ROOT),capture)
            fallback_receipt=parent_oracles.fallback_receipt();parent_oracles.close();parent_oracles=None
        if parent_oracles is not None:
            parent_oracles.check(m,capture)
            parent_oracles.start(verify_package(ROOT),capture)
            adapter=parent_oracles.adapter;entries=parent_oracles.entries;data=None
        else:
            adapter = adapter or open_suite(m)
            entries,data = prepare_entries(adapter, m)
        evidence=load(capture/'evidence.json')
        record=file_records(capture,['readback.bin'])[0];output_digest=record['sha256']
        if parent_oracles is None:
            if (capture/'input.bin').read_bytes()!=data or sha(data)!=m['golden']['input_sha256']:raise ValueError('Saved input mismatch')
            input_hash=sha(data);iw=adapter.suite.INPUT*4
            input_digests=[sha(data[4+i*iw:4+(i+1)*iw]) for i in range(len(entries))]
        else:
            input_hash,input_digests=stream_input_fingerprints(capture/'input.bin',len(entries),adapter.suite.INPUT*4)
            if input_hash!=m['golden']['input_sha256']:raise ValueError('Saved input mismatch')
        if record['bytes']!=len(entries)*SUITES[m['suite']].get('output_words',786432)*4 or output_digest!=evidence['output_sha256'] or evidence['input_sha256']!=input_hash:
            raise ValueError('Saved evidence/raw mismatch')
        audit_generation_capture(m,capture)
        if evidence['source_sha256']!=m['golden']['source_sha256'] or not evidence['gpu_execution_verified']:
            raise ValueError('Wrong/unverified GPU source')
        if evidence['backend']=='cuda' and 'compile_artifact' in evidence['transport']:
            receipt=evidence['transport']['compile_artifact'];kind=receipt['identity']['artifact']
            if kind not in ('ptx','cubin'):raise ValueError('Unknown compiled CUDA artifact')
            artifact=(capture/('compiled.'+kind)).read_bytes()
            identity_key=sha(json.dumps(receipt['identity'],sort_keys=True,separators=(',',':')).encode())
            if receipt['key']!=identity_key or receipt['identity']['artifact'] not in ('ptx','cubin') or receipt['identity']['schema']!=1:
                raise ValueError('Invalid CUDA compile cache key/schema')
            linked=receipt['identity'].get('provider')=='saved-module-jit-cubin'
            if linked:
                audit_saved_linked_artifact(m,capture,receipt)
            else:
                from portable_backend import cuda_compile_options
                allowed=[cuda_compile_options(kind)]
                if kind=='cubin':allowed += [cuda_compile_options(kind,level) for level in range(4)]
                if receipt['identity']['options'] not in allowed:
                    raise ValueError('CUDA compiler options changed')
            if sha(artifact)!=receipt['artifact_sha256'] or len(artifact)!=receipt['artifact_bytes']:
                raise ValueError('Compiled CUDA artifact mismatch')
            if receipt['identity']['source_sha256']!=sha((capture/'generated.cu').read_bytes()):
                raise ValueError('Compiled CUDA source identity mismatch')
            phases=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
            stage='cuda_linked_artifact_receipt' if linked else 'cuda_compile_cache'
            if [r['receipt'] for r in phases if r['stage']==stage and r['state']=='verified']!=[receipt]:
                raise ValueError('CUDA compiler artifact phase mismatch')
            stream=evidence['transport'].get('readback_stream')
            markers=[r for r in phases if r['stage']=='cuda_readback_file' and r['state']=='returned']
            if stream is not None or markers:
                from portable_backend import READBACK_CHUNK_BYTES
                if stream is None or [r['receipt'] for r in markers]!=[stream] or stream.get('output_sha256')!=output_digest or stream.get('output_bytes')!=record['bytes'] or stream.get('chunk_bytes')!=READBACK_CHUNK_BYTES or stream.get('chunks')!=(record['bytes']+READBACK_CHUNK_BYTES-1)//READBACK_CHUNK_BYTES:
                    raise ValueError('CUDA file readback receipt mismatch')
        results=[]; mismatches=[]; iw=adapter.suite.INPUT*4; ow=SUITES[m['suite']].get('output_words',786432)*4
        parts=readback_parts(capture/'readback.bin',len(entries),ow,output_digest)
        for i,((name,words,domain),part) in enumerate(zip(entries,parts,strict=True)):
            block=array.array('I'); block.frombytes(part)
            if sys.byteorder!='little': block.byteswap()
            try:
                with parent_oracles.comparison(i) if parent_oracles is not None else contextlib.nullcontext():
                    if domain is None:
                        if block[0]!=64:raise ValueError('Expected rejection status64')
                        if hasattr(adapter,'validate_rejection'):adapter.validate_rejection(block,name)
                        if SUITES[m['suite']].get('require_rejection_stage'):adapter.validate_rejection_stage(block,name)
                        native=dict(status=64)
                    else:
                        if block[0]!=0:raise ValueError('Expected GPU success status0; got status'+str(block[0]))
                        native=adapter.compare(block,domain)
                row=dict(name=name,input_sha256=input_digests[i],output_sha256=sha(part),native_sha256=adapter.cross.digest(native))
                expected = m['golden']['entries'][i]
                actual = {key:row[key] for key in expected} if is_development(m) else row
                if actual!=expected:mismatches.append(dict(index=i,name=name,reason='fingerprint mismatch'))
                results.append(row)
            except (AssertionError,ValueError,KeyError,IndexError) as error:
                mismatches.append(dict(index=i,name=name,reason=type(error).__name__+': '+str(error)))
        # Reuse strict normalizer; no new normalization exceptions.
        generated={}
        for backend,suffix in [('cuda','cu'),('metal','metal')]:
            generated[backend]=adapter.cross.normalized((capture/('generated.'+suffix)).read_bytes())
        if not is_development(m) and generated!=m['golden']['generated_normalized']:mismatches.append(dict(reason='generated code mismatch'))
        if not is_development(m) and output_digest!=m['golden']['output_sha256']:mismatches.append(dict(reason='full readback fingerprint mismatch'))
        return dict(calculation_verified=not mismatches, entries=results, mismatches=mismatches,
                    input_count=len(entries), native_oracles=sum(domain is not None for _,_,domain in entries),
                    input_sha256=input_hash,output_sha256=output_digest,generated_normalized=generated,audit_gpu_calls=0,
                    **(dict(parent_oracles=parent_oracles.receipt()) if parent_oracles is not None else dict(parent_oracles=fallback_receipt) if fallback_receipt is not None else {}))


def replay_source(m, source_package, source_capture,reference_migration=None):
    """Validate an immutable successful Metal dispatch, including failed decode."""
    original=verify_package(source_package)
    if not is_development(m) or not is_development(original) or m['suite']!=original['suite'] or m['golden']!=original['golden'] and reference_migration is None:
        raise ValueError('Replay requires identical development source/input/native baselines')
    if reference_migration is not None:verify_reference_migration(reference_migration,original,m)
    old={r['path']:r['sha256'] for r in original['files']};new={r['path']:r['sha256'] for r in m['files']}
    critical={'app/portable_backend.py','app/portable_compile_cache.py','scripts/run-metal-probe.swift',
              'research/portable_phase_audit.py','research/summarize-portable-cross-gpu.py',
              'app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py'}
    critical |= {name for name in old.keys() | new.keys() if name.startswith(('gpu/','research/upstream/')) or name in ('app/portable_generation_cache.py','app/portable_slang_generation.py','app/portable_metal_cache.py')}
    if any(name not in old or name not in new or old[name]!=new[name] for name in critical):
        raise ValueError('GPU transport, source, normalizer or canonical reference changed')
    run=load(source_capture/'run.json')
    if run['package_id']!=original['package_id'] or run['backend']!='metal' or run.get('mode')!='gpu':
        raise ValueError('Original Metal GPU capture required')
    claim=load(source_package/'gpu-claimed-metal.json')
    if claim['package_id']!=original['package_id'] or Path(claim['capture']).resolve()!=source_capture.resolve():
        raise ValueError('Original GPU execution claim mismatch')
    records=load(source_capture/'artifacts.json')['files']
    required={'run.json','execution.json','evidence.json','phases.jsonl','comparison.json','result.json'}
    if not required <= {r['path'] for r in records}:raise ValueError('Original capture proof set incomplete')
    check_records(source_capture,records)
    facts=load(source_capture/'execution.json');evidence=load(source_capture/'evidence.json')
    if facts['timed_out'] or any(facts[k] is not None for k in ('error','cleanup_error','observation_error')):
        raise ValueError('Timeout/control failure cannot be replayed as a completed dispatch')
    if facts['final_child_exit_code'] not in (0,1):raise ValueError('Unexpected original child termination')
    if evidence['backend']!='metal' or not evidence['gpu_execution_verified'] or evidence['transport']['command_status']!='completed':
        raise ValueError('Original dispatch did not complete on Metal')
    rows=[json.loads(line) for line in (source_capture/'phases.jsonl').read_text().splitlines()]
    dispatch=[r['state'] for r in rows if r['stage']=='shared_gpu_execute']
    if dispatch!=['entered','returned']:raise ValueError('Original GPU execution boundary incomplete')
    for backend,suffix in [('cuda','cu'),('metal','metal')]:
        if sha((source_capture/('generated.'+suffix)).read_bytes())!=evidence['generated_sha256'][backend]:
            raise ValueError('Original generated bytes mismatch')
    return original,facts,evidence

def verify_reference_migration(name,original,m):
    if name=='leftmost-rejection-domains-v1':
        from portable_leftmost_replay_migration import verify
        with forbid_gpu():
            adapter=open_suite(m);entries,_=prepare_entries(adapter,m)
            return verify(original,m,entries)
    from portable_reference_migration import verify,CASE
    with forbid_gpu():
        adapter=open_suite(m);entries,_=prepare_entries(adapter,m)
        domains=[d for n,_,d in entries if n==CASE]
        if len(domains)!=1 or domains[0] is None:raise ValueError('Native observation migration domain missing')
        return verify(name,original,m,adapter.native_reference(domains[0]))


def audit_replay_capture(m, capture, *, verify_artifacts=True,record_comparison=False):
    run=load(capture/'run.json');origin=load(capture/'replay.json')
    if run['package_id']!=m['package_id'] or run['backend']!='metal':raise ValueError('Wrong replay package/backend')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    original,facts,evidence=replay_source(m,Path(origin['source_package']),Path(origin['source_capture']),origin.get('reference_migration'))
    if origin.get('reference_migration'):
        if load(capture/'reference-migration.json')!=verify_reference_migration(origin['reference_migration'],original,m):raise ValueError('Native observation migration receipt mismatch')
    if origin['source_package_id']!=original['package_id']:raise ValueError('Wrong original package')
    source=Path(origin['source_capture'])
    for name in ('input.bin','readback.bin','evidence.json','generated.cu','generated.metal'):
        if (capture/name).read_bytes()!=(source/name).read_bytes():raise ValueError('Replay changed original bytes: '+name)
    if (capture/'source-execution.json').read_bytes()!=(source/'execution.json').read_bytes():
        raise ValueError('Replay changed original failure/control facts')
    result=compare_readback(m,capture)
    if record_comparison:write(capture/'comparison.json',result)
    return dict(result,passed=result['calculation_verified'],preservation_verified=None,sealed=False,
                mode='saved-metal-replay',source_package_id=original['package_id'],source_execution_passed=facts['passed'],
                original_failure_preserved=True,gpu_calls=0,gpu_retry_count=0,source_gpu_dispatches=1)


def replay_capture(capture, source_package, source_capture,reference_migration=None):
    m=verify_package(ROOT);original,facts,evidence=replay_source(m,source_package,source_capture,reference_migration)
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend='metal',mode='replay',status='replaying',gpu_retry_count=0))
    write(capture/'replay.json',dict(source_package=str(source_package.resolve()),source_capture=str(source_capture.resolve()),source_package_id=original['package_id']))
    if reference_migration:
        origin=load(capture/'replay.json');origin['reference_migration']=reference_migration;write(capture/'replay.json',origin)
        write(capture/'reference-migration.json',verify_reference_migration(reference_migration,original,m))
    for name in ('input.bin','readback.bin','evidence.json','generated.cu','generated.metal'):
        (capture/name).write_bytes((source_capture/name).read_bytes())
    (capture/'source-execution.json').write_bytes((source_capture/'execution.json').read_bytes())
    try:
        result=audit_replay_capture(m,capture,verify_artifacts=False,record_comparison=True)
        write(capture/'result.json',result)
        run=load(capture/'run.json');run['status']='finished';write(capture/'run.json',run)
    except BaseException as error:
        write(capture/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_calls=0));raise
    finally:collect(capture,capture/'artifacts.json')
    return result


def compiler_statistics(capture,output,*,top=12,caller=None,runtime=None):
    """Inspect a saved generated source with the existing artifact verifier."""
    if output.exists():raise ValueError('Compiler statistics output already exists')
    records=load(capture/'artifacts.json')['files']
    source=[r for r in records if r['path']=='generated.cu']
    if len(source)>1:raise ValueError('Duplicate generated CUDA source records')
    if source:check_records(capture,source)
    raw=(capture/'generated.cu').read_bytes()
    from portable_compiler_stats import cuda_statistics
    result=cuda_statistics(raw,top=top,caller=caller,runtime=runtime)
    anchored=bool(source)
    for name in ('evidence.json','compiler.json'):
        if (capture/name).is_file():
            record=[r for r in records if r['path']==name]
            if len(record)!=1:raise ValueError('Source evidence record missing')
            check_records(capture,record)
            if load(capture/name)['generated_sha256']['cuda']!=result['source_sha256']:
                raise ValueError('Generated CUDA does not match source evidence')
            anchored=True
    if not anchored:raise ValueError('Saved generated-source hash evidence required')
    result.update(source_integrity_verified=True,analysis_complete=True,
                  calculation_verified=False,compiler_verified=False,
                  gpu_calls=0,nvrtc_compile_calls=0)
    write(output,result);return result


def ptx_statistics(cache_entry,phases,output,*,top=8,callgraph=False):
    if output.exists():raise ValueError('PTX statistics output already exists')
    from portable_ptx_stats import saved_ptx_statistics
    result=saved_ptx_statistics(cache_entry,phases,top=top,callgraph=callgraph)
    write(output,result);return result


def check_compile_cache(capture, output):
    """Verify warm artifact reuse using file reads only: NVRTC/GPU forbidden."""
    m=verify_package(ROOT)
    if load(capture/'run.json')['package_id']!=m['package_id']:
        raise ValueError('Capture belongs to another package')
    check_records(capture,load(capture/'artifacts.json')['files'])
    if load(capture/'run.json')['backend']!='cuda':raise ValueError('CUDA artifact required')
    evidence=load(capture/'evidence.json') if (capture/'evidence.json').exists() else None
    if evidence and evidence['transport']['compile_artifact']['identity'].get('provider')=='saved-module-jit-cubin':
        started=time.perf_counter();receipt=evidence['transport']['compile_artifact']
        with forbid_gpu():audit_saved_linked_artifact(m,capture,receipt)
        result=dict(passed=True,cache=receipt,elapsed_seconds=time.perf_counter()-started,gpu_calls=0,nvrtc_compile_calls=0,calculation_verified=False,package_id=m['package_id'])
        with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        return result
    from portable_compile_cache import get_or_compile,quoted_headers
    directory=os.environ.get('NIKKE_CUDA_COMPILE_CACHE')
    if not directory:raise ValueError('NIKKE_CUDA_COMPILE_CACHE is required')
    cuda_bin=Path(os.environ.get('CUDA_PATH',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
    if evidence is not None:receipt=evidence['transport']['compile_artifact']
    else:
        receipts=[]
        lines=(capture/'phases.jsonl').read_text().splitlines()
        for i,line in enumerate(lines):
            try:row=json.loads(line)
            except json.JSONDecodeError:
                if i!=len(lines)-1:raise
                continue
            if row['stage']=='cuda_compile_cache' and row['state']=='verified':receipts.append(row['receipt'])
        if len(receipts)!=1:raise ValueError('No unique successful compiler artifact')
        receipt=receipts[0]
    def forbidden():raise RuntimeError('Cache miss; NVRTC compilation forbidden in cache-check')
    started=time.perf_counter()
    artifact,hit=get_or_compile((capture/'generated.cu').read_bytes(),receipt['identity']['options'],
                               list(cuda_bin.glob('nvrtc*.dll')),forbidden,directory,
                               header_files=quoted_headers((capture/'generated.cu').read_bytes()),
                               artifact_kind=receipt['identity']['artifact'])
    if not hit['hit'] or hit['key']!=receipt['key'] or artifact!=(capture/('compiled.'+receipt['identity']['artifact'])).read_bytes():
        raise ValueError('Warm CUDA artifact does not match captured compiler output')
    result=dict(passed=True,cache=hit,elapsed_seconds=time.perf_counter()-started,
                gpu_calls=0,nvrtc_compile_calls=0,calculation_verified=False,package_id=m['package_id'])
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    return result


def audited_comparison(module, capture):
    """Use the original comparator's result from this fresh independent audit."""
    observed=[]
    original=module.compare_readback
    def compare(*args,**kwargs):
        result=original(*args,**kwargs)
        observed.append(result)
        return result
    with patch.object(module,'compare_readback',compare):
        audit=module.audit_capture(capture)
    if not audit['calculation_verified'] or len(observed)!=1:
        raise ValueError('Seal requires exactly one successful independent comparison')
    return audit,observed[0]


def audit_saved_metal(package_root,capture,*,timeout=60,development_only=False):
    """GPU0 audit in the saved package's own process/import context."""
    # Use the package's own imports and auditors in a fresh process. Its files
    # are verified before native work; never patch a consumed package in place.
    # Legacy adapter chains use relative module paths: anchor their cwd too.
    if type(timeout) is not int or not 1<=timeout<=180:raise ValueError('CPU seal timeout must be an integer from 1 to 180 seconds')
    script = """import importlib.util,json,sys,pathlib
root=pathlib.Path(sys.argv[1]);capture=pathlib.Path(sys.argv[2])
s=importlib.util.spec_from_file_location('seal_controller',sys.argv[3])
controller=importlib.util.module_from_spec(s);s.loader.exec_module(controller)
s=importlib.util.spec_from_file_location('seal_cli',root/'scripts/nikke_gpu.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=m.verify_package(root)
if (sys.argv[4]=='development' and not m.is_development(p)) or p.get('purpose','sealed') not in ('sealed','development') or m.load(capture/'run.json')['backend']!='metal':raise ValueError('Matching Metal battle capture required')
a,r=controller.audited_comparison(m,capture)
g=dict(input_sha256=r['input_sha256'],output_sha256=r['output_sha256'],source_sha256=p['golden']['source_sha256'],entries=r['entries'],generated_normalized=r['generated_normalized'])
print(json.dumps(dict(golden=g,package_id=p['package_id'],audit=a)))
"""
    completed=subprocess.run([sys.executable,'-c',script,str(package_root.resolve()),str(capture.resolve()),str(Path(__file__).resolve()),'development' if development_only else 'battle'],
                             cwd=package_root.resolve(),capture_output=True,text=True,check=True,timeout=timeout)
    result=json.loads(completed.stdout)
    for name,digest in result['golden']['source_sha256'].items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError('Current source differs from verified Metal source')
    return result


def seal_development(package_root,capture,output,*,timeout=60):
    """Explicit GPU0 seal of a successful immutable Metal development capture."""
    result=audit_saved_metal(package_root,capture,timeout=timeout,development_only=True)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result['golden'],stream,ensure_ascii=False,indent=2);stream.write('\n')
    return dict(sealed=True,gpu_calls=0,package_id=result['package_id'],
                input_count=len(result['golden']['entries']),golden=str(output.resolve()))


def make_compiler_certificate(suite,package_root,capture,output,*,timeout=120):
    """Re-audit saved Metal bytes using the shared seal; never run generation/GPU."""
    from portable_compiler_certificate import certificate
    from portable_backend import source_hashes
    diagnostic=compiler_alias(suite)
    if diagnostic not in SUITES or not full_compiler(dict(suite=diagnostic)):raise ValueError('Registered full-world battle suite required')
    if type(timeout) is not int or not 1<=timeout<=180:raise ValueError('CPU certificate timeout must be1..180 seconds')
    output.mkdir(parents=True,exist_ok=False)
    try:
        package=verify_package(package_root);run=load(capture/'run.json')
        anchors={str(path):sha(path.read_bytes()) for path in (package_root/'gpu-package.json',capture/'artifacts.json',capture/'run.json')}
        if package['suite']!=suite or compiler_only(package) or package.get('selected_cases') or run.get('backend')!='metal' or run.get('package_id')!=package['package_id']:
            raise ValueError('Unfiltered matching Metal battle package/capture required')
        expected_path=ROOT/SUITES[suite]['golden'];raw=expected_path.read_bytes();baseline=json.loads(raw)
        if baseline['source_sha256']!=source_hashes(SUITES[suite]['source']):raise ValueError('Current Metal source baseline is stale')
        if package['golden']['source_sha256']!=baseline['source_sha256']:raise ValueError('Saved Metal source closure differs from current baseline')
        # The original immutable package owns imports and native comparisons.
        # Existing successful flags or a user-provided seal JSON alone are insufficient.
        proof=audit_saved_metal(package_root,capture,timeout=timeout)
        write(output/'metal-golden.json',proof['golden'])
        if proof['package_id']!=package['package_id'] or proof['golden']!=baseline:raise ValueError('Audited Metal output differs from the registered battle baseline')
        result=certificate(suite,baseline,raw)
        if raw!=expected_path.read_bytes() or baseline['source_sha256']!=source_hashes(SUITES[suite]['source']):raise ValueError('Metal baseline changed during certificate preparation')
        if verify_package(package_root)!=package or any(sha(Path(path).read_bytes())!=digest for path,digest in anchors.items()):raise ValueError('Saved Metal package/capture changed during certificate preparation')
        write(output/'source-certificate.json',result)
        report=dict(passed=True,compiler_suite=diagnostic,certificate_target=SUITES[diagnostic]['golden'],
            baseline_suite=suite,baseline_golden_sha256=sha(raw),certificate_sha256=sha((output/'source-certificate.json').read_bytes()),
            metal_package_id=package['package_id'],metal_manifest_sha256=anchors[str(package_root/'gpu-package.json')],
            metal_artifacts_sha256=anchors[str(capture/'artifacts.json')],metal_run_sha256=anchors[str(capture/'run.json')],metal_input_count=len(proof['golden']['entries']),
            independent_metal_audit=True,compiler_verified=False,cache_hit_verified=False,calculation_verified=False,
            gpu_calls=0,compiler_calls=0,scope='Compiler source identity only; audited Metal baseline is a separate calculation proof')
        write(output/'report.json',report);return report
    except BaseException as error:
        write(output/'failure.json',dict(passed=False,error=type(error).__name__+': '+str(error),gpu_calls=0,compiler_calls=0));raise


def copy_generated(capture, suite, *, partial=False):
    stem=Path(SUITES[suite]['source']).stem
    for suffix in ('cu','metal'):
        source=ROOT/'research/portable-build'/(stem+'.'+suffix)
        if source.exists():(capture/('generated.'+suffix)).write_bytes(source.read_bytes())
        elif not partial:raise ValueError('Missing generated source: '+suffix)
    for kind in ('ptx','cubin'):
        source=ROOT/'research/portable-build'/(stem+'.'+kind)
        if source.exists():(capture/('compiled.'+kind)).write_bytes(source.read_bytes())

    if os.environ.get('NIKKE_SLANG_GENERATION_CACHE'):
        receipt=ROOT/'research/portable-build'/(stem+'.generation-cache.json')
        if receipt.exists():
            (capture/'generation-cache.json').write_bytes(receipt.read_bytes())
            for suffix in ('cu','metal'):
                source=ROOT/'research/portable-build'/(stem+'.'+suffix+'.reflection.json')
                (capture/('generated.'+suffix+'.reflection.json')).write_bytes(source.read_bytes())
        elif not partial:raise ValueError('Missing Slang generation cache receipt')


def audit_generation_capture(m,capture):
    runtime=load(capture/'runtime.json') if (capture/'runtime.json').exists() else {}
    active=runtime.get('generation_cache_enabled',False) and load(capture/'run.json').get('mode') in ('gpu','compile-only','module-only')
    if not active:
        if (capture/'generation-cache.json').exists():raise ValueError('Unexpected Slang generation cache receipt')
        return None
    from portable_generation_cache import audit_receipt
    receipt=load(capture/'generation-cache.json')
    if runtime.get('generation_cache_required') and not receipt['hit']:raise ValueError('Required Slang generation cache was not a hit')
    result=audit_receipt(receipt,m['golden']['source_sha256'],{t:capture/('generated.'+suffix) for t,suffix in [('cuda','cu'),('metal','metal')]})
    rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
    calls=[r['state'] for r in rows if r['stage']=='slang_compiler']
    if calls!=['entered','returned']*receipt['compiler_invocations']:raise ValueError('Slang generation compiler invocation mismatch')
    if [r.get('receipt') for r in rows if r['stage']=='slang_generation_cache' and r['state']=='verified']!=[receipt]:raise ValueError('Slang generation cache journal mismatch')
    return result


def bounded_module():
    return module(ROOT/'research/run-world-bounded.py')


def validation_environment(capture):
    """Keep owned Windows tests/compiler scratch out of a sandbox default TEMP."""
    env=os.environ.copy();env.pop('__PYVENV_LAUNCHER__',None)
    # Package sources, JSON and child logs use UTF-8 on every host. Scope this
    # to owned validation processes; never change the user's OS/Python setup.
    env['PYTHONUTF8']='1';env['PYTHONIOENCODING']='utf-8'
    if platform.system()=='Darwin':
        cache=Path(env.get('NIKKE_METAL_MODULE_CACHE',str((capture/'swift-module-cache').resolve())))
        if not cache.is_absolute():raise ValueError('Absolute private Swift module cache required')
        cache.mkdir(parents=True,exist_ok=True);env['NIKKE_METAL_MODULE_CACHE']=str(cache)
    if os.name=='nt':
        temporary=(capture/'temporary').resolve();temporary.mkdir(exist_ok=True)
        for key in ('TEMP','TMP','TMPDIR'):env[key]=str(temporary)
    return env


def run_job(capture,backend,timeout,original_workspace=None,smoke=False,compile_only=False,module_only=False,assemble_only=False,partition_object_only=False,module_object_only=False,link_object_only=False,jit_link_object_only=False):
    bounded=bounded_module()
    env=validation_environment(capture)
    env['PYTHONPATH']=os.pathsep.join([*site.getsitepackages(),env.get('PYTHONPATH','')])
    interpreter=getattr(sys,'_base_executable',sys.executable) if os.name=='nt' else sys.executable
    command=[interpreter,str(Path(__file__).resolve()),'_child','--capture',str(capture),'--backend',backend]
    if smoke:command.append('--smoke')
    if compile_only:command.append('--compile-only')
    if assemble_only:command.append('--assemble-only')
    if partition_object_only:command.append('--partition-object-only')
    if module_object_only:command.append('--module-object-only')
    if link_object_only:command.append('--link-object-only')
    if jit_link_object_only:
        command.append('--jit-link-object-only')
        env['CUDA_CACHE_DISABLE']='1'
        cache=(capture/'jit-private-cache').resolve();cache.mkdir(exist_ok=True);env['CUDA_CACHE_PATH']=str(cache)
    if (capture/'linked-artifact-request.json').exists():
        env['CUDA_CACHE_DISABLE']='1';env['CUDA_CACHE_PATH']=str((capture/'linked-private-cache').resolve());Path(env['CUDA_CACHE_PATH']).mkdir(exist_ok=False)
    if module_only:
        command.append('--module-only')
        driver_cache=(capture/'driver-cache').resolve();driver_cache.mkdir(exist_ok=True)
        env['CUDA_CACHE_PATH']=str(driver_cache)
    write(capture/'runtime.json',dict(interpreter=interpreter,parent_interpreter=sys.executable,platform=platform.platform(),generation_cache_enabled=bool(os.environ.get('NIKKE_SLANG_GENERATION_CACHE')),generation_cache_path=env.get('NIKKE_SLANG_GENERATION_CACHE'),generation_cache_required=os.environ.get('NIKKE_SLANG_GENERATION_REQUIRED','0')=='1',slang_root=os.environ.get('NIKKE_SLANG_ROOT'),cuda_artifact_kind=('diagnostic-jit-linked-cubin' if jit_link_object_only else 'diagnostic-linked-cubin' if link_object_only else 'diagnostic-module-relocatable-object' if module_object_only else 'diagnostic-relocatable-object' if partition_object_only else os.environ.get('NIKKE_CUDA_ARTIFACT','cubin')) if backend=='cuda' else None,compile_cache_enabled=bool(os.environ.get('NIKKE_CUDA_COMPILE_CACHE')),compile_cache_path=env.get('NIKKE_CUDA_COMPILE_CACHE'),compile_only=compile_only,module_only=module_only,assemble_only=assemble_only,partition_object_only=partition_object_only,module_object_only=module_object_only,link_object_only=link_object_only,jit_link_object_only=jit_link_object_only,swift_module_cache_path=env.get('NIKKE_METAL_MODULE_CACHE'),metal_pipeline_cache_enabled=backend=='metal' and bool(env.get('NIKKE_METAL_PIPELINE_CACHE')),metal_pipeline_cache_required=backend=='metal' and env.get('NIKKE_METAL_PIPELINE_REQUIRED')=='1',jit_private_cache_path=env.get('CUDA_CACHE_PATH') if jit_link_object_only else None,driver_cache_path=env.get('CUDA_CACHE_PATH') if module_only else None,ptxas_optimization_level=os.environ.get('NIKKE_CUDA_PTXAS_OPT_LEVEL'),cache_required=os.environ.get('NIKKE_CUDA_CACHE_REQUIRED','0'),job_memory_limit_mb=os.environ.get('NIKKE_VALIDATION_JOB_MEMORY_MB'),launcher_variable_removed='__PYVENV_LAUNCHER__' not in env))
    from portable_phase_audit import Journal
    preparation=Journal(capture/'preparation.jsonl')
    observation={}
    if os.name=='nt':
        from windows_validation_observer import capture_snapshot,observe_job,compare_snapshots
        if not original_workspace:raise ValueError('--original-workspace is required on Windows')
        def before():
            observation['before']=preparation.invoke('inner_before_observation',capture_snapshot,original_workspace,ROOT)
            write(capture/'observation.json',observation)
        def after():
            observation['after']=preparation.invoke('inner_after_observation',capture_snapshot,original_workspace,ROOT)
            if 'before' in observation:observation['comparison']=compare_snapshots(observation['before'],observation['after'])
            write(capture/'observation.json',observation)
        with observe_job(bounded,capture/'job.json'):
            facts=bounded.run_bounded(command,capture,timeout,cwd=ROOT,env=env,before_gate=before,after_wait=after)
    else:facts=bounded.run_bounded(command,capture,timeout,cwd=ROOT,env=env)
    return facts


def cpu_test_environment(capture):
    # Execution cache selection belongs to the GPU/compiler child. Unit tests
    # exercise their own opt-in cache settings and minimal fake backends.
    env=validation_environment(capture)
    for name in ('NIKKE_SLANG_GENERATION_CACHE','NIKKE_SLANG_GENERATION_REQUIRED','NIKKE_METAL_PIPELINE_CACHE','NIKKE_METAL_PIPELINE_REQUIRED'):env.pop(name,None)
    return env


def cpu_test_groups(m,capture,smoke=False):
    """Keep discovery/import in one fresh CPU process; never skip a registry group."""
    from portable_cpu_tests import validate_groups,validate_dependency_files,complete
    patterns=SMOKE_TESTS if smoke else SUITES[m['suite']]['tests']
    validate_groups(ROOT,patterns)
    validate_dependency_files(ROOT,patterns,included={r['path'] for r in m.get('files',[])})
    timeout=SUITES[m['suite']].get('cpu_test_timeout',60)
    if type(timeout) is not int or not 1<=timeout<=180:raise ValueError('Invalid bounded CPU test timeout')
    if not patterns:
        write(capture/'cpu-tests.json',[]);return []
    command=[sys.executable,str(Path(__file__).resolve()),'_tests','--capture',str(capture)]
    if smoke:command.append('--smoke')
    started=time.perf_counter();timed_out=False;completed=None
    try:
        completed=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=timeout,env=cpu_test_environment(capture))
    except subprocess.TimeoutExpired as error:
        timed_out=True
        (capture/'cpu-batch.stdout.log').write_bytes(error.stdout or b'');(capture/'cpu-batch.stderr.log').write_bytes(error.stderr or b'')
        raise
    finally:
        write(capture/'cpu-batch.json',dict(schema=1,mode='single-process-unittest',patterns=list(patterns),timeout_seconds=timeout,
            elapsed_seconds=time.perf_counter()-started,timed_out=timed_out,exit_code=completed.returncode if completed else None,
            gpu_calls=0,scope='Python group output in per-group logs; inherited native subprocess output in batch logs'))
    (capture/'cpu-batch.stdout.log').write_bytes(completed.stdout);(capture/'cpu-batch.stderr.log').write_bytes(completed.stderr)
    rows=load(capture/'cpu-tests.json') if (capture/'cpu-tests.json').exists() else []
    if completed.returncode or not complete(rows,patterns):
        failed=next((r['pattern'] for r in rows if r.get('exit_code')!=0),'incomplete batch')
        raise ValueError('CPU tests failed: '+failed)
    return rows


def validate_generation_request(m):
    if not os.environ.get('NIKKE_SLANG_GENERATION_CACHE'):return
    import re
    pattern=rb'^\s*#define\s+PORTABLE_RESIDENT_RUNTIME(?:\s|$)'
    if not any(re.search(pattern,(ROOT/name).read_bytes(),re.M) for name in m['golden']['source_sha256']):
        raise ValueError('Generation cache requires a resident source; omit --generation-cache for a standalone probe')


def cache_probe(source,cuda_root,cache,output,*,artifact_kind='cubin',ptxas_level=None,require_hit=False):
    """Inspect an exact source/toolchain cache without changing its contents."""
    source,cuda_root,cache,output=map(lambda p:Path(p).resolve(),(source,cuda_root,cache,output))
    if output.is_relative_to(cache) or output.is_relative_to(cuda_root):raise ValueError('Cache probe report must be outside cache and toolchain')
    if not source.is_file():raise ValueError('Generated CUDA source is missing')
    started=time.perf_counter()
    with output.open('x',encoding='utf-8') as stream:
        try:
            import portable_backend
            def forbidden(*args,**kwargs):raise RuntimeError('Native libraries and processes forbidden during cache probe')
            with forbid_gpu(),patch.object(portable_backend.subprocess,'run',forbidden),\
                 patch.object(portable_backend.C,'WinDLL',forbidden,create=True),patch.object(portable_backend.C,'CDLL',forbidden):
                receipt=portable_backend.probe_cuda_source_cache(source,cache,cuda_root=cuda_root,artifact_kind=artifact_kind,ptxas_level=ptxas_level)
            result=dict(passed=receipt['hit'] if require_hit else True,probe_verified=True,cache=receipt,
                gpu_calls=0,nvrtc_compile_calls=0,calculation_verified=False,preservation_verified=None,
                elapsed_seconds=time.perf_counter()-started,scope='Exact requested generated bytes/toolchain only; not a GPU calculation or compiler performance proof')
        except BaseException as error:
            json.dump(dict(passed=False,error=type(error).__name__+': '+str(error),gpu_calls=0,calculation_verified=False),stream,indent=2)
            stream.write('\n');stream.flush();os.fsync(stream.fileno());raise
        json.dump(result,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    return result


@contextlib.contextmanager
def cache_file_checks_only():
    import portable_backend
    import portable_slang_generation
    cached_generation_build=portable_slang_generation.build
    blocked=[]
    def forbidden(*args,**kwargs):
        blocked.append('compiler/process/library');raise RuntimeError('Required-cache preflight forbids compilation, subprocesses and native libraries')
    with forbid_gpu(),patch.object(portable_backend,'_build_resident',forbidden),\
         patch.object(portable_slang_generation,'build',cached_generation_build),patch.object(portable_slang_generation,'_build_resident',forbidden),\
         patch.object(portable_backend.subprocess,'run',forbidden),\
         patch.object(portable_backend.C,'WinDLL',forbidden,create=True),patch.object(portable_backend.C,'CDLL',forbidden):
        yield blocked


def required_generation_snapshot(m):
    import portable_backend
    started=time.perf_counter();cached_build=portable_backend.build
    with cache_file_checks_only() as blocked:
        source=SUITES[m['suite']]['source'];outputs,hashes=cached_build(source,'portableEvents')
        normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
        generated={k:normalized(p.read_bytes()) for k,p in outputs.items()}
        expected=m['golden'].get('generated_normalized')
        if hashes!=m['golden']['source_sha256'] or (expected is not None and generated!=expected) or (not is_development(m) and expected is None):
            raise ValueError('Cache preflight source differs from the sealed Metal proof')
        generation=load(ROOT/'research/portable-build'/(Path(source).stem+'.generation-cache.json'))
        if generation.get('hit') is not True or generation.get('compiler_invocations')!=0:
            raise ValueError('Cache preflight requires a verified generation cache hit')
    return outputs,dict(passed=True,stage='before-cpu-preflight',package_id=m['package_id'],generation=generation,
        generated_normalized=generated,sealed_generated_baseline_verified=expected is not None,
        elapsed_seconds=time.perf_counter()-started,forbidden_attempts=blocked,gpu_calls=0,nvrtc_compile_calls=0,
        calculation_verified=False,preservation_verified=None,scope='Required generation-cache snapshot, not a calculation proof')


def required_generation_cache_preflight(m,capture):
    required=os.environ.get('NIKKE_SLANG_GENERATION_REQUIRED','0')
    if required not in ('0','1'):raise ValueError('Required cache flags must be0 or1')
    if required!='1':return False
    if not os.environ.get('NIKKE_SLANG_GENERATION_CACHE'):raise ValueError('Required generation cache directory is missing')
    _,result=required_generation_snapshot(m);write(capture/'generation-preflight.json',result);return True


def required_cuda_cache_preflight(m,capture):
    """Paired required-cache snapshot before CPU work; never a launch proof."""
    required=os.environ.get('NIKKE_CUDA_CACHE_REQUIRED','0');generation_required=os.environ.get('NIKKE_SLANG_GENERATION_REQUIRED','0')
    if required not in ('0','1') or generation_required not in ('0','1'):raise ValueError('Required cache flags must be0 or1')
    if required!='1' or generation_required!='1':return False
    started=time.perf_counter()
    if not os.environ.get('NIKKE_SLANG_GENERATION_CACHE') or not os.environ.get('NIKKE_CUDA_COMPILE_CACHE'):
        raise ValueError('Paired required caches need both cache directories')
    outputs,snapshot=required_generation_snapshot(m)
    import portable_backend
    with cache_file_checks_only() as blocked:
        kind=portable_backend.cuda_artifact_kind();level=os.environ.get('NIKKE_CUDA_PTXAS_OPT_LEVEL')
        if level not in (None,'','0','1','2','3'):raise ValueError('Invalid NIKKE_CUDA_PTXAS_OPT_LEVEL')
        receipt=portable_backend.probe_cuda_source_cache(outputs['cuda'],os.environ['NIKKE_CUDA_COMPILE_CACHE'],
            artifact_kind=kind,ptxas_level=None if level in (None,'') else int(level))
    result=dict(passed=receipt['hit'],stage='before-cpu-preflight',package_id=m['package_id'],generation=snapshot['generation'],generation_preflight=snapshot,
        cache=receipt,elapsed_seconds=time.perf_counter()-started,forbidden_attempts=blocked,
        gpu_calls=0,nvrtc_compile_calls=0,calculation_verified=False,preservation_verified=None,
        scope='File-only advisory snapshot; bounded child revalidates required caches before loading or execution')
    write(capture/'cache-preflight.json',result)
    if not receipt['hit']:raise RuntimeError('Required CUDA cache miss before CPU preflight; no execution claim consumed')
    return True


def run_capture(capture,backend,timeout,original_workspace=None,smoke=False,cpu_only=False,*,linked_package=None,linked_capture=None):
    parent_oracles=None
    m=verify_package(ROOT)
    if compiler_only(m) and not smoke:raise ValueError('Compiler diagnostic cannot execute a battle')
    if is_development(m) and backend!='metal':raise ValueError('Development execution requires Metal; seal before CUDA verification')
    if not 1<=timeout<=180:raise ValueError('Timeout must be 1..180')
    if backend=='cuda' and os.name!='nt' and not smoke and not cpu_only:raise ValueError('CUDA transport requires Windows')
    if bool(linked_package)!=bool(linked_capture):raise ValueError('Both saved CUBIN package and capture required')
    linked=linked_package is not None
    if linked and (backend!='cuda' or smoke or cpu_only or not 1<=timeout<=60 or not original_workspace or compiler_only(m) or is_development(m)):raise ValueError('Saved CUBIN requires a sealed CUDA battle and1..60 seconds')
    if not smoke and not cpu_only:validate_generation_request(m)
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend=backend,
                                mode='cpu-only' if cpu_only else 'smoke' if smoke else 'gpu',status='preflight',gpu_retry_count=0,
                                **(dict(input_protocol=PREPARED_INPUT_PROTOCOL) if not cpu_only and not smoke else {})))
    try:
        if linked:
            request=dict(package=str(Path(linked_package).resolve()),capture=str(Path(linked_capture).resolve()))
            write(capture/'linked-artifact-request.json',request)
            with forbid_gpu():saved_linked_admission(m,request)
        # An extracted packet deliberately excludes compiler distributions.
        # Catch a missing Metal toolchain before expensive native preparation
        # and before consuming the exclusive GPU execution claim.
        if backend=='metal' and not smoke and not cpu_only:
            compiler_root=Path(os.environ.get('NIKKE_SLANG_ROOT',ROOT/f'.tools/slang-2026.20-{platform.system()}-{platform.machine()}')).resolve()
            compiler=compiler_root/'bin'/('slangc.exe' if os.name=='nt' else 'slangc')
            if not compiler.is_file():
                raise ValueError('Slang compiler missing: '+str(compiler)+'; specify --slang-root')
        if not smoke and not cpu_only:capture_storage_preflight(m,capture)
        if not linked and not smoke and not cpu_only:
            paired=backend=='cuda' and required_cuda_cache_preflight(m,capture)
            if not paired:required_generation_cache_preflight(m,capture)
        if not smoke and not cpu_only and SUITES[m['suite']].get('parent_oracle_reuse'):
            from portable_parent_oracles import ParentOracles
            parent_oracles=ParentOracles(m,capture)
        # Reject broken test payloads before expensive full native battles.
        # Both gates still complete before the exclusive GPU claim/start.
        cpu_test_groups(m,capture,smoke)
        options=dict(parent_oracles=parent_oracles) if parent_oracles is not None else {}
        if not cpu_only and not smoke:options['input_capture']=capture
        pre=(dict(passed=True,controller_only=True,input_count=0,native_oracles=0,gpu_calls=0)
             if smoke else cpu_preflight(m,**options))
        write(capture/'cpu.json',pre)
        if parent_oracles is not None:parent_oracles.check(verify_package(ROOT),capture)
        if cpu_only:
            write(capture/'result.json',dict(cpu_verified=True,gpu_calls=0,calculation_verified=False,preservation_verified=None,status='cpu-only'))
        else:
            # Durable exclusive claim prevents same-package/backend GPU retries, even after a crash.
            if not smoke:capture_storage_preflight(m,capture,prepared=True)
            if not smoke:
                claim=ROOT/('gpu-claimed-'+backend+'.json')
                with claim.open('x',encoding='utf-8') as stream:
                    json.dump(dict(capture=str(capture),package_id=m['package_id'],started_unix_ns=time.time_ns()),stream)
            if smoke and os.name=='nt':
                with patch.dict(os.environ,{'NIKKE_VALIDATION_JOB_MEMORY_MB':'2048'}):facts=run_job(capture,backend,timeout,original_workspace,smoke)
            elif linked:
                with patch.dict(os.environ,NIKKE_VALIDATION_JOB_MEMORY_MB='2048',NIKKE_CUDA_ARTIFACT='cubin'):
                    facts=run_job(capture,backend,timeout,original_workspace,smoke)
            else:facts=run_job(capture,backend,timeout,original_workspace,smoke)
            if not smoke:
                # Child publishes generated files before comparing; failed compilation may lack them.
                copy_generated(capture,m['suite'],partial=True)
                result=audit_capture(capture,verify_artifacts=False,record_comparison=True,**(dict(parent_oracles=parent_oracles) if parent_oracles is not None else {}))
            else:
                marker=load(capture/'smoke.json') if (capture/'smoke.json').exists() else {}
                smoke_ok=facts['passed']
                if os.name=='nt':
                    jobs=load(capture/'job.json')['records']
                    smoke_ok &= bool(len(jobs)==1 and jobs[0]['pre_gate_verified'] and not jobs[0]['inspection_error'] and jobs[0]['post_wait'] and jobs[0]['post_wait']['job_members']==[] and marker==dict(pid=jobs[0]['child_pid'],ppid=jobs[0]['wrapper_pid'],gpu_calls=0))
                    if smoke_ok:smoke_ok &= audit_native_smoke(capture,jobs[0]['child_pid'])
                result=dict(smoke_verified=bool(smoke_ok),gpu_calls=0,calculation_verified=False,preservation_verified=None,status='smoke')
            write(capture/'result.json',result)
        run=load(capture/'run.json');run.update(status='finished',finished_unix_ns=time.time_ns());write(capture/'run.json',run)
    except BaseException as error:
        write(capture/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_retries=0))
        run=load(capture/'run.json');run['status']='failed';write(capture/'run.json',run)
        raise
    finally:
        if parent_oracles is not None:parent_oracles.close()
        collect(capture,capture/'artifacts.json')
    return load(capture/'result.json')


def job_contained(capture,rows,*,memory_limit_bytes=None):
    if not (capture/'job.json').exists() or not rows:return False,None
    records=load(capture/'job.json')['records']
    if len(records)!=1:return False,None
    r=records[0];pre=r['pre_gate'];post=r['post_wait'];pid=r['child_pid']
    good=bool(r['pre_gate_verified'] and not r['inspection_error'] and pre and post
        and pre['child_pid']==post['child_pid']==pid
        and pre['child_ppid']==post['child_ppid']==r['wrapper_pid']
        and pre['job_members']==[pid] and post['job_members']==[]
        and bool(pre['child_creation_filetime_ticks'])
        and pre['child_creation_filetime_ticks']==post['child_creation_filetime_ticks']
        and all(row.get('pid')==pid for row in rows)
        and all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(rows,rows[1:]))
        and pre['observed_unix_ns']<=rows[0]['wall_time_ns']<=rows[-1]['wall_time_ns']<=post['observed_unix_ns'])
    if memory_limit_bytes is not None:
        good &= pre.get('job_memory_limit_bytes')==post.get('job_memory_limit_bytes')==memory_limit_bytes
    return bool(good),pid


MODULE_DRIVER_APIS=('cuInit','cuDeviceGet','cuDeviceGetName','cuCtxCreate_v2','cuModuleLoadData','cuModuleLoadDataEx','cuModuleGetFunction','cuModuleGetGlobal_v2','cuCtxDestroy_v2')


def module_child(m,capture,backend):
    """Exact cached PTX and shared module lifecycle; forbid every battle API."""
    if backend!='cuda' or is_development(m) or compiler_only(m):raise ValueError('Module check requires a sealed CUDA battle package')
    import portable_backend
    from portable_phase_audit import Journal,NativeLibrary
    journal=Journal(capture/'phases.jsonl');loader=portable_backend.C.WinDLL
    class DriverOnly:
        def __init__(self,driver):self.driver=driver
        def __getattr__(self,name):
            if name=='cuModuleLoadDataEx':
                native=getattr(self.driver,name)
                class CheckedLoader:
                    def __getattr__(self,key):return getattr(native,key)
                    def __setattr__(self,key,value):setattr(native,key,value)
                    def __call__(self,*args):
                        if level is None or args[2]!=1 or args[3][0]!=7 or args[4][0]!=(level or None):
                            raise ValueError('Driver JIT native arguments differ from requested configuration')
                        journal.emit('cuda_jit_native_options','verified',optimization_level=level,option=7)
                        return native(*args)
                return CheckedLoader()
            if name in MODULE_DRIVER_APIS:return getattr(self.driver,name)
            def forbidden(*args):
                journal.emit('cuda_module_forbidden_api','rejected',api=name)
                raise RuntimeError('Battle API forbidden in module check: '+name)
            return forbidden
    def library(name,*args,**kwargs):
        if str(name).replace('\\','/').rsplit('/',1)[-1].lower()!='nvcuda.dll':
            journal.emit('cuda_module_forbidden_library','rejected')
            raise RuntimeError('Only nvcuda.dll is allowed in module check; NVRTC forbidden')
        driver=journal.invoke('cuda_module_driver_load',loader,name,*args,**kwargs)
        return NativeLibrary(DriverOnly(driver),journal)
    original_compile=portable_backend.compile_cuda_artifact
    def cached(*args,**kwargs):
        artifact,receipt=journal.invoke('cuda_compile_artifact',original_compile,*args,**kwargs)
        journal.emit('cuda_compile_cache','verified',receipt=receipt);return artifact,receipt
    source=SUITES[m['suite']]['source']
    with patch.object(portable_backend.C,'WinDLL',library),patch.object(portable_backend,'compile_cuda_artifact',cached):
        outputs,hashes=journal.invoke('slang_build',portable_backend.build,source,'portableEvents')
        normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
        generated={k:normalized(p.read_bytes()) for k,p in outputs.items()}
        if hashes!=m['golden']['source_sha256'] or generated!=m['golden']['generated_normalized']:
            raise ValueError('Module inputs differ from the sealed Metal proof')
        plan=portable_backend.resident_plan(source,'portableEvents',outputs)
        copy_generated(capture,m['suite'])
        if plan:
            for path in outputs.values():
                (capture/('generated'+path.suffix+'.reflection.json')).write_bytes(Path(str(path)+'.reflection.json').read_bytes())
        value=os.environ.get('NIKKE_CUDA_JIT_OPT_LEVEL','')
        level=int(value) if value else None
        if value and (value not in tuple(str(i) for i in range(5))):raise ValueError('Invalid driver JIT optimization level')
        journal.emit('cuda_jit_configuration','verified',optimization_level=level)
        checked=journal.invoke('shared_cuda_module_check',portable_backend.inspect_cuda_module,outputs['cuda'],'portableEvents',resident=plan,jit_opt_level=level)
    copy_generated(capture,m['suite'])
    write(capture/'module.json',dict(source_sha256=hashes,generated_sha256={k:sha(p.read_bytes()) for k,p in outputs.items()},
          generated_normalized=generated,resident_runtime=plan,transport=checked))


def audit_module_capture(m,capture,*,verify_artifacts=True):
    audit_generation_capture(m,capture)
    if compiler_only(m):raise ValueError('Compiler diagnostic cannot load a CUDA module')
    from portable_phase_audit import valid_cache_hit
    run=load(capture/'run.json');facts=load(capture/'execution.json')
    if run.get('mode')!='module-only' or run['package_id']!=m['package_id'] or run['backend']!='cuda' or is_development(m):raise ValueError('Wrong module check capture')
    if type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60 or run['memory_limit_mb']!=2048:raise ValueError('Module check exceeds its bounded policy')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    rows=[];error=None;verified=False
    try:
        rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
        if any(r['stage'].startswith('nvrtc') or r['stage'].startswith('cuda_module_forbidden') or r['stage'].startswith('cu') and len(r['stage'])>2 and r['stage'][2].isupper() and r['stage'] not in MODULE_DRIVER_APIS for r in rows):raise ValueError('Forbidden module check operation')
        span=[(i,r) for i,r in enumerate(rows) if r['stage']=='shared_cuda_module_check']
        if [r['state'] for _,r in span]!=['entered','returned']:raise ValueError('Module check did not return')
        level=run.get('jit_optimization_level')
        if level is not None and (type(level) is not int or level not in range(5)):raise ValueError('Invalid recorded JIT level')
        configs=[r for r in rows if r['stage']=='cuda_jit_configuration']
        if len(configs)!=1 or configs[0].get('optimization_level')!=level:raise ValueError('JIT configuration mismatch')
        load_api='cuModuleLoadData' if level is None else 'cuModuleLoadDataEx'
        other_api='cuModuleLoadDataEx' if level is None else 'cuModuleLoadData'
        if any(r['stage']==other_api for r in rows):raise ValueError('Unexpected module loader')
        previous=-1;first_api=None
        for stage in ('cuInit','cuDeviceGet','cuDeviceGetName','cuCtxCreate_v2',load_api,'cuModuleGetFunction','cuModuleGetGlobal_v2','cuCtxDestroy_v2'):
            hits=[(i,r) for i,r in enumerate(rows) if r['stage']==stage]
            if len(hits)!=2 or hits[0][1]['state']!='entered' or hits[1][1]['state']!='returned' or hits[1][1].get('return_code')!=0 or hits[0][0]<=previous:raise ValueError('Module API return missing: '+stage)
            if first_api is None:first_api=hits[0][0]
            previous=hits[1][0]
        cached=[(i,r) for i,r in enumerate(rows) if valid_cache_hit(r)]
        if len(cached)!=1:raise ValueError('One verified compiler cache hit required')
        if not span[0][0]<cached[0][0]<first_api<=previous<span[1][0]:raise ValueError('Cache/module API order invalid')
        loaded=[(i,r) for i,r in enumerate(rows) if r['stage']=='cuda_module_driver_load']
        if [r['state'] for _,r in loaded]!=['entered','returned'] or not cached[0][0]<loaded[0][0]<loaded[1][0]<first_api:raise ValueError('Driver load must follow the verified cache hit')
        proof=load(capture/'module.json');t=proof['transport'];receipt=t['compile_artifact'];kind=receipt['identity']['artifact']
        if t.get('jit_optimization_level')!=level:raise ValueError('Module JIT receipt mismatch')
        native_options=[(i,r) for i,r in enumerate(rows) if r['stage']=='cuda_jit_native_options']
        if level is None:
            if native_options:raise ValueError('Unexpected native JIT options')
        else:
            calls=[i for i,r in enumerate(rows) if r['stage']=='cuModuleLoadDataEx']
            if len(native_options)!=1 or native_options[0][1].get('optimization_level')!=level or native_options[0][1].get('option')!=7 or not calls[0]<native_options[0][0]<calls[1]:raise ValueError('Native JIT options not verified')
        if kind!='ptx' or cached[0][1]['receipt']!=receipt:raise ValueError('Wrong module artifact receipt')
        from portable_backend import cuda_compile_options
        if receipt['identity']['options']!=cuda_compile_options('ptx'):raise ValueError('Wrong PTX compiler options')
        if receipt['key']!=sha(json.dumps(receipt['identity'],sort_keys=True,separators=(',',':')).encode()):raise ValueError('Wrong PTX cache key')
        normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
        if proof['source_sha256']!=m['golden']['source_sha256'] or proof['generated_normalized']!=m['golden']['generated_normalized']:raise ValueError('Module source baseline mismatch')
        for target,suffix in [('cuda','cu'),('metal','metal')]:
            raw=(capture/('generated.'+suffix)).read_bytes()
            if sha(raw)!=proof['generated_sha256'][target] or normalized(raw)!=proof['generated_normalized'][target]:raise ValueError('Generated module source mismatch')
        raw=(capture/'compiled.ptx').read_bytes()
        if len(raw)!=receipt['artifact_bytes'] or sha(raw)!=receipt['artifact_sha256'] or receipt['identity']['source_sha256']!=proof['generated_sha256']['cuda']:raise ValueError('Cached PTX bytes mismatch')
        from portable_backend import resident_plan
        paths={k:capture/('generated.'+suffix) for k,suffix in [('cuda','cu'),('metal','metal')]}
        plan=resident_plan(SUITES[m['suite']]['source'],'portableEvents',paths)
        if plan!=proof['resident_runtime']:raise ValueError('Module Runtime reflection mismatch')
        if plan:
            from portable_resident_layout import verify_cuda_layout_assertions
            verify_cuda_layout_assertions(paths['cuda'],plan)
        expected=48 if proof['resident_runtime'] else 32
        if t.get('constant_buffer_bytes')!=expected or t.get('module_verified') is not True or t.get('kernel_calls')!=0 or t.get('buffer_allocations')!=0 or t.get('calculation_verified') is not False:raise ValueError('Wrong module proof scope or ABI')
        verified=True
    except (ValueError,KeyError,OSError) as exc:error=str(exc)
    containment,pid=job_contained(capture,rows,memory_limit_bytes=2048*1024*1024)
    verified=bool(verified and facts['passed'] and containment)
    preservation=environment_preserved(capture,facts)
    return dict(mode='module-only',module_verified=verified,passed=verified and preservation is True,
        containment_verified=containment,preservation_verified=preservation,calculation_verified=False,
        kernel_calls=0 if not any(r['stage']=='cuLaunchKernel' for r in rows) else None,
        buffer_allocations=0 if not any(r['stage']=='cuMemAlloc_v2' for r in rows) else None,error=error,gpu_retry_count=0)


def module_capture(capture,timeout,original_workspace,jit_opt_level=None):
    if jit_opt_level is not None and (type(jit_opt_level) is not int or jit_opt_level not in range(5)):raise ValueError('Invalid driver JIT optimization level')
    if os.name!='nt':raise ValueError('Module check requires Windows')
    if type(timeout) is not int or not 1<=timeout<=60:raise ValueError('Module check budget must be1..60 seconds')
    if not original_workspace or not os.environ.get('NIKKE_CUDA_COMPILE_CACHE'):raise ValueError('Original workspace and dedicated compiler cache required')
    m=verify_package(ROOT)
    if is_development(m) or compiler_only(m):raise ValueError('Module check requires a sealed Metal battle package')
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend='cuda',mode='module-only',status='loading',jit_optimization_level=jit_opt_level,memory_limit_mb=2048,gpu_retry_count=0))
    try:
        with (ROOT/'module-claimed-cuda.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(package_id=m['package_id'],capture=str(capture)),stream)
        with patch.dict(os.environ,dict(NIKKE_CUDA_JIT_OPT_LEVEL='' if jit_opt_level is None else str(jit_opt_level),NIKKE_CUDA_ARTIFACT='ptx',NIKKE_CUDA_PTXAS_OPT_LEVEL='',NIKKE_CUDA_CACHE_REQUIRED='1',NIKKE_VALIDATION_JOB_MEMORY_MB='2048')):
            run_job(capture,'cuda',timeout,original_workspace,module_only=True)
        copy_generated(capture,m['suite'],partial=True)
        result=audit_module_capture(m,capture,verify_artifacts=False);write(capture/'result.json',result)
        run=load(capture/'run.json');run['status']='finished';write(capture/'run.json',run)
    except BaseException as exc:
        write(capture/'failure.json',dict(error=type(exc).__name__+': '+str(exc),kernel_calls=0))
        run=load(capture/'run.json');run['status']='failed';write(capture/'run.json',run);raise
    finally:collect(capture,capture/'artifacts.json')
    return result


def assembly_origin(m,source_package,source_capture,*,historical_compiler=False):
    """Re-audit the immutable upstream PTX producer, including its original Job."""
    source_package=Path(source_package);source_capture=Path(source_capture)
    producer=verify_package(source_package,historical_compiler=True) if historical_compiler else verify_package(source_package)
    if is_development(m) or is_development(producer) or (not historical_compiler and producer['golden']!=m['golden']):
        raise ValueError('Assembly requires the same sealed GPU/native baseline')
    run=load(source_capture/'run.json');facts=load(source_capture/'execution.json')
    if run.get('mode')!='compile-only' or run.get('artifact_kind')!='ptx' or run.get('memory_limit_mb')!=2048 or facts.get('cleanup_error') or facts.get('observation_error'):
        raise ValueError('Assembly requires a bounded successful PTX producer')
    result=audit_compile_capture(producer,source_capture)
    if not result.get('compiler_verified') or not result.get('containment_verified'):raise ValueError('Upstream PTX producer not verified')
    observation=load(source_capture/'observation.json')
    from windows_validation_observer import compare_snapshots
    comparison=compare_snapshots(observation['before'],observation['after'])
    if observation['comparison']!=comparison:raise ValueError('Producer observation mismatch')
    if comparison['missing_existing_processes']:raise ValueError('Producer lost an existing process')
    proof=load(source_capture/'compiler.json');receipt=proof['compile_artifact'];raw=(source_capture/'compiled.ptx').read_bytes()
    from portable_offline_assembler import validate_ptx
    ptx=validate_ptx(raw)
    if receipt['artifact_sha256']!=ptx['sha256'] or receipt['artifact_bytes']!=ptx['bytes']:raise ValueError('Producer PTX mismatch')
    origin=dict(schema=1,producer_package_id=producer['package_id'],producer_manifest_sha256=sha((source_package/'gpu-package.json').read_bytes()),
        producer_artifacts_sha256=sha((source_capture/'artifacts.json').read_bytes()),ptx=ptx,cache_key=receipt['key'],
        cuda_sha256=proof['generated_sha256']['cuda'],generated_normalized=proof['generated_normalized'],
        source_sha256=proof['source_sha256'],producer_compiler_verified=True,producer_containment_verified=True)
    if historical_compiler:
        origin.update(historical_compiler_source=True,current_battle_equivalence_verified=False)
    return origin,raw


def linked_object_origin(request):
    """Read-only audit of the saved object; never recompute its PTX/object."""
    import portable_partition_object as obj
    package=Path(request['object_package']).resolve();capture=Path(request['object_capture']).resolve()
    expected=request['object_sha256']
    if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):raise ValueError('Expected original object SHA256 required')
    producer=verify_package(package,historical_compiler=True)
    result=audit_partition_object_capture(producer,capture,module_object=True)
    facts=load(capture/'execution.json')
    if not result['object_verified'] or not result['containment_verified'] or facts['cleanup_error'] or facts['observation_error']:raise ValueError('Saved module object is not verified')
    from windows_validation_observer import compare_snapshots
    observation=load(capture/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
    if observation['comparison']!=comparison or comparison['missing_existing_processes']:raise ValueError('Saved object observation mismatch or lost process')
    proof=load(capture/'object.json');receipt=proof['receipt'];raw=(capture/'module.o').read_bytes();artifact=obj.validate_object(raw)
    if artifact!=receipt['artifact'] or artifact['sha256']!=expected:raise ValueError('Object differs from original recorded SHA256')
    claim=load(package/'module-object-claimed-cuda.json')
    if claim.get('package_id')!=producer['package_id'] or Path(claim.get('capture','')).resolve()!=capture or claim.get('origin')!=proof['origin']:raise ValueError('Saved module object claim mismatch')
    return dict(schema=1,purpose='diagnostic-module-link',input=artifact,object_package_id=producer['package_id'],
        object_manifest_sha256=sha((package/'gpu-package.json').read_bytes()),object_artifacts_sha256=sha((capture/'artifacts.json').read_bytes()),
        object_claim_sha256=sha((package/'module-object-claimed-cuda.json').read_bytes()),object_receipt=receipt,
        expected_object_sha256=expected,object_compiler_verified=True,object_containment_verified=True,
        current_battle_equivalence_verified=False),raw


def saved_linked_admission(m,request):
    """Independent full producer/object/link audit; never activates a compiler."""
    from portable_linked_artifact import admission
    package=Path(request['package']).resolve();capture=Path(request['capture']).resolve()
    linked=verify_package(package,historical_compiler=True)
    if not full_compiler(linked):raise ValueError('Saved CUBIN must originate in a full compiler package')
    result=audit_jit_link_capture(linked,capture,package_root=package)
    if not result['link_verified'] or not result['containment_verified']:raise ValueError('Saved CUBIN link chain is not verified')
    from windows_validation_observer import compare_snapshots
    observation=load(capture/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
    if observation['comparison']!=comparison or comparison['missing_existing_processes']:raise ValueError('Saved CUBIN link observation mismatch or missing process')
    proof=load(capture/'jit-link.json');link_request=load(capture/'object-request.json')
    object_capture=Path(link_request['object_capture']);object_request=load(object_capture/'object-request.json')
    producer=proof['origin']['object_receipt']['identity']['origin']['producer']
    compiler=load(Path(object_request['source_capture'])/'compiler.json')
    anchors=dict(package_id=linked['package_id'],manifest_sha256=sha((package/'gpu-package.json').read_bytes()),
        artifacts_sha256=sha((capture/'artifacts.json').read_bytes()),claim_sha256=sha((package/'jit-link-object-claimed-cuda.json').read_bytes()),link_receipt_key=proof['receipt']['key'])
    receipt=admission(m,linked,producer,compiler,proof['receipt'],anchors)
    return dict(receipt=receipt,artifact=str(capture/'jit-linked.cubin'))


@contextlib.contextmanager
def saved_linked_provider(m,capture,backend,journal):
    request_path=capture/'linked-artifact-request.json'
    if not request_path.exists():
        yield;return
    if backend!='cuda' or compiler_only(m) or is_development(m):raise ValueError('Saved CUBIN requires a sealed CUDA battle')
    import portable_backend
    from portable_linked_artifact import read_verified,STAGE
    with forbid_gpu():state=saved_linked_admission(m,load(request_path))
    journal.emit('cuda_linked_origin','verified',receipt=state['receipt'])
    calls=0
    def saved(source,*,artifact_kind=None):
        nonlocal calls
        if calls or (artifact_kind or portable_backend.cuda_artifact_kind())!='cubin':raise ValueError('One explicit saved CUBIN load required')
        calls+=1
        image,receipt=journal.invoke('cuda_linked_artifact',read_verified,state['receipt'],source,state['artifact'])
        Path(source).with_suffix('.cubin').write_bytes(image)
        journal.emit(STAGE,'verified',receipt=receipt)
        return image,receipt
    def forbidden(*args,**kwargs):raise RuntimeError('Live NVRTC compilation forbidden for saved CUBIN')
    with patch.object(portable_backend,'compile_cuda_source',saved),patch.object(portable_backend,'compile_cuda_artifact',forbidden):yield


def audit_saved_linked_artifact(m,capture,receipt):
    from portable_linked_artifact import read_verified
    state=saved_linked_admission(m,load(capture/'linked-artifact-request.json'))
    if state['receipt']!=receipt:raise ValueError('Saved CUBIN admission receipt changed')
    image,_=read_verified(receipt,capture/'generated.cu',state['artifact'])
    if image!=(capture/'compiled.cubin').read_bytes():raise ValueError('Saved CUBIN copied image changed')
    facts=load(capture/'execution.json')
    if type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60:raise ValueError('Saved CUBIN execution exceeds fixed budget')
    rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
    if any(r['stage'].startswith('nvrtc') or r['stage']=='cuda_compile_cache' for r in rows):raise ValueError('Unexpected live NVRTC in saved CUBIN execution')
    if [r.get('receipt') for r in rows if r['stage']=='cuda_linked_origin' and r['state']=='verified']!=[receipt]:raise ValueError('Saved CUBIN source admission phase mismatch')
    if [r['state'] for r in rows if r['stage']=='cuda_linked_artifact']!=['entered','returned']:raise ValueError('Incomplete saved CUBIN read phase')
    origin_index=next(i for i,r in enumerate(rows) if r['stage']=='cuda_linked_origin')
    read_indices=[i for i,r in enumerate(rows) if r['stage']=='cuda_linked_artifact']
    receipt_indices=[i for i,r in enumerate(rows) if r['stage']=='cuda_linked_artifact_receipt' and r['state']=='verified']
    if len(receipt_indices)!=1 or not origin_index<read_indices[0]<read_indices[1]<receipt_indices[0]:raise ValueError('Saved CUBIN admission phase order mismatch')
    return True


def jit_link_origin(request):
    if request.get('source_kind')!='jit-link':raise ValueError('JIT link source kind mismatch')
    origin,raw=linked_object_origin(request)
    return dict(origin,purpose='diagnostic-module-jit-link'),raw


def jit_link_child(m,capture,backend):
    if backend!='cuda' or is_development(m):raise ValueError('JIT link requires a non-development CUDA package')
    import ctypes as C
    import portable_partition_object as obj
    from portable_phase_audit import Journal
    request=load(capture/'object-request.json');journal=Journal(capture/'phases.jsonl');prefix='module_jit_link'
    dll=Path(request['nvjitlink']).resolve();loader=getattr(C,'WinDLL',None)
    def library(name,*args,**kwargs):
        basename=str(name).replace('\\','/').rsplit('/',1)[-1].lower()
        if basename not in ('kernel32','kernel32.dll') and Path(name).resolve()!=dll:
            journal.emit(prefix+'_forbidden_library','rejected');raise RuntimeError('Only the fixed JIT linker DLL and kernel32 are allowed')
        return loader(name,*args,**kwargs)
    with forbid_gpu(),patch.object(C,'WinDLL',library,create=True):
        origin,raw=jit_link_origin(request)
        if request['origin']!=origin:raise ValueError('JIT link origin changed after request')
        journal.emit(prefix+'_origin','verified',origin=origin)
        receipt=journal.invoke('shared_'+prefix,obj.run,capture,dll,raw,origin,journal=journal)
    write(capture/'jit-link.json',dict(origin=origin,receipt=receipt,calculation_verified=False,link_verified=True,kernel_calls=0))


def audit_jit_link_capture(m,capture,*,verify_artifacts=True,package_root=None):
    import portable_partition_object as obj
    import portable_jit_link_run as execution
    capture=Path(capture).resolve();run=load(capture/'run.json')
    if run.get('mode')!='jit-link-object-only' or run.get('backend')!='cuda' or run.get('package_id')!=m['package_id'] or is_development(m):raise ValueError('Wrong JIT link capture')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    if not (capture/'execution.json').exists():return dict(mode='jit-link-object-only',object_verified=False,link_verified=False,passed=False,containment_verified=False,preservation_verified=False,calculation_verified=False,kernel_calls=0,error='No bounded JIT execution receipt',gpu_retry_count=0)
    facts=load(capture/'execution.json')
    if run.get('memory_limit_mb')!=2048 or type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60:raise ValueError('JIT link exceeds fixed policy')
    rows=[];verified=False;error=None
    try:
        rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
        request=load(capture/'object-request.json');origin,raw=jit_link_origin(request)
        if request['origin']!=origin:raise ValueError('JIT request origin mismatch')
        tool=obj.validate_tool_path(origin,request['nvjitlink'])
        records=load(capture/'job.json')['records']
        if len(records)!=1:raise ValueError('One bounded JIT Job required')
        execution.audit_rows(rows,capture,origin,tool,records[0])
        if obj.object_paths(capture,origin)[0].read_bytes()!=raw:raise ValueError('JIT object bytes changed')
        claim=load((ROOT if package_root is None else Path(package_root))/'jit-link-object-claimed-cuda.json')
        if claim.get('package_id')!=m['package_id'] or Path(claim.get('capture','')).resolve()!=capture or claim.get('origin')!=origin:raise ValueError('JIT link consumed claim mismatch')
        verified=True
    except (KeyError,ValueError,OSError) as exc:error=str(exc)
    containment,pid=job_contained(capture,rows,memory_limit_bytes=2048*1024*1024)
    verified=bool(verified and facts['passed'] and containment);preservation=environment_preserved(capture,facts)
    return dict(mode='jit-link-object-only',object_verified=verified,link_verified=verified,passed=verified and preservation is True,
        containment_verified=containment,preservation_verified=preservation,calculation_verified=False,current_full_battle_verified=False,
        kernel_calls=0,error=error,gpu_retry_count=0)


def object_spec(kind):
    if kind not in ('focus','module','link','jit-link'):raise ValueError('Unknown diagnostic object kind')
    stem={'focus':'partition-object','module':'module-object','link':'link-object','jit-link':'jit-link-object'}[kind]
    return dict(mode=stem+'-only',claim=stem+'-claimed-cuda.json',flag=stem.replace('-','_')+'_only',
        prefix='module_jit_link' if kind=='jit-link' else 'module_link' if kind=='link' else 'partition_object',tool_key='nvjitlink' if kind=='jit-link' else 'nvlink' if kind=='link' else 'ptxas')


def partition_object_origin(m,request,*,module_object=False,link_object=False):
    import portable_partition_object as obj
    if module_object and link_object:raise ValueError('Diagnostic object modes are exclusive')
    kind='link' if link_object else 'module' if module_object else 'focus'
    if request.get('source_kind','focus')!=kind:raise ValueError('Diagnostic object source kind mismatch')
    if link_object:return linked_object_origin(request)
    producer,raw=assembly_origin(m,request['source_package'],request['source_capture'],historical_compiler=True)
    if module_object:return obj.module_origin(request['cache_entry'],request['phases'],producer,raw)
    return obj.origin(request['cache_entry'],request['phases'],request['candidate'],producer)


def partition_object_child(m,capture,backend,*,module_object=False,link_object=False):
    if backend!='cuda':raise ValueError('Focus object requires CUDA package')
    import ctypes as C
    import portable_partition_object as obj
    from portable_phase_audit import Journal
    request=load(capture/'object-request.json');journal=Journal(capture/'phases.jsonl')
    spec=object_spec('link' if link_object else 'module' if module_object else 'focus');prefix=spec['prefix']
    loader=getattr(C,'WinDLL',None)
    def library(name,*a,**k):
        if str(name).replace('\\','/').rsplit('/',1)[-1].lower() not in ('kernel32','kernel32.dll'):
            journal.emit(prefix+'_forbidden_library','rejected');raise RuntimeError('Driver/NVRTC DLL forbidden in focus object experiment')
        return loader(name,*a,**k)
    with forbid_gpu(),patch.object(C,'WinDLL',library,create=True):
        origin,raw=partition_object_origin(m,request,module_object=module_object,link_object=link_object)
        if origin!=request['origin']:raise ValueError('Focus object source changed after request')
        journal.emit(prefix+'_origin','verified',origin=origin)
        receipt=journal.invoke('shared_'+prefix,obj.run,capture,request[spec['tool_key']],raw,origin,journal=journal)
    write(capture/obj.object_profile(origin)['proof'],dict(origin=origin,receipt=receipt,calculation_verified=False,link_verified=link_object,kernel_calls=0))


def audit_partition_object_capture(m,capture,*,verify_artifacts=True,module_object=False,link_object=False,artifact_records=None):
    import portable_partition_object as obj
    import portable_offline_assembler as assembler
    capture=Path(capture).resolve();run=load(capture/'run.json')
    if module_object and link_object:raise ValueError('Diagnostic object modes are exclusive')
    spec=object_spec('link' if link_object else 'module' if module_object else 'focus');mode=spec['mode'];prefix=spec['prefix']
    if run.get('mode')!=mode or run.get('backend')!='cuda' or run.get('package_id')!=m['package_id'] or is_development(m):raise ValueError('Wrong diagnostic object capture')
    if not (capture/'execution.json').exists():
        if artifact_records is not None:check_records(capture,artifact_records)
        elif verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
        return dict(mode=mode,object_verified=False,passed=False,containment_verified=False,
            preservation_verified=False,partition_legal_verified=False,calculation_verified=False,link_verified=False,
            kernel_calls=0,error='No bounded execution receipt; preflight failure or incomplete capture',gpu_retry_count=0)
    facts=load(capture/'execution.json')
    if run.get('memory_limit_mb')!=2048 or type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60:raise ValueError('Focus object exceeds fixed policy')
    if artifact_records is not None:check_records(capture,artifact_records)
    elif verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    rows=[];verified=False;error=None
    try:
        rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
        operation=prefix+('_tool_run' if link_object else '_ptxas')
        expected=[(prefix+'_origin','verified'),('shared_'+prefix,'entered'),(prefix+'_tool','verified'),(prefix+'_input','verified'),(operation,'entered'),(prefix+'_child','verified'),(operation,'returned'),(prefix+'_receipt','verified'),('shared_'+prefix,'returned')]
        if [(r['stage'],r['state']) for r in rows]!=expected:raise ValueError('Incomplete or forbidden focus object journal')
        request=load(capture/'object-request.json');origin,raw=partition_object_origin(m,request,module_object=module_object,link_object=link_object)
        proof=load(capture/obj.object_profile(origin)['proof']);receipt=proof['receipt'];tool=obj.validate_tool_path(origin,request[spec['tool_key']])
        if request['origin']!=origin or proof['origin']!=origin or rows[0]['origin']!=origin:raise ValueError('Focus object origin mismatch')
        if rows[2]['tool']!=tool or rows[3]['input']!=origin['input'] or rows[4]['tool_sha256']!=tool['sha256']:raise ValueError('Focus object tool/input mismatch')
        input_path,partial_path,object_path=obj.object_paths(capture,origin)
        argv=[str(Path(request[spec['tool_key']]).resolve()),*obj.object_options(origin),str(input_path),'-o',str(partial_path)]
        if rows[4]['argv']!=argv or rows[6]['return_code']!=0:raise ValueError('Focus object command/return mismatch')
        snapshot=rows[5]['inspection']
        if not assembler.contained(snapshot,rows[5]['pid'],snapshot['child_pid']) or not rows[4]['wall_time_ns']<=snapshot['observed_unix_ns']<=rows[6]['wall_time_ns']:raise ValueError('Focus assembler child not observed inside Job')
        if link_object:
            from portable_native_process import validate_launch
            validate_launch(rows[5].get('native_launch'))
        ident=obj.identity(tool,origin)
        if receipt['identity']!=ident or receipt['key']!=sha(json.dumps(ident,sort_keys=True,separators=(',',':')).encode()):raise ValueError('Focus object identity mismatch')
        if rows[7]['receipt']!=receipt or input_path.read_bytes()!=raw:raise ValueError('Object receipt/PTX changed')
        if obj.validate_output(origin,object_path.read_bytes())!=receipt['artifact']:raise ValueError('Focus object ELF changed')
        if proof.get('calculation_verified') is not False or proof.get('link_verified') is not link_object or proof.get('kernel_calls')!=0:raise ValueError('Wrong diagnostic object proof scope')
        verified=True
    except (KeyError,ValueError,OSError) as exc:error=str(exc)
    containment,pid=job_contained(capture,rows,memory_limit_bytes=2048*1024*1024)
    verified=bool(verified and facts['passed'] and containment);preservation=environment_preserved(capture,facts)
    return dict(mode=mode,object_verified=verified,passed=verified and preservation is True,
        containment_verified=containment,preservation_verified=preservation,partition_legal_verified=False,
        calculation_verified=False,link_verified=bool(verified and link_object),kernel_calls=0,error=error,gpu_retry_count=0)


def recover_partition_object(experiment_package,capture,out,expected_partial_sha256):
    """CPU-only recovery receipt for a saved format-validation failure.

    Does not alter the old run, publish an object, consume a claim, or execute
    anything. Partial bytes remain anchored to the original artifact inventory.
    """
    import portable_partition_object as obj
    import portable_offline_assembler as assembler
    experiment_package=Path(experiment_package).resolve();capture=Path(capture).resolve();out=Path(out).resolve()
    request=load(capture/'object-request.json')
    readonly=[experiment_package,capture,*[Path(request[k]).resolve() for k in ('source_package','source_capture','candidate')],Path(request['cache_entry']).resolve().parent]
    if any(out.is_relative_to(root) for root in readonly):raise ValueError('Recovery receipt must be outside all original evidence')
    if out.exists():raise FileExistsError('Fresh recovery receipt required')
    result=dict(schema=1,purpose='saved-focus-object-cpu-recovery',saved_object_cpu_verified=False,passed=False,
        original_execution_passed=False,original_object_published=False,partition_legal_verified=False,
        link_verified=False,calculation_verified=False,nvrtc_calls=0,ptxas_calls=0,link_calls=0,driver_calls=0,gpu_calls=0)
    try:
        if len(expected_partial_sha256)!=64 or any(c not in '0123456789abcdef' for c in expected_partial_sha256):raise ValueError('Expected original partial SHA256 is required')
        m=verify_package(experiment_package)
        inventory=load(capture/'artifacts.json');records=inventory['files'];anchor=sha((capture/'artifacts.json').read_bytes());check_records(capture,records)
        run=load(capture/'run.json');facts=load(capture/'execution.json')
        if run.get('mode')!='partition-object-only' or run.get('backend')!='cuda' or run.get('package_id')!=m['package_id'] or run.get('status') not in ('failed','finished') or run.get('memory_limit_mb')!=2048:raise ValueError('Expected original failed focus experiment')
        if facts.get('passed') is not False or facts.get('timed_out') is not False or facts.get('child_exit_code')!=1 or facts.get('final_child_exit_code')!=1 or facts.get('error') is not None or facts.get('cleanup_error') is not None or facts.get('observation_error') is not None or facts.get('below_normal_priority') is not True or type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60:raise ValueError('Original bounded execution is incomplete or abnormal')
        if any((capture/name).exists() for name in ('focus.o','object.json')):raise ValueError('Recovery requires retained unpublished partial')
        if (capture/'result.json').exists() and load(capture/'result.json').get('object_verified') is not False:raise ValueError('Original result is not a failed object validation')
        rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
        expected=[('partition_object_origin','verified'),('shared_partition_object','entered'),('partition_object_tool','verified'),('partition_object_input','verified'),('partition_object_ptxas','entered'),('partition_object_child','verified'),('partition_object_ptxas','returned'),('partition_object_failure','raised'),('shared_partition_object','raised')]
        if [(r['stage'],r['state']) for r in rows]!=expected or any(r.get('exception')!='ValueError' for r in rows[7:]):raise ValueError('Not a complete saved object-validation failure')
        source,raw=partition_object_origin(m,request);tool=assembler.validate_tool(request['ptxas'])
        claim_path=experiment_package/'partition-object-claimed-cuda.json';claim_raw=claim_path.read_bytes();claim=json.loads(claim_raw)
        if claim.get('package_id')!=m['package_id'] or Path(claim.get('capture','')).resolve()!=capture or claim.get('origin')!=source:raise ValueError('Original consumed claim mismatch')
        if request['origin']!=source or rows[0]['origin']!=source or rows[2]['tool']!=tool or rows[3]['input']!=source['input'] or rows[4]['tool_sha256']!=tool['sha256'] or (capture/'focus.ptx').read_bytes()!=raw:raise ValueError('Saved object source/tool changed')
        argv=[str(Path(request['ptxas']).resolve()),*obj.OPTIONS,str(capture/'focus.ptx'),'-o',str(capture/'focus.o.partial')]
        if rows[4]['argv']!=argv or rows[6]['return_code']!=0:raise ValueError('Saved assembler command/return mismatch')
        snapshot=rows[5]['inspection']
        if not assembler.contained(snapshot,rows[5]['pid'],snapshot['child_pid']) or not rows[4]['wall_time_ns']<=snapshot['observed_unix_ns']<=rows[6]['wall_time_ns']:raise ValueError('Saved assembler child containment not verified')
        containment,pid=job_contained(capture,rows,memory_limit_bytes=2048*1024*1024)
        if not containment:raise ValueError('Original bounded Job not verified')
        artifact=obj.validate_object((capture/'focus.o.partial').read_bytes())
        if artifact['sha256']!=expected_partial_sha256:raise ValueError('Partial differs from original externally recorded SHA256')
        matches=[r for r in records if r['path']=='focus.o.partial']
        if matches and (matches[0]['bytes']!=artifact['bytes'] or matches[0]['sha256']!=artifact['sha256']):raise ValueError('Partial differs from original inventory')
        if not matches and inventory.get('raw_included') is not False:raise ValueError('Missing partial record without original metadata-only inventory')
        preservation=environment_preserved(capture,facts)
        check_records(capture,records)
        if sha((capture/'artifacts.json').read_bytes())!=anchor or claim_path.read_bytes()!=claim_raw:raise ValueError('Original inventory or claim changed during recovery')
        result.update(saved_object_cpu_verified=True,passed=preservation is True,containment_verified=True,preservation_verified=preservation,
            original_package_id=m['package_id'],original_artifacts_sha256=anchor,origin=source,tool=tool,options=obj.OPTIONS,
            artifact=dict(artifact,path=str(capture/'focus.o.partial')),partial_external_sha256=expected_partial_sha256,partial_in_original_inventory=bool(matches),compiler_return_verified=True,compiler_elapsed_seconds=rows[6]['elapsed_seconds'])
    except (ValueError,KeyError,OSError) as error:result['error']=type(error).__name__+': '+str(error)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return result


def object_capture(capture,timeout,original_workspace,request):
    if os.name!='nt':raise ValueError('Diagnostic native tool requires Windows')
    if type(timeout) is not int or not 1<=timeout<=60 or not original_workspace:raise ValueError('Diagnostic tool requires original workspace and1..60s')
    import portable_partition_object as obj
    kind=request['source_kind'];spec=object_spec(kind);m=verify_package(ROOT)
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend='cuda',mode=spec['mode'],status='preflight',memory_limit_mb=2048,gpu_retry_count=0))
    write(capture/'object-request.json',request)
    try:
        origin,_=jit_link_origin(request) if kind=='jit-link' else partition_object_origin(m,request,module_object=kind=='module',link_object=kind=='link');request['origin']=origin
        obj.validate_tool_path(origin,request[spec['tool_key']]);write(capture/'object-request.json',request)
        run=load(capture/'run.json');run['status']='processing';write(capture/'run.json',run)
        with (ROOT/spec['claim']).open('x',encoding='utf-8') as stream:json.dump(dict(package_id=m['package_id'],capture=str(capture),origin=origin),stream)
        with patch.dict(os.environ,NIKKE_VALIDATION_JOB_MEMORY_MB='2048'):
            run_job(capture,'cuda',timeout,original_workspace,**{spec['flag']:True})
        flags={'module_object':True} if kind=='module' else {'link_object':True} if kind=='link' else {}
        result=audit_jit_link_capture(m,capture,verify_artifacts=False) if kind=='jit-link' else audit_partition_object_capture(m,capture,verify_artifacts=False,**flags);write(capture/'result.json',result)
        run=load(capture/'run.json');run['status']='finished';write(capture/'run.json',run)
    except BaseException as exc:
        write(capture/'failure.json',dict(error=type(exc).__name__+': '+str(exc),kernel_calls=0));run=load(capture/'run.json');run['status']='failed';write(capture/'run.json',run);raise
    finally:collect(capture,capture/'artifacts.json')
    return result


def partition_object_capture(capture,timeout,original_workspace,source_package,source_capture,cache_entry,phases,candidate,ptxas,*,module_object=False):
    paths=dict(source_package=source_package,source_capture=source_capture,cache_entry=cache_entry,phases=phases,ptxas=ptxas)
    if not module_object:paths['candidate']=candidate
    elif candidate is not None:raise ValueError('Unmodified module experiment must not accept a partition candidate')
    request={name:str(Path(value).resolve()) for name,value in paths.items()};request['source_kind']='module' if module_object else 'focus'
    return object_capture(capture,timeout,original_workspace,request)


def link_object_capture(capture,timeout,original_workspace,object_package,object_capture_path,object_sha256,nvlink):
    request={name:str(Path(value).resolve()) for name,value in dict(object_package=object_package,object_capture=object_capture_path,nvlink=nvlink).items()}
    request.update(source_kind='link',object_sha256=object_sha256)
    return object_capture(capture,timeout,original_workspace,request)


def assemble_child(m,capture,backend):
    if backend!='cuda':raise ValueError('Standalone assembly requires CUDA package')
    import ctypes as C
    from portable_phase_audit import Journal
    import portable_offline_assembler as assembler
    journal=Journal(capture/'phases.jsonl');request=load(capture/'assembly-request.json')
    loader=getattr(C,'WinDLL',None)
    def library(name,*a,**k):
        if str(name).replace('\\','/').rsplit('/',1)[-1].lower() not in ('kernel32','kernel32.dll'):
            journal.emit('offline_assembly_forbidden_library','rejected');raise RuntimeError('Driver/NVRTC DLL forbidden in offline assembly')
        return loader(name,*a,**k)
    with forbid_gpu(),patch.object(C,'WinDLL',library,create=True):
        origin,raw=assembly_origin(m,request['source_package'],request['source_capture'])
        if origin!=request['origin']:raise ValueError('Upstream assembly input changed after request')
        journal.emit('assembly_origin','verified',origin=origin)
        receipt=journal.invoke('shared_offline_assembly',assembler.run,capture,request['ptxas'],raw,origin,journal=journal)
    write(capture/'assembly.json',dict(origin=origin,receipt=receipt,calculation_verified=False,kernel_calls=0))


def audit_assemble_capture(m,capture,*,verify_artifacts=True):
    import portable_offline_assembler as assembler
    capture=Path(capture).resolve()
    run=load(capture/'run.json');facts=load(capture/'execution.json')
    if run.get('mode')!='assemble-only' or run.get('backend')!='cuda' or run.get('package_id')!=m['package_id'] or is_development(m):raise ValueError('Wrong standalone assembly capture')
    if run.get('memory_limit_mb')!=2048 or type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60:raise ValueError('Standalone assembly exceeds fixed policy')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    rows=[];verified=False;error=None
    try:
        rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
        allowed={'assembly_origin','shared_offline_assembly','offline_ptxas_tool','offline_ptxas_input','offline_ptxas','offline_ptxas_child','offline_assembly_receipt'}
        if any(r['stage'] not in allowed for r in rows):raise ValueError('Forbidden or failed assembly operation')
        expected=[('assembly_origin','verified'),('shared_offline_assembly','entered'),('offline_ptxas_tool','verified'),('offline_ptxas_input','verified'),('offline_ptxas','entered'),('offline_ptxas_child','verified'),('offline_ptxas','returned'),('offline_assembly_receipt','verified'),('shared_offline_assembly','returned')]
        if [(r['stage'],r['state']) for r in rows]!=expected:raise ValueError('Incomplete or reordered assembly journal')
        request=load(capture/'assembly-request.json');origin,ptx=assembly_origin(m,request['source_package'],request['source_capture'])
        proof=load(capture/'assembly.json');receipt=proof['receipt'];identity=receipt['identity']
        if request['origin']!=origin or proof['origin']!=origin or rows[0]['origin']!=origin:raise ValueError('Assembly origin mismatch')
        tool=assembler.validate_tool(request['ptxas'])
        if rows[2]['tool']!=tool or rows[3]['input']!=origin['ptx'] or rows[4]['tool_sha256']!=tool['sha256']:raise ValueError('Assembly tool/input journal mismatch')
        argv=[str(Path(request['ptxas']).resolve()),*assembler.OPTIONS,str(capture/'input.ptx'),'-o',str(capture/'compiled.cubin.partial')]
        if rows[4]['argv']!=argv or rows[6]['return_code']!=0:raise ValueError('Assembler command/return mismatch')
        snapshot=rows[5]['inspection']
        if not assembler.contained(snapshot,rows[5]['pid'],snapshot['child_pid']) or not rows[4]['wall_time_ns']<=snapshot['observed_unix_ns']<=rows[6]['wall_time_ns']:raise ValueError('Assembler child not observed inside the validation Job')
        expected_identity=dict(schema=1,provider='offline-ptxas',artifact='cubin',tool=tool,options=assembler.OPTIONS,input=origin['ptx'],upstream_cache_key=origin['cache_key'],upstream_cuda_sha256=origin['cuda_sha256'])
        if identity!=expected_identity or receipt['key']!=sha(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()):raise ValueError('Assembly identity mismatch')
        if rows[7]['receipt']!=receipt or (capture/'input.ptx').read_bytes()!=ptx:raise ValueError('Assembly receipt/PTX changed')
        binary=(capture/'compiled.cubin').read_bytes()
        if not binary.startswith(b'\x7fELF') or len(binary)<64 or sha(binary)!=receipt['artifact_sha256'] or len(binary)!=receipt['artifact_bytes']:raise ValueError('Assembly ELF mismatch')
        if proof.get('calculation_verified') is not False or proof.get('kernel_calls')!=0:raise ValueError('Wrong assembly proof scope')
        verified=True
    except (KeyError,ValueError,OSError) as exc:error=str(exc)
    containment,pid=job_contained(capture,rows,memory_limit_bytes=2048*1024*1024)
    verified=bool(verified and facts['passed'] and containment)
    preservation=environment_preserved(capture,facts)
    return dict(mode='assemble-only',assembly_verified=verified,passed=verified and preservation is True,
        containment_verified=containment,preservation_verified=preservation,calculation_verified=False,
        kernel_calls=0,error=error,gpu_retry_count=0)


def assemble_capture(capture,timeout,original_workspace,source_package,source_capture,ptxas):
    if os.name!='nt':raise ValueError('Standalone assembly requires Windows')
    if type(timeout) is not int or not 1<=timeout<=60 or not original_workspace:raise ValueError('Standalone assembly requires original workspace and1..60s')
    m=verify_package(ROOT)
    origin,_=assembly_origin(m,source_package,source_capture)
    from portable_offline_assembler import validate_tool
    validate_tool(ptxas)
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend='cuda',mode='assemble-only',status='assembling',memory_limit_mb=2048,gpu_retry_count=0))
    request=dict(source_package=str(Path(source_package).resolve()),source_capture=str(Path(source_capture).resolve()),ptxas=str(Path(ptxas).resolve()),origin=origin)
    write(capture/'assembly-request.json',request)
    try:
        with (ROOT/'assembly-claimed-cuda.json').open('x',encoding='utf-8') as stream:json.dump(dict(package_id=m['package_id'],capture=str(capture),origin=origin),stream)
        with patch.dict(os.environ,NIKKE_VALIDATION_JOB_MEMORY_MB='2048',NIKKE_CUDA_ARTIFACT='cubin',NIKKE_CUDA_PTXAS_OPT_LEVEL='1'):
            run_job(capture,'cuda',timeout,original_workspace,assemble_only=True)
        result=audit_assemble_capture(m,capture,verify_artifacts=False);write(capture/'result.json',result)
        run=load(capture/'run.json');run['status']='finished';write(capture/'run.json',run)
    except BaseException as exc:
        write(capture/'failure.json',dict(error=type(exc).__name__+': '+str(exc),kernel_calls=0));run=load(capture/'run.json');run['status']='failed';write(capture/'run.json',run);raise
    finally:collect(capture,capture/'artifacts.json')
    return result


def compile_child(m,capture,backend):
    """Same compiler/cache as execution, with no CUDA driver admission."""
    if backend!='cuda' or is_development(m):raise ValueError('Compile-only requires a sealed CUDA package')
    if compiler_only(m) and (os.environ.get('NIKKE_CUDA_ARTIFACT')!='ptx' or os.environ.get('NIKKE_CUDA_PTXAS_OPT_LEVEL','')!='' or os.environ.get('NIKKE_VALIDATION_JOB_MEMORY_MB')!='2048'):
        raise ValueError('Compiler diagnostic child requires PTX and2GiB')
    import portable_backend
    from portable_phase_audit import Journal,observe
    journal=Journal(capture/'phases.jsonl')
    loader=getattr(portable_backend.C,'WinDLL',None)
    def guarded_library(name,*args,**kwargs):
        basename=str(name).replace('\\','/').rsplit('/',1)[-1].lower()
        if not basename.startswith('nvrtc') or not basename.endswith('.dll'):
            journal.emit('cuda_driver_load_forbidden','rejected');raise RuntimeError('Only the NVRTC compiler library is allowed')
        journal.emit('cuda_compiler_library','entered',name=basename)
        try:library=loader(name,*args,**kwargs)
        except BaseException as error:
            journal.emit('cuda_compiler_library','raised',name=basename,exception=type(error).__name__);raise
        journal.emit('cuda_compiler_library','loaded',name=basename)
        return library
    def forbidden(*a,**k):raise RuntimeError('GPU dispatch forbidden in compile-only mode')
    with patch.object(portable_backend.C,'WinDLL',guarded_library,create=True),patch.object(portable_backend,'execute',forbidden),patch.object(portable_backend,'execute_batches',forbidden),observe(portable_backend,journal):
        outputs,hashes=portable_backend.build(SUITES[m['suite']]['source'],'portableEvents')
        normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
        generated={k:normalized(p.read_bytes()) for k,p in outputs.items()}
        if hashes!=m['golden']['source_sha256'] or generated!=m['golden']['generated_normalized']:
            raise ValueError('Generated compiler inputs differ from the '+('fixed diagnostic source certificate' if compiler_only(m) else 'sealed Metal proof'))
        artifact,receipt=journal.invoke('shared_cuda_compile_only',portable_backend.compile_cuda_source,outputs['cuda'])
    copy_generated(capture,m['suite'])
    write(capture/'compiler.json',dict(source_sha256=hashes,generated_sha256={k:sha(p.read_bytes()) for k,p in outputs.items()},
        generated_normalized=generated,compile_artifact=receipt,gpu_calls=0,driver_load_calls=0,calculation_verified=False))


def audit_compile_capture(m,capture,*,verify_artifacts=True):
    audit_generation_capture(m,capture)
    run=load(capture/'run.json')
    if run.get('mode')!='compile-only' or run['package_id']!=m['package_id'] or run['backend']!='cuda':raise ValueError('Wrong compiler capture')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    facts=load(capture/'execution.json')
    if is_development(m) or type(facts['timeout_seconds']) is not int or not 1<=facts['timeout_seconds']<=60 or type(run['memory_limit_mb']) is not int or not 64<=run['memory_limit_mb']<=4096:raise ValueError('Compiler proof exceeds its bounded policy')
    if compiler_only(m) and (run['artifact_kind']!='ptx' or run['ptxas_level'] is not None or run['memory_limit_mb']!=2048):
        raise ValueError('Compiler diagnostic proof must use PTX and2GiB')
    rows=[];phase_error=None
    if (capture/'phases.jsonl').exists():
        for line in (capture/'phases.jsonl').read_text().splitlines():
            try:rows.append(json.loads(line))
            except json.JSONDecodeError:phase_error='Malformed or incomplete compiler phase journal';break
    complete=phase_error is None and [r['state'] for r in rows if r['stage']=='shared_cuda_compile_only']==['entered','returned']
    no_gpu=not any((r['stage'].startswith('cu') and len(r['stage'])>2 and r['stage'][2].isupper()) or r['stage'] in ('shared_gpu_execute','cuda_driver_load_forbidden') for r in rows)
    compiler=False;error=phase_error
    if (capture/'compiler.json').exists():
        try:
            c=load(capture/'compiler.json');receipt=c['compile_artifact'];kind=receipt['identity']['artifact']
            if kind!=run['artifact_kind']:raise ValueError('Compiler artifact kind mismatch')
            from portable_backend import cuda_compile_options
            if receipt['identity']['options']!=cuda_compile_options(kind,run['ptxas_level']):raise ValueError('Compiler options mismatch')
            if c['source_sha256']!=m['golden']['source_sha256'] or c['generated_normalized']!=m['golden']['generated_normalized']:raise ValueError('Compiler source baseline mismatch')
            normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
            for backend,suffix in [('cuda','cu'),('metal','metal')]:
                raw=(capture/('generated.'+suffix)).read_bytes()
                if sha(raw)!=c['generated_sha256'][backend] or normalized(raw)!=c['generated_normalized'][backend]:raise ValueError('Compiler generated bytes mismatch')
            artifact=(capture/('compiled.'+kind)).read_bytes()
            if sha(artifact)!=receipt['artifact_sha256'] or len(artifact)!=receipt['artifact_bytes']:raise ValueError('Compiler output mismatch')
            if kind=='cubin' and not artifact.startswith(b'\x7fELF'):raise ValueError('Compiler output is not ELF')
            if receipt['identity']['source_sha256']!=c['generated_sha256']['cuda']:raise ValueError('Compiler input mismatch')
            if receipt['key']!=sha(json.dumps(receipt['identity'],sort_keys=True,separators=(',',':')).encode()):raise ValueError('Compiler identity key mismatch')
            if [r['receipt'] for r in rows if r['stage']=='cuda_compile_cache' and r['state']=='verified']!=[receipt]:raise ValueError('Compiler receipt phase mismatch')
            compiler=True
        except (ValueError,KeyError,OSError) as exc:error=str(exc)
    containment,pid=job_contained(capture,rows,memory_limit_bytes=run['memory_limit_mb']*1024*1024)
    from portable_phase_audit import summarize
    phase=summarize(capture/'phases.jsonl')
    compiler=bool(compiler and facts['passed'] and complete and no_gpu and containment and (phase['nvrtc_compile_returned_success'] or phase['cuda_compile_cache_hit_verified']))
    preservation=environment_preserved(capture,facts)
    return dict(mode='compile-only',compiler_verified=compiler,passed=compiler and preservation is True,
        containment_verified=containment,preservation_verified=preservation,calculation_verified=False,
        gpu_calls=0 if no_gpu else None,driver_load_calls=0 if no_gpu else None,phase=phase,error=error,gpu_retry_count=0)


def compile_capture(capture,timeout,original_workspace,artifact_kind='cubin',ptxas_level=None,memory_limit_mb=2048):
    if os.name!='nt':raise ValueError('Compile-only requires Windows')
    if type(timeout) is not int or not 1<=timeout<=60:raise ValueError('Compile-only budget must be1..60 seconds')
    if type(memory_limit_mb) is not int or not 64<=memory_limit_mb<=4096:raise ValueError('Compile-only memory must be64..4096 MiB')
    from portable_backend import cuda_compile_options
    cuda_compile_options(artifact_kind,ptxas_level)
    if not original_workspace or not os.environ.get('NIKKE_CUDA_COMPILE_CACHE'):raise ValueError('Original workspace and dedicated compiler cache required')
    m=verify_package(ROOT)
    if is_development(m):raise ValueError('Compile-only requires a sealed Metal package')
    if compiler_only(m) and (artifact_kind!='ptx' or ptxas_level is not None or memory_limit_mb!=2048):
        raise ValueError('Compiler diagnostic requires PTX and the fixed2GiB budget')
    capture.mkdir(parents=True,exist_ok=False)
    write(capture/'run.json',dict(schema=SCHEMA,package_id=m['package_id'],backend='cuda',mode='compile-only',status='compiling',artifact_kind=artifact_kind,ptxas_level=ptxas_level,memory_limit_mb=memory_limit_mb,gpu_retry_count=0))
    try:
        with (ROOT/'compile-claimed-cuda.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(package_id=m['package_id'],capture=str(capture),artifact_kind=artifact_kind,ptxas_level=ptxas_level),stream)
        environment=dict(NIKKE_CUDA_ARTIFACT=artifact_kind,NIKKE_CUDA_PTXAS_OPT_LEVEL='' if ptxas_level is None else str(ptxas_level),NIKKE_VALIDATION_JOB_MEMORY_MB=str(memory_limit_mb))
        with patch.dict(os.environ,environment):run_job(capture,'cuda',timeout,original_workspace,compile_only=True)
        copy_generated(capture,m['suite'],partial=True)
        result=audit_compile_capture(m,capture,verify_artifacts=False);write(capture/'result.json',result)
        run=load(capture/'run.json');run['status']='finished';write(capture/'run.json',run)
    except BaseException as exc:
        write(capture/'failure.json',dict(error=type(exc).__name__+': '+str(exc),gpu_calls=0))
        run=load(capture/'run.json');run['status']='failed';write(capture/'run.json',run);raise
    finally:collect(capture,capture/'artifacts.json')
    return result


def environment_preserved(capture,facts,backend='cuda'):
    preservation=None if backend!='cuda' else False
    if (capture/'observation.json').exists():
        from windows_validation_observer import compare_snapshots
        o=load(capture/'observation.json')
        if 'before' in o and 'after' in o:
            comparison=compare_snapshots(o['before'],o['after'])
            if o.get('comparison')!=comparison:raise ValueError('Process comparison mismatch')
            immediate=0 <= o['after']['observed_unix_ns']-facts['wait_completed_unix_ns'] <= 30_000_000_000
            preservation=bool(immediate and not facts['observation_error'] and comparison['all_monitored_processes_preserved'] and comparison['identified_nikke_service_preservation_verified'])
    return preservation


def audit_capture(capture,verify_artifacts=True,*,record_comparison=False,parent_oracles=None):
    m=verify_package(ROOT)
    if parent_oracles is not None:
        if not record_comparison or load(capture/'run.json').get('mode')!='gpu':raise ValueError('Preflight oracles are only for the owning live battle audit')
        parent_oracles.check(m,capture)
    if load(capture/'run.json')['package_id']!=m['package_id']:raise ValueError('Capture belongs to another package')
    if verify_artifacts:check_records(capture,load(capture/'artifacts.json')['files'])
    if load(capture/'run.json').get('mode')=='jit-link-object-only':
        return audit_jit_link_capture(m,capture,verify_artifacts=verify_artifacts)
    if load(capture/'run.json').get('mode')=='link-object-only':
        return audit_partition_object_capture(m,capture,verify_artifacts=verify_artifacts,link_object=True)
    if load(capture/'run.json').get('mode')=='module-object-only':
        return audit_partition_object_capture(m,capture,verify_artifacts=verify_artifacts,module_object=True)
    if load(capture/'run.json').get('mode')=='partition-object-only':
        return audit_partition_object_capture(m,capture,verify_artifacts=verify_artifacts)
    if load(capture/'run.json').get('mode')=='assemble-only':
        return audit_assemble_capture(m,capture,verify_artifacts=verify_artifacts)
    if load(capture/'run.json').get('mode')=='module-only':
        return audit_module_capture(m,capture,verify_artifacts=verify_artifacts)
    if load(capture/'run.json').get('mode')=='compile-only':
        return audit_compile_capture(m,capture,verify_artifacts=verify_artifacts)
    if compiler_only(m) and load(capture/'run.json').get('mode')!='smoke':raise ValueError('Compiler diagnostic cannot certify a battle')
    if load(capture/'run.json').get('mode')=='replay':
        return audit_replay_capture(m,capture,verify_artifacts=verify_artifacts)
    protocol=load(capture/'run.json').get('input_protocol','legacy')
    if protocol not in ('legacy',PREPARED_INPUT_PROTOCOL):raise ValueError('Unknown transport input protocol')
    if protocol==PREPARED_INPUT_PROTOCOL:read_prepared_transport_input(m,capture)
    facts=load(capture/'execution.json')
    if load(capture/'run.json')['backend']=='metal' and (capture/'evidence.json').exists():
        from portable_metal_cache import verify as verify_metal_cache
        verify_metal_cache(load(capture/'evidence.json')['transport'],load(capture/'runtime.json'),
                           (capture/'generated.metal').read_bytes(),(ROOT/'scripts/run-metal-probe.swift').read_bytes())
    calc=False;error=None;first_difference=None
    if (capture/'readback.bin').exists():
        try:
            if record_comparison:
                from portable_phase_audit import Journal
                comparison=Journal(capture/'audit-phases.jsonl').invoke('shared_native_compare',compare_readback,m,capture,**(dict(parent_oracles=parent_oracles) if parent_oracles is not None else {}))
            else:comparison=compare_readback(m,capture)
            if record_comparison:write(capture/'comparison.json',comparison)
            calc=comparison['calculation_verified']
            first_difference=next(iter(comparison['mismatches']),None)
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
            if record_comparison:write(capture/'comparison.json',dict(calculation_verified=False,comparison_error=error))
    elif record_comparison:
        write(capture/'comparison.json',dict(calculation_verified=False,comparison_error='Missing readback.bin'))
    backend=load(capture/'run.json')['backend']
    if (capture/'evidence.json').exists():
        e=load(capture/'evidence.json')
        calc &= bool(e['backend']==backend and e['transport']['command_status']=='completed' and e['transport']['cases']==len(m['golden']['entries']))
    from portable_phase_audit import summarize,verify_cuda_trace
    phases=summarize(capture/'phases.jsonl')
    transport_ok=facts['passed']
    if backend=='cuda':
        transport_ok &= (phases['nvrtc_compile_returned_success'] or phases['cuda_compile_cache_hit_verified'] or phases['cuda_linked_artifact_observed']) and all(phases[k] for k in ('cuda_launch_returned_success','cuda_synchronize_returned_success','cuda_readback_returned_success'))
    preservation=None if backend!='cuda' else False
    preservation=environment_preserved(capture,facts,backend)
    containment=True if backend!='cuda' else False
    if backend=='cuda':
        phase_rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()] if (capture/'phases.jsonl').exists() else []
        containment,pid=job_contained(capture,phase_rows,memory_limit_bytes=2147483648 if (capture/'linked-artifact-request.json').exists() else None)
        containment &= verify_cuda_trace(phase_rows,pid=pid) if containment else False
    return dict(sealed=not is_development(m) and not compiler_only(m),purpose=m.get('purpose','sealed'),
                calculation_verified=bool(calc and transport_ok and containment),preservation_verified=preservation,
                passed=bool(calc and transport_ok and containment and (backend!='cuda' or preservation is True)),
                containment_verified=containment,comparison_error=error,first_difference=first_difference,phase=phases,gpu_retries=0,audit_gpu_calls=0)


def collect(capture,output):
    # Raw remains local; return the small evidence/report set by default.
    names=[p.relative_to(capture).as_posix() for p in capture.iterdir()
           if p.is_file() and p.suffix in ('.json','.jsonl','.log') and p.name not in ('artifacts.json',Path(output).name)]
    result=dict(schema=SCHEMA,files=file_records(capture,names),raw_included=False,gpu_calls=0)
    write(output,result);return result


def export_results(capture,output):
    receipt=load(capture/'artifacts.json');check_records(capture,receipt['files'])
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('artifacts.json',json.dumps(receipt,indent=2))
        for row in receipt['files']:z.writestr(row['path'],(capture/row['path']).read_bytes())
    return dict(bytes=Path(output).stat().st_size,sha256=sha(Path(output).read_bytes()),gpu_calls=0)


def import_results(archive,destination):
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate result members')
        for name in names:safe_name(name)
        receipt=json.loads(z.read('artifacts.json'))
        if set(names)!={'artifacts.json',*(r['path'] for r in receipt['files'])}:raise ValueError('Unexpected result members')
        for row in receipt['files']:
            b=z.read(row['path'])
            if len(b)!=row['bytes'] or sha(b)!=row['sha256']:raise ValueError('Result integrity mismatch')
        destination.mkdir(parents=True,exist_ok=False)
        for name in names:
            p=destination/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    check_records(destination,receipt['files'])
    return dict(files=len(receipt['files']),gpu_calls=0,remote_report_only=True)


def generation_capture(output,*,development=False,packet_stage=None):
    containment=None
    if os.name=='nt':
        from portable_generation_gate import verify_packet_generation
        containment=verify_packet_generation(ROOT,packet_stage,output)
    m=verify_package(ROOT)
    dev=is_development(m)
    if dev and not development:raise ValueError('Generation reuse requires a sealed source baseline; use --develop for generation-only preflight')
    if development and not dev:raise ValueError('--develop generation requires a development package')
    output.mkdir(parents=True,exist_ok=False)
    try:
        import portable_backend
        from portable_phase_audit import Journal,observe
        journal=Journal(output/'phases.jsonl')
        def forbidden(*args,**kwargs):raise RuntimeError('CUDA compilation or GPU execution forbidden in generation preparation')
        with patch.object(portable_backend,'execute',forbidden),patch.object(portable_backend,'execute_batches',forbidden),patch.object(portable_backend,'compile_cuda_source',forbidden),patch.object(portable_backend,'compile_cuda_artifact',forbidden),observe(portable_backend,journal):
            paths,hashes=portable_backend.build(SUITES[m['suite']]['source'],'portableEvents')
        normalized=module(ROOT/'research/summarize-portable-cross-gpu.py').normalized
        generated={k:normalized(p.read_bytes()) for k,p in paths.items()}
        if hashes!=m['golden']['source_sha256']:raise ValueError('Generation source differs from immutable package baseline')
        if not dev and generated!=m['golden']['generated_normalized']:raise ValueError('Generated cache outputs differ from sealed baseline')
        copy_generated(output,m['suite'])
        from portable_generation_cache import audit_receipt
        receipt=load(output/'generation-cache.json')
        verified=audit_receipt(receipt,hashes,{k:output/('generated.'+suffix) for k,suffix in [('cuda','cu'),('metal','metal')]})
        report=dict(package_id=m['package_id'],source_sha256=hashes,generated_normalized=generated,**verified,development_only=dev,sealed_generated_baseline_verified=not dev,calculation_verified=False,executable_battle_verified=False)
        if containment is not None:report['packet_containment']=containment
        write(output/'generation.json',report)
        return report
    except BaseException as error:
        write(output/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_calls=0));raise
    finally:collect(output,output/'artifacts.json')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    a=sub.add_parser('generation');a.add_argument('--packet-stage',type=Path);a.add_argument('--develop',action='store_true');a.add_argument('--out',type=Path,required=True);a.add_argument('--generation-cache',type=Path,required=True);a.add_argument('--require-generation-cache',action='store_true');a.add_argument('--slang-root',type=Path)
    for name in ('readback-index','readback-compare'):
        a=sub.add_parser(name);a.add_argument('--readback',type=Path,required=True);a.add_argument('--sha256',required=True);a.add_argument('--out',type=Path,required=True)
        if name=='readback-compare':a.add_argument('--index',type=Path,required=True);a.add_argument('--index-sha256',required=True)
        else:a.add_argument('--case-words',type=int,choices=(786432,1048576,1310720),default=786432)
    a=sub.add_parser('readback-retain');a.add_argument('--reference-capture',type=Path,required=True);a.add_argument('--reference-comparison-sha256',required=True);a.add_argument('--candidate-capture',type=Path,required=True);a.add_argument('--candidate-comparison-sha256',required=True);a.add_argument('--case-words',type=int,choices=(786432,1048576,1310720),default=786432);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('replay');a.add_argument('--source-package',type=Path,required=True);a.add_argument('--source-capture',type=Path,required=True);a.add_argument('--capture',type=Path,required=True);a.add_argument('--reference-migration',choices=['parts-cleared-v1','leftmost-rejection-domains-v1'])
    a=sub.add_parser('cache-check');a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('compiler-stats');a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--top',type=int,default=12);a.add_argument('--caller');a.add_argument('--runtime')
    a=sub.add_parser('ptx-stats');a.add_argument('--cache-entry',type=Path,required=True);a.add_argument('--phases',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--top',type=int,default=8);a.add_argument('--callgraph',action='store_true')
    a=sub.add_parser('ptx-partition');a.add_argument('--cache-entry',type=Path,required=True);a.add_argument('--phases',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--function');a.add_argument('--audit',action='store_true')
    a=sub.add_parser('compile');a.add_argument('--capture',type=Path,required=True);a.add_argument('--timeout',type=int,default=60)
    a.add_argument('--original-workspace',type=Path,required=True);a.add_argument('--artifact-kind',choices=('cubin','ptx'),default='cubin')
    a.add_argument('--ptxas-level',type=int,choices=range(4));a.add_argument('--memory-limit-mb',type=int,default=2048);a.add_argument('--slang-root',type=Path);a.add_argument('--compile-cache',type=Path);a.add_argument('--generation-cache',type=Path);a.add_argument('--require-generation-cache',action='store_true')
    a=sub.add_parser('assemble');a.add_argument('--capture',type=Path,required=True);a.add_argument('--source-package',type=Path,required=True);a.add_argument('--source-capture',type=Path,required=True);a.add_argument('--ptxas',type=Path,required=True);a.add_argument('--timeout',type=int,default=60);a.add_argument('--original-workspace',type=Path,required=True)
    a=sub.add_parser('partition-object-recover');a.add_argument('--experiment-package',type=Path,required=True);a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--partial-sha256',required=True)
    a=sub.add_parser('link-object');a.add_argument('--capture',type=Path,required=True);a.add_argument('--timeout',type=int,default=60);a.add_argument('--object-sha256',required=True)
    for name in ('object-package','object-capture','nvlink','original-workspace'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('jit-link-object');a.add_argument('--capture',type=Path,required=True);a.add_argument('--timeout',type=int,default=60);a.add_argument('--object-sha256',required=True)
    for name in ('object-package','object-capture','nvjitlink','original-workspace'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('recover-object');a.add_argument('--object-sha256',required=True)
    for name in ('source-package','source-capture','out'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('module-object');a.add_argument('--capture',type=Path,required=True);a.add_argument('--timeout',type=int,default=60)
    for name in ('source-package','source-capture','cache-entry','phases','ptxas','original-workspace'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('partition-object');a.add_argument('--capture',type=Path,required=True);a.add_argument('--timeout',type=int,default=60)
    for name in ('source-package','source-capture','cache-entry','phases','candidate','ptxas','original-workspace'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('module-check');a.add_argument('--jit-opt-level',type=int,choices=range(5));a.add_argument('--capture',type=Path,required=True);a.add_argument('--timeout',type=int,default=60)
    a.add_argument('--original-workspace',type=Path,required=True);a.add_argument('--slang-root',type=Path);a.add_argument('--compile-cache',type=Path,required=True);a.add_argument('--generation-cache',type=Path);a.add_argument('--require-generation-cache',action='store_true')
    a=sub.add_parser('seal');a.add_argument('--package-root',type=Path,required=True);a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--timeout',type=int,default=60)
    a=sub.add_parser('compiler-certificate');a.add_argument('--suite',choices=[config['compiler_baseline_suite'] for config in SUITES.values() if config.get('compiler_baseline_suite')],required=True);a.add_argument('--package-root',type=Path,required=True);a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--timeout',type=int,default=120)
    a=sub.add_parser('cases');a.add_argument('--suite',choices=SUITES,required=True)
    a=sub.add_parser('cache-probe');a.add_argument('--generated-cuda',type=Path,required=True);a.add_argument('--cuda-root',type=Path,required=True);a.add_argument('--compile-cache',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a.add_argument('--artifact-kind',choices=('ptx','cubin'),default='cubin');a.add_argument('--ptxas-level',type=int,choices=range(4));a.add_argument('--require-hit',action='store_true')
    a=sub.add_parser('consumer-audit');a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('inventory');a.add_argument('--out',type=Path,required=True)
    from portable_reference import REFERENCES
    a=sub.add_parser('saved-core-report-audit');a.add_argument('--report-root',type=Path,required=True);a.add_argument('--manifest-sha256',required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('layout-compare');a.add_argument('--before',type=Path,required=True);a.add_argument('--after',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('aimed-factor-compare');a.add_argument('--before',type=Path,required=True);a.add_argument('--after',type=Path,required=True);a.add_argument('--diagnostic',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('layout-check');a.add_argument('--out',type=Path)
    from portable_arena_specs import PROFILES as ARENA_PROFILES
    a=sub.add_parser('arena-check');a.add_argument('--profile',choices=ARENA_PROFILES,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('numeric-audit');a.add_argument('--out',type=Path,required=True);a.add_argument('--samples',type=int,default=512);a.add_argument('--profile',choices=('coordinate-binary64-v1','coordinate-unit-power-v1'),default='coordinate-binary64-v1')
    a=sub.add_parser('model-check');a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('reference');a.add_argument('--suite',choices=REFERENCES,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('phase-codegen');a.add_argument('--out',type=Path,required=True);a.add_argument('--slang-root',type=Path)
    a=sub.add_parser('sparsify-raw');a.add_argument('--block-size',type=int,choices=(4096,65536),default=65536);a.add_argument('--capture',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--apply',action='store_true')
    for storage_command in ('archive-raw','restore-raw'):
        a=sub.add_parser(storage_command);a.add_argument('--capture',type=Path,required=True);a.add_argument('--archive',type=Path,required=True)
        if storage_command=='archive-raw':a.add_argument('--remove-original',action='store_true')
    a=sub.add_parser('storage-check',help='CPU-only free-space budget check; does not archive or delete files')
    a.add_argument('--required-bytes',type=int,default=0);a.add_argument('--reserve-bytes',type=int,default=1024**3);a.add_argument('--path',type=Path,default=ROOT)
    a=sub.add_parser('_tests');a.add_argument('--capture',type=Path,required=True);a.add_argument('--smoke',action='store_true')
    a=sub.add_parser('package');a.add_argument('--suite',choices=SUITES,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--develop',action='store_true');a.add_argument('--case',action='append',default=[]);a.add_argument('--compact',action='store_true',help='Validated selected-suite Python payload; preserves GPU sources, fixtures and CPU/smoke groups')
    a=sub.add_parser('unpack');a.add_argument('--archive',type=Path,required=True);a.add_argument('--dest',type=Path,required=True)
    for name in ('run','_child'):
        a=sub.add_parser(name);a.add_argument('--capture',type=Path,required=True);a.add_argument('--backend',choices=('metal','cuda'),required=True);a.add_argument('--smoke',action='store_true')
        if name=='run':
            a.add_argument('--cpu-only',action='store_true');a.add_argument('--timeout',type=int,default=180);a.add_argument('--original-workspace',type=Path);a.add_argument('--slang-root',type=Path);a.add_argument('--generation-cache',type=Path);a.add_argument('--require-generation-cache',action='store_true')
            a.add_argument('--metal-pipeline-cache',type=Path);a.add_argument('--require-metal-pipeline-cache',action='store_true')
            a.add_argument('--require-cache',action='store_true');a.add_argument('--compile-cache',type=Path);a.add_argument('--ptxas-level',type=int,choices=range(4));a.add_argument('--artifact-kind',choices=('cubin','ptx'));a.add_argument('--linked-package',type=Path);a.add_argument('--linked-capture',type=Path)
        else:
            a.add_argument('--compile-only',action='store_true');a.add_argument('--module-only',action='store_true');a.add_argument('--assemble-only',action='store_true');a.add_argument('--partition-object-only',action='store_true');a.add_argument('--module-object-only',action='store_true');a.add_argument('--link-object-only',action='store_true');a.add_argument('--jit-link-object-only',action='store_true')
    for name in ('status','audit','collect','export'):
        a=sub.add_parser(name);a.add_argument('--capture',type=Path,required=True)
        if name in ('collect','export'):a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('import');a.add_argument('--archive',type=Path,required=True);a.add_argument('--dest',type=Path,required=True)
    a=sub.add_parser('audit-legacy');a.add_argument('--version',type=int,choices=(102,103,104),required=True)
    a=p.parse_args(argv)
    if (ROOT/'gpu-package.json').is_file():
        from portable_package_projection import check_command
        check_command(load(ROOT/'gpu-package.json').get('payload_projection'),a.command)
    if getattr(a,'require_generation_cache',False) and not getattr(a,'generation_cache',None):raise ValueError('--require-generation-cache requires --generation-cache')
    if getattr(a,'generation_cache',None):os.environ['NIKKE_SLANG_GENERATION_CACHE']=str(a.generation_cache.resolve())
    if getattr(a,'require_generation_cache',False):os.environ['NIKKE_SLANG_GENERATION_REQUIRED']='1'
    if hasattr(a,'capture'):a.capture=a.capture.resolve()
    if a.command=='list':
        result={}
        for name,config in SUITES.items():
            if not (ROOT/config['golden']).is_file():
                result[name]=dict(config,golden_source_ready=False,reason='No sealed golden');continue
            golden=load(ROOT/config['golden'])
            stale=[f for f,h in golden['source_sha256'].items() if not (ROOT/f).is_file() or sha((ROOT/f).read_bytes())!=h]
            result[name]=dict(config,golden_source_ready=not stale,stale_source_files=stale)
    elif a.command in ('readback-index','readback-compare'):
        from portable_readback_blocks import main as blocks_main
        args=['index' if a.command=='readback-index' else 'compare','--readback',str(a.readback),'--sha256',a.sha256,'--out',str(a.out)]
        if a.command=='readback-compare':args+=['--index',str(a.index),'--index-sha256',a.index_sha256]
        else:args+=['--case-words',str(a.case_words)]
        blocks_main(args);return
    elif a.command=='readback-retain':
        from portable_readback_blocks import main as blocks_main
        blocks_main(['retain','--reference-capture',str(a.reference_capture),'--reference-comparison-sha256',a.reference_comparison_sha256,'--candidate-capture',str(a.candidate_capture),'--candidate-comparison-sha256',a.candidate_comparison_sha256,'--case-words',str(a.case_words),'--out',str(a.out)]);return
    elif a.command=='replay':result=replay_capture(a.capture,a.source_package,a.source_capture,**(dict(reference_migration=a.reference_migration) if a.reference_migration else {}))
    elif a.command=='cache-check':result=check_compile_cache(a.capture,a.out)
    elif a.command=='compiler-stats':result=compiler_statistics(a.capture,a.out,top=a.top,caller=a.caller,runtime=a.runtime)
    elif a.command=='ptx-stats':result=ptx_statistics(a.cache_entry,a.phases,a.out,top=a.top,callgraph=a.callgraph)
    elif a.command=='ptx-partition':
        from portable_ptx_partition import saved_partition,audit_partition
        if a.audit and a.function:raise ValueError('Audit uses the stored focus; --function is creation only')
        result=audit_partition(a.cache_entry,a.phases,a.out) if a.audit else saved_partition(a.cache_entry,a.phases,a.out,a.function)
    elif a.command=='compile':
        if a.slang_root:os.environ['NIKKE_SLANG_ROOT']=str(a.slang_root.resolve())
        if a.compile_cache:os.environ['NIKKE_CUDA_COMPILE_CACHE']=str(a.compile_cache.resolve())
        result=compile_capture(a.capture,a.timeout,a.original_workspace,a.artifact_kind,a.ptxas_level,a.memory_limit_mb)
    elif a.command=='partition-object-recover':
        with forbid_gpu():result=recover_partition_object(a.experiment_package,a.capture,a.out,a.partial_sha256)
    elif a.command=='link-object':result=link_object_capture(a.capture,a.timeout,a.original_workspace,a.object_package,a.object_capture,a.object_sha256,a.nvlink)
    elif a.command=='jit-link-object':
        request=dict(source_kind='jit-link',object_package=str(a.object_package.resolve()),object_capture=str(a.object_capture.resolve()),object_sha256=a.object_sha256,nvjitlink=str(a.nvjitlink.resolve()))
        result=object_capture(a.capture,a.timeout,a.original_workspace,request)
    elif a.command=='module-object':result=partition_object_capture(a.capture,a.timeout,a.original_workspace,a.source_package,a.source_capture,a.cache_entry,a.phases,None,a.ptxas,module_object=True)
    elif a.command=='partition-object':result=partition_object_capture(a.capture,a.timeout,a.original_workspace,a.source_package,a.source_capture,a.cache_entry,a.phases,a.candidate,a.ptxas)
    elif a.command=='assemble':result=assemble_capture(a.capture,a.timeout,a.original_workspace,a.source_package,a.source_capture,a.ptxas)
    elif a.command=='module-check':
        if a.slang_root:os.environ['NIKKE_SLANG_ROOT']=str(a.slang_root.resolve())
        os.environ['NIKKE_CUDA_COMPILE_CACHE']=str(a.compile_cache.resolve())
        result=module_capture(a.capture,a.timeout,a.original_workspace,a.jit_opt_level)
    elif a.command=='recover-object':
        from portable_object_recovery import recover
        with forbid_gpu():
            verify_package(ROOT)
            result=recover(SimpleNamespace(**globals()),a.source_package,a.source_capture,a.out,a.object_sha256)
    elif a.command=='seal':result=seal_development(a.package_root,a.capture,a.out,timeout=a.timeout)
    elif a.command=='compiler-certificate':
        with forbid_gpu():result=make_compiler_certificate(a.suite,a.package_root,a.capture,a.out,timeout=a.timeout)
    elif a.command=='cases':
        with forbid_gpu():
            entries,_=prepare_entries(open_suite(dict(suite=a.suite)),dict(purpose='development'))
        result=dict(suite=a.suite,cases=[row[0] for row in entries],gpu_calls=0)
    elif a.command=='inventory':
        if a.out.exists():raise ValueError('Inventory output already exists')
        inventory=module(ROOT/'research/audit-world-roster-input.py').main(destination=str(a.out.resolve()),quiet=True)
        result={k:inventory[k] for k in ('profile_count','packed_profiles','packed_base','forbidden_calls','classification')}
        result['report']=str(a.out.resolve());result['priority_categories']=len(inventory['priorities'])
        result['work_lane_counts']={name:len(indexes) for name,indexes in inventory['work_lanes'].items()}
    elif a.command=='saved-core-report-audit':
        if a.out.exists():raise ValueError('Saved report audit output already exists')
        from portable_saved_core_report import audit
        result=audit(a.report_root,load(ROOT/SUITES['damage-accum-core']['golden']),module(ROOT/'research/summarize-portable-cross-gpu.py').normalized,a.manifest_sha256)
        write(a.out,result)
    elif a.command=='layout-compare':
        from portable_scratch_layout_migration import compare_captures
        receipt=compare_captures(ROOT,a.before,a.after);write(a.out,receipt)
        result={k:v for k,v in receipt.items() if k!='rows'}
    elif a.command=='aimed-factor-compare':
        from portable_aimed_factor_retention import compare_captures
        if a.out.exists():raise ValueError('Saved-result audit output already exists')
        with forbid_gpu():receipt=compare_captures(ROOT,a.before,a.after,a.diagnostic)
        with a.out.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
        result={k:v for k,v in receipt.items() if k!='changed_memo_rows'}
    elif a.command=='arena-check':
        from portable_arena_specs import audit_live_sources,audit_profile
        if a.out.exists():raise ValueError('Arena audit output already exists')
        with forbid_gpu():result={**audit_live_sources(ROOT),**audit_profile(a.profile)}
        write(a.out,result)
    elif a.command=='numeric-audit':
        if a.profile=='coordinate-unit-power-v1':
            from coordinate_power_accuracy import audit as numeric_audit
        else:
            from coordinate_numeric_accuracy import audit as numeric_audit
        if a.out.exists():raise ValueError('Numeric accuracy audit output already exists')
        with forbid_gpu():result=numeric_audit(ROOT,a.samples)
        with a.out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    elif a.command=='model-check':
        from portable_coordinate_frontier import verify as audit_frontier
        if a.out.exists():raise ValueError('Model audit output already exists')
        with forbid_gpu():result=audit_frontier(ROOT)
        with a.out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    elif a.command=='layout-check':
        from portable_specs import LIMITS
        from portable_scratch_layout import audit_sources
        result=audit_sources(ROOT,LIMITS)
        if a.out:write(a.out,result)
    elif a.command=='consumer-audit':
        from portable_missing_consumer_audit import verify as audit_consumers
        if a.out.exists():raise ValueError('Consumer audit output already exists')
        with forbid_gpu():result=audit_consumers(ROOT)
        with a.out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    elif a.command=='reference':
        from portable_reference import run_reference
        result=run_reference(a.suite,a.out,write=write,forbid_gpu=forbid_gpu)
    elif a.command=='generation':
        if a.slang_root:os.environ['NIKKE_SLANG_ROOT']=str(a.slang_root.resolve())
        result=generation_capture(a.out,development=a.develop,packet_stage=a.packet_stage)
    elif a.command=='phase-codegen':
        m=verify_package(ROOT)
        from portable_backend import source_hashes
        from portable_phase_codegen import generate
        with forbid_gpu():
            report=generate(ROOT,SUITES[m['suite']]['source'],a.out,package_id=m['package_id'],source_hashes=source_hashes,compiler_root=a.slang_root)
        result={k:report[k] for k in ('passed','package_id','calculation_verified','executable_battle_verified','gpu_calls','nvrtc_calls','driver_calls','kernel_calls','elapsed_seconds')}
        result['report']=str(a.out.resolve()/'report.json')
    elif a.command=='sparsify-raw':
        from portable_sparse_raw import sparsify_raw
        result=sparsify_raw(a.capture,a.out,check_records,apply=a.apply,block_size=a.block_size)
    elif a.command=='storage-check':
        from portable_capture_storage import space_status
        result=dict(space_status(a.path,a.required_bytes,reserve=a.reserve_bytes),gpu_calls=0,calculation_verified=False,scope='Free-space budget only; no archive integrity or cleanup')
    elif a.command=='archive-raw':
        from portable_capture_storage import archive_raw
        result=archive_raw(a.capture,a.archive,check_records,remove_original=a.remove_original)
    elif a.command=='restore-raw':
        from portable_capture_storage import restore_raw
        result=restore_raw(a.capture,a.archive,check_records)
    elif a.command=='cache-probe':result=cache_probe(a.generated_cuda,a.cuda_root,a.compile_cache,a.out,artifact_kind=a.artifact_kind,ptxas_level=a.ptxas_level,require_hit=a.require_hit)
    elif a.command=='package':result=make_package(a.suite,a.out,develop=a.develop,cases=a.case,compact=a.compact)
    elif a.command=='unpack':result=dict(package_id=unpack(a.archive,a.dest))
    elif a.command=='run':
        if a.backend!='metal' and (a.metal_pipeline_cache or a.require_metal_pipeline_cache):raise ValueError('Metal pipeline settings require Metal backend')
        if a.require_metal_pipeline_cache and not a.metal_pipeline_cache:raise ValueError('--require-metal-pipeline-cache requires --metal-pipeline-cache')
        if a.metal_pipeline_cache:os.environ['NIKKE_METAL_PIPELINE_CACHE']=str(a.metal_pipeline_cache.resolve())
        if a.require_metal_pipeline_cache:os.environ['NIKKE_METAL_PIPELINE_REQUIRED']='1'
        if (a.linked_package or a.linked_capture) and (a.require_cache or a.compile_cache or a.ptxas_level is not None or a.artifact_kind):raise ValueError('Saved CUBIN and live NVRTC/cache settings are exclusive')
        if a.backend!='cuda' and (a.require_cache or a.compile_cache or a.ptxas_level is not None or a.artifact_kind):raise ValueError('CUDA compiler settings require CUDA backend')
        if a.slang_root:os.environ['NIKKE_SLANG_ROOT']=str(a.slang_root.resolve())
        if a.compile_cache:os.environ['NIKKE_CUDA_COMPILE_CACHE']=str(a.compile_cache.resolve())
        if a.require_cache:os.environ['NIKKE_CUDA_CACHE_REQUIRED']='1'
        if a.ptxas_level is not None:os.environ['NIKKE_CUDA_PTXAS_OPT_LEVEL']=str(a.ptxas_level)
        if a.artifact_kind:os.environ['NIKKE_CUDA_ARTIFACT']=a.artifact_kind
        result=run_capture(a.capture,a.backend,a.timeout,a.original_workspace,a.smoke,a.cpu_only,**(dict(linked_package=a.linked_package,linked_capture=a.linked_capture) if a.linked_package or a.linked_capture else {}))
    elif a.command=='_tests':
        from portable_cpu_tests import run_groups,complete
        from portable_phase_audit import Journal
        m=Journal(a.capture/'preparation.jsonl').invoke('cpu_worker_verify_package',verify_package,ROOT)
        patterns=SMOKE_TESTS if a.smoke else SUITES[m['suite']]['tests']
        rows=run_groups(ROOT,a.capture,patterns,write)
        print(json.dumps(dict(cpu_tests_verified=complete(rows,patterns),groups=len(rows),gpu_calls=0)))
        if not complete(rows,patterns):raise SystemExit(1)
        return
    elif a.command=='_child':
        # Generated source copies are captured before comparison, including a mismatch.
        child(a.capture,a.backend,a.smoke,a.compile_only,a.module_only,a.assemble_only,a.partition_object_only,a.module_object_only,a.link_object_only,a.jit_link_object_only);return
    elif a.command=='audit':result=audit_capture(a.capture)
    elif a.command=='status':result=capture_status(a.capture)
    elif a.command=='collect':result=collect(a.capture,a.out)
    elif a.command=='export':result=export_results(a.capture,a.out)
    elif a.command=='import':result=import_results(a.archive,a.dest)
    else:
        # Historical fixed reports remain supported by their existing sealers.
        runpy.run_path(str(ROOT/f'research/seal-world-v{a.version}-cuda.py'),run_name='__main__');return
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.command=='partition-object-recover':
        if not result.get('saved_object_cpu_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is not True:raise SystemExit(2)
        return
    if result.get('mode') in ('partition-object-only','module-object-only','link-object-only','jit-link-object-only','recover-object-only'):
        if not result.get('object_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is not True:raise SystemExit(2)
        return
    if result.get('mode')=='assemble-only':
        if not result.get('assembly_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is False:raise SystemExit(2)
        return
    if result.get('mode')=='module-only':
        if not result.get('module_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is False:raise SystemExit(2)
        return
    if a.command=='compile' or result.get('mode')=='compile-only':
        if not result.get('compiler_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is False:raise SystemExit(2)
        return
    if a.command=='storage-check':
        if not result['passed']:raise SystemExit(2)
        return
    if a.command=='cache-probe':
        if not result['passed']:raise SystemExit(1)
        return
    if a.command=='arena-check':
        if not result['address_plan_verified']:raise SystemExit(1)
        return
    if a.command in ('run','audit','replay'):
        if result.get('cpu_verified') or result.get('smoke_verified'):return
        if not result.get('calculation_verified'):raise SystemExit(1)
        if result.get('preservation_verified') is False:raise SystemExit(2)


if __name__=='__main__':main()
