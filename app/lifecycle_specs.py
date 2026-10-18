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

def render_cuda():
    """Only registered state hooks; numerical rules stay in their own handlers."""
    specs=ordered_specs()
    lines=['// Generated from lifecycle_specs.py; do not hand-edit.']
    initial_hp=[code for spec in specs for code in spec.initial_hp_stats]
    initial_hp_match='||'.join(f'q[2]=={code}' for code in initial_hp) or '0'
    lines += [f'__device__ int lifecycle_init_hp(const double* q){{return q[1]==0&&({initial_hp_match});}}']
    lines += ['__device__ int lifecycle_instance(const double* e,State* s,int r,int uid){',
              ' if(r<0)return -1;const double* q=effect(e,s,r);']
    for spec in specs:
        if spec.current_instance and not spec.any_instance:
            codes=((spec.activation_stat,) if spec.activation_stat is not None else ())+spec.additional_stats
            match='||'.join(f'q[2]=={code}' for code in codes)
            lines.append(f' if(q[1]==0&&({match}))return s->alive[r]&&s->entry_seq[r]==uid?r:-1;')
    lines += [' return first_instance(e,s,s->definition[r]);','}']
    lines += [f'__device__ void {s.gpu_prepare}(const double*,const double*,int,State*,int,int);' for s in specs if s.gpu_prepare]
    lines += ['__device__ void lifecycle_prepare(const double* c,const double* e,int ne,State* s,int r,int full){',
              ' const double* q=effect(e,s,r);']
    for spec in specs:
        if spec.gpu_prepare:
            codes=((spec.activation_stat,) if spec.activation_stat is not None else ())+spec.additional_stats
            match='||'.join(f'q[2]=={code}' for code in codes)
            lines.append(f' if(q[1]==0&&({match})){spec.gpu_prepare}(c,e,ne,s,r,full);')
    lines += ['}']
    lines += [f'__device__ void {s.gpu_activate}(const double*,const double*,int,State*,int,int);' for s in specs if s.gpu_activate]
    lines += ['__device__ int lifecycle_activate(const double* c,const double* e,int ne,State* s,int r,int full,const double* q,int uid,int lazy,int mask,int* emitted,Order* targets,int* stop){',
              ' *emitted=-1;*stop=0;']
    for spec in specs:
        if not spec.gpu_activate:continue
        guard='&&!lazy&&mask' if spec.needs_resolved_targets else ''
        codes=((spec.activation_stat,) if spec.activation_stat is not None else ())+spec.additional_stats
        match='||'.join(f'q[2]=={code}' for code in codes)
        if len(codes)>1:match='('+match+')'
        call=f' if(q[1]==0&&{match}{guard}){{r=lifecycle_instance(e,s,r,uid);'
        if spec.applied_event is None:
            call+=f'if(r>=0){spec.gpu_activate}(c,e,ne,s,r,full);'
        else:
            call+=f'*stop=1;if(r>=0){{{spec.gpu_activate}(c,e,ne,s,r,full);*emitted={spec.applied_event};*targets=unique_order(s->target_order[r]);}}'
        lines.append(call+'}')
    lines+=[' return r;','}', '__device__ void lifecycle_retire(const double* e,State* s,int j){']
    lines += [f' {spec.gpu_retire}(e,s,j);' for spec in specs if spec.gpu_retire]
    lines+=['}', '__device__ void lifecycle_before_body_heal(const double* c,const double* e,int ne,State* s,int who,double amount,int full){']
    lines += [f' {spec.gpu_before_heal}(c,e,ne,s,who,amount,full);' for spec in specs if spec.gpu_before_heal]
    return '\n'.join(lines+['}'])+'\n'

BEGIN='// BEGIN GENERATED LIFECYCLE\n'
END='// END GENERATED LIFECYCLE\n'

@lru_cache(maxsize=2)
def _source_matches(path,stamp,size):
    source=Path(path).read_text(encoding='utf-8')
    if source.count(BEGIN)!=1 or source.count(END)!=1:return False
    return source.split(BEGIN,1)[1].split(END,1)[0]==render_cuda()

def gpu_source_matches():
    source=Path(__file__).with_name('detail_effects.cu');stat=source.stat()
    return _source_matches(str(source),stat.st_mtime_ns,stat.st_size)
