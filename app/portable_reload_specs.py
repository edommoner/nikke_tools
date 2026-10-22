"""Reload definition identity and authored-value presence;no CPU time calculation."""
STAT=90
MAGIC=0x57524c31
WORDS=264

def fixed(effect):return effect.get('type')=='buff' and effect.get('stat')=='reload_time_fixed'
def forced(effect):return effect.get('type')=='instant' and effect.get('stat')=='force_reload'
def pack(effects,*,manual_swap=None):
 flags=[False]*5 if manual_swap is None else manual_swap
 if not isinstance(flags,list) or len(flags)!=5 or any(type(v) is not bool for v in flags):raise ValueError('Five boolean manual-swap flags required')
 mask=sum(1<<i for i,v in enumerate(flags) if v)
 effects=list(effects)
 if not 1<=len(effects)<=256:raise ValueError('Reload definition capacity exceeded')
 rows=[]
 for effect in effects:
  rows.append(2 if forced(effect) else int('fixed_value' in effect or 'values' in effect) if fixed(effect) else 0)
 return [MAGIC,1,len(effects),mask,0x574d5331 if mask else 0,0,0,0,*rows,*([0]*(256-len(rows)))]
