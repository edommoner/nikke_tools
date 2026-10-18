"""Data-only staged applications followed by a periodic damage clock."""
import math,re
from dataclasses import dataclass
MAX_STEPS=64
MIN_GAP=1e-6
MODEL_WARNING='段階的な継続攻撃は指定間隔で計算します。親攻撃の連続ヒットを一括計算する近似を含み、実機の着弾時刻は未検証です。'
RAMP_FIELDS=frozenset(('ramp_interval','ramp_damage_stack','post_ramp_tick_delay'))

@dataclass(frozen=True)
class StagedDotSpec:
    reference:str
    count:int|str
    gap:float
    damage_stack:int|None
    post_delay:float
    duration:float
    cap:int
    def stack(self,index):return index if self.cap<0 else min(index,self.cap)

def specification(effect,caster,effects):
    periodic_named=effect.get('type')=='damage' and effect.get('tick_interval') and isinstance(effect.get('target'),str) and effect['target'].startswith('same_target:')
    if not RAMP_FIELDS.intersection(effect) and not periodic_named:return None
    target=effect.get('target')
    if effect.get('type')!='damage' or effect.get('stat')!='dot_damage' or effect.get('scaling')!='stack_count' or effect.get('scaling_ref') or not isinstance(target,str) or not target.startswith('same_target:'):
        raise ValueError('Staged damage requires an owned same-target stack-scaled DoT')
    if not {'ramp_interval','post_ramp_tick_delay'}<=effect.keys():raise ValueError('Staged timing must be explicit')
    reference=target.split(':',1)[1]
    if not effect.get('name') or sum(owner==caster and e.get('name')==effect.get('name') for e,owner in effects)!=1:raise ValueError('Staged carrier name must be unique for its caster')
    matches=[e for e,owner in effects if owner==caster and e.get('name')==reference]
    if not reference or len(matches)!=1:raise ValueError('Staged parent must resolve exactly once for its caster')
    parent=matches[0];parts=parent.get('stat','').split(':')
    if parent.get('type')!='damage' or parent.get('tick_interval') or parts[0] not in ('damage','burst_damage','armor_break_damage','armor_break_burst_damage','sequential_damage','split_damage','bonus_damage') or len(parts)>2:raise ValueError('Staged parent must be a direct attack')
    target_parent=parent.get('target','')
    if not isinstance(target_parent,str) or not (target_parent in ('enemy','target','target_body','same_target','boss','all_enemies') or target_parent.startswith('enemies_')):raise ValueError('Staged parent requires the current aimed enemy model')
    count=1 if len(parts)==1 else int(parts[1]) if re.fullmatch(r'\d+',parts[1]) else parts[1]
    if isinstance(count,int) and not 0<=count<=MAX_STEPS or isinstance(count,str) and (not count or ':' in count or count.startswith('-')):raise ValueError('Invalid staged hit-count reference')
    finite=lambda x:isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
    gap=effect['ramp_interval'];post=effect['post_ramp_tick_delay'];duration=effect.get('duration');cap=effect.get('max_stack',1);damage=effect.get('ramp_damage_stack');interval=effect.get('tick_interval')
    if not finite(gap) or not MIN_GAP<=gap<=60 or not finite(post) or not 0<=post<=3600 or not finite(interval) or interval<=0:raise ValueError('Invalid staged timing')
    if not finite(duration) or not (duration==-1 or 0<duration<=86400):raise ValueError('Invalid staged lifetime')
    if type(cap) is not int or not (cap==-1 or 1<=cap<=MAX_STEPS):raise ValueError('Invalid staged stack cap')
    if damage is not None and (type(damage) is not int or not 0<=damage<=MAX_STEPS):raise ValueError('Invalid staged damage stack')
    if any(key in effect for key in ('tick_start','duration_values','duration_scaling','duration_bullets','hit_count_gauge_ref','damage_formula')):raise ValueError('Ambiguous staged clock or coefficient policy')
    return StagedDotSpec(reference,count,float(gap),damage,float(post),float(duration),cap)

def resolved_count(manager,spec,caster):
    value=spec.count if isinstance(spec.count,int) else manager.ref_count(caster,spec.count)
    value=1 if value is None else value
    if not isinstance(value,(float,int)) or not math.isfinite(value) or not 0<=value<=MAX_STEPS:raise ValueError('Staged count exceeds verified capacity')
    return int(value)
