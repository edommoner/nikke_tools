"""Explicit target-scoped hit credit policies; no implicit ammo/core fallback."""
import math
from dataclasses import dataclass
from impact_specs import ActorHandle,ActorKind,HitFamily,HitOutcome,Impact

STAT='target_hit_counter'
SINGLE_BODY_WARNING='対象別の命中数は、本体1体への通常攻撃・スキル・継続ダメージの各着弾を1命中として数えるモデルです。特殊な命中判定は実機未検証です。'
FAMILIES={name.lower():value for name,value in HitFamily.__members__.items()}
OUTCOMES={name.lower():value for name,value in HitOutcome.__members__.items() if value!=HitOutcome.MISS}
KINDS={name.lower():value for name,value in ActorKind.__members__.items()}

@dataclass(frozen=True)
class CounterSpec:
    threshold:float
    actor:ActorHandle
    families:int
    outcomes:int
    preserve:bool
    on_death:bool
    owner_only:bool
    single_body:bool
    def accepts(self,packet):
        return packet.target==self.actor and bool(self.families&(1<<int(packet.family))) and bool(self.outcomes&(1<<int(packet.outcome)))

def _mask(values,names):
    if not isinstance(values,list) or not values or any(not isinstance(name,str) or name not in names for name in values) or len(set(values))!=len(values):raise ValueError('Invalid target-counter credit policy')
    return sum(1<<int(names[name]) for name in values)

def specification(effect):
    if effect.get('stat')!=STAT:
        if 'target_counter' in effect:raise ValueError('Target counter configuration on another operation')
        return None
    if effect.get('type')!='buff' or not isinstance(effect.get('name'),str) or not effect['name']:raise ValueError('Target counter requires a named buff carrier')
    if type(effect.get('max_stack',1)) is not int or effect.get('max_stack',1)!=1:raise ValueError('Target counters have one progress value per carrier')
    if effect.get('trigger',{}).get('condition',[]):raise ValueError('Runtime-conditioned counter carriers require an explicit binding policy')
    if any(key in effect for key in ('scaling','scaling_ref','duration_bullets','duration_scaling','duration_scaling_ref','duration_values','values','fixed_value','tick_interval','tick_start')):raise ValueError('Counter carriers do not use scalar/bullet/periodic value rules')
    duration=effect.get('duration',-1)
    if type(duration) not in (int,float) or not math.isfinite(duration) or duration!=-1 and not 0<duration<=180:raise ValueError('Invalid target-counter lifetime')
    value=effect.get('target_counter')
    if not isinstance(value,dict) or set(value)!={'threshold','actor','families','outcomes','refresh','on_death','attackers','world_scope'}:raise ValueError('Target counter requires all explicit policies')
    threshold=value['threshold']
    if type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1e12:raise ValueError('Invalid target-counter threshold')
    actor=value['actor']
    if not isinstance(actor,dict) or set(actor)!={'kind','identity','generation'} or not isinstance(actor.get('kind'),str) or actor['kind'] not in KINDS:raise ValueError('Invalid target-counter actor')
    target=ActorHandle(KINDS[actor['kind']],actor['identity'],actor['generation'])
    if value['refresh'] not in ('reset','preserve') or type(value['on_death']) is not bool:raise ValueError('Invalid target-counter refresh/death policy')
    if value['attackers'] not in ('owner','squad'):raise ValueError('Invalid target-counter attacker policy')
    if value['world_scope'] not in ('physical_actor','single_body'):raise ValueError('Invalid target-counter world scope')
    single=value['world_scope']=='single_body'
    if single and target!=ActorHandle(ActorKind.BODY,0,1):raise ValueError('Single-body counter must bind the fixed body')
    return CounterSpec(threshold,target,_mask(value['families'],FAMILIES),_mask(value['outcomes'],OUTCOMES),value['refresh']=='preserve',value['on_death'],value['attackers']=='owner',single)

@dataclass(frozen=True)
class CounterCompletion:
    uid:int
    epoch:int
    owner:str
    name:str
    actor:ActorHandle
    credit:float
    reason:str
    impact:Impact|None=None
