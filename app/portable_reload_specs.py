"""Reload definition identity and authored-value presence;no CPU time calculation."""
STAT=90
MAGIC=0x57524c31
WORDS=264

def fixed(effect):return effect.get('type')=='buff' and effect.get('stat')=='reload_time_fixed'
def forced(effect):return effect.get('type')=='instant' and effect.get('stat')=='force_reload'
def pack(effects):
 effects=list(effects)
 if not 1<=len(effects)<=256:raise ValueError('Reload definition capacity exceeded')
 rows=[]
 for effect in effects:
  rows.append(2 if forced(effect) else int('fixed_value' in effect or 'values' in effect) if fixed(effect) else 0)
 return [MAGIC,1,len(effects),0,0,0,0,0,*rows,*([0]*(256-len(rows)))]
