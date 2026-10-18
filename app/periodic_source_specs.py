"""Authored slot lifetimes and population-dependent periodic clocks."""
import math
from dataclasses import dataclass
MAX_SOURCES=64
MAX_SLOTS=32
LEGACY_WARNING='召喚物の寿命と攻撃間隔には取得元データの推定値を使用しています。実機での確定値ではありません。'

@dataclass(frozen=True)
class SourceSpec:
    name:str
    lifetimes:tuple
    base:float
    reduction:float
    legacy:bool=False
    def interval(self,count):
        if not 1<=count<=len(self.lifetimes):raise ValueError('Invalid periodic source population')
        return self.base*(1-self.reduction/100*(count-1))

def specification(effect):
    stat=effect.get('stat')
    if stat not in ('periodic_source_refresh','feather_refresh'):return None
    if effect.get('type')!='instant' or effect.get('target','self')!='self':raise ValueError('Periodic refresh requires an instant self operation')
    legacy=stat=='feather_refresh'
    if legacy and 'periodic_source' in effect or not legacy and any(key.startswith('feather_') for key in effect):raise ValueError('Mixed periodic source descriptor forms')
    if legacy:
        keys=('feather_id','feather_slots','feather_interval_base','feather_interval_step_pct')
        if any(key not in effect for key in keys):raise ValueError('Explicit periodic source fields are required')
        name,slots,base,reduction=(effect[k] for k in keys)
    else:
        value=effect.get('periodic_source')
        if not isinstance(value,dict) or set(value)!={'name','slots','base_interval','population_reduction_pct'}:raise ValueError('Invalid periodic source descriptor')
        name,slots,base,reduction=(value[k] for k in ('name','slots','base_interval','population_reduction_pct'))
    number=lambda value:isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    if not isinstance(name,str) or not name or not isinstance(slots,(list,tuple)) or not 1<=len(slots)<=MAX_SLOTS:raise ValueError('Invalid periodic source name/slots')
    if any(not number(v) or not (v==-1 or 0<=v<=86400) for v in slots):raise ValueError('Invalid periodic source lifetime')
    if not number(base) or not 0<base<=3600 or not number(reduction) or not 0<=reduction<=100 or 1-reduction/100*(len(slots)-1)<=0:raise ValueError('Nonpositive periodic source interval')
    if any(k in effect for k in ('values','fixed_value','scaling','tick_interval','duration_bullets','duration')):raise ValueError('Periodic refresh uses its explicit descriptor without scalar/lifetime modifiers')
    return SourceSpec(name,tuple(float(v) for v in slots),float(base),float(reduction),legacy)
