"""Backend-independent lifecycle operation catalog, independent of character names.

Adding a character using these operations changes data only. A new mechanic
needs an explicit operation, CPU handler, GPU handler and ordering witnesses.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

@dataclass(frozen=True)
class LifecycleSpec:
    key: str
    depends: tuple = ()
    activation_stat: int | None = None
    gpu_activate: str | None = None
    needs_resolved_targets: bool = True
    gpu_retire: str | None = None
    gpu_before_heal: str | None = None
    applied_event: int | None = None
    cpu_phase: str | None = None
    additional_stats: tuple = ()
    gpu_prepare: str | None = None
    current_instance: bool = False
    initial_hp_stats: tuple = ()
    any_instance: bool = False

SPECS=(
    LifecycleSpec('enemy_recipients',cpu_phase='prepare_activation',current_instance=True,any_instance=True),
    LifecycleSpec('attack_groups',cpu_phase='impact'),
    LifecycleSpec('staged_dot',cpu_phase='periodic_prepare'),
    LifecycleSpec('periodic_sources',cpu_phase='instant'),
    LifecycleSpec('periodic_source_legacy_adapter',depends=('periodic_sources',),cpu_phase='instant'),
    LifecycleSpec('decoy',activation_stat=72,gpu_activate='build_decoy',cpu_phase='protection_activate',current_instance=True),
    LifecycleSpec('shield',activation_stat=45,gpu_activate='build_shield',applied_event=18,cpu_phase='protection_activate',current_instance=True),
    LifecycleSpec('overheal_storage',activation_stat=74,gpu_activate='build_heal_storage',cpu_phase='activate',current_instance=True),
    LifecycleSpec('healing_share',depends=('overheal_storage',),cpu_phase='heal_plan'),
    LifecycleSpec('healing_charge',depends=('healing_share',),activation_stat=76,
                  gpu_activate='build_heal_charge',needs_resolved_targets=False,
                  gpu_retire='retire_heal_charge',gpu_before_heal='collect_heal_charge',cpu_phase='activate',current_instance=True),
    LifecycleSpec('damage_accumulation',depends=('healing_charge',),activation_stat=81,
                  additional_stats=(82,),gpu_activate='build_damage_accum',
                  needs_resolved_targets=False,cpu_phase='activate',current_instance=True),
    LifecycleSpec('max_hp_snapshot',activation_stat=84,gpu_activate='build_max_hp_snapshot',
                  cpu_phase='activate',current_instance=True),
    LifecycleSpec('base_stat_copy',activation_stat=85,additional_stats=(86,),
                  gpu_prepare='prepare_base_copy',gpu_activate='build_base_copy',
                  needs_resolved_targets=False,cpu_phase='prepare_activation',current_instance=True,initial_hp_stats=(86,)),
    LifecycleSpec('target_hit_counter',activation_stat=87,gpu_prepare='prepare_target_counter',
                  needs_resolved_targets=False,cpu_phase='prepare_activation',current_instance=True),
)

def ordered_specs(specs=SPECS):
    found={};ordered=[];stat_codes=set()
    for spec in specs:
        if not re.fullmatch('[a-z][a-z0-9_]*',spec.key):raise ValueError('Invalid operation key')
        if spec.key in found:raise ValueError('Duplicate lifecycle operation: '+spec.key)
        if not isinstance(spec.additional_stats,tuple):raise ValueError('Additional state stats must be immutable')
        if type(spec.current_instance) is not bool:raise ValueError('Invalid lifecycle instance policy')
        codes=((spec.activation_stat,) if spec.activation_stat is not None else ())+spec.additional_stats
        if not isinstance(spec.initial_hp_stats,tuple) or len(set(spec.initial_hp_stats))!=len(spec.initial_hp_stats) or any(type(code) is not int or code not in codes for code in spec.initial_hp_stats):raise ValueError('Invalid initialized-HP stat policy')
        for code in codes:
            if type(code) is not int or code in stat_codes:raise ValueError('Duplicate/invalid state stat')
            stat_codes.add(code)
        if type(spec.any_instance) is not bool or spec.any_instance and codes:raise ValueError('Generic instance hooks cannot bind a state stat')
        if spec.any_instance and (spec.gpu_activate or spec.gpu_prepare):raise ValueError('Generic GPU instance hooks require an executor binding')
        if (spec.gpu_activate or spec.gpu_prepare or spec.current_instance) and not codes and not spec.any_instance:raise ValueError('GPU activation requires state stats')
        for name in (spec.gpu_prepare,spec.gpu_activate,spec.gpu_retire,spec.gpu_before_heal):
            if name is not None and not re.fullmatch('[a-z][a-z0-9_]*',name):raise ValueError('Invalid GPU handler name')
        missing=set(spec.depends)-found.keys()
        if missing:raise ValueError('Missing or unordered lifecycle dependencies: '+str(sorted(missing)))
        found[spec.key]=spec;ordered.append(spec)
    return tuple(ordered)


BEGIN='// BEGIN GENERATED LIFECYCLE\n'
END='// END GENERATED LIFECYCLE\n'
