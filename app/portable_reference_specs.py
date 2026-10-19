"""Static reference identity; live quantities and activation hit counts stay GPU owned."""
def hit_reference(effect):
    if effect.get('type')!='damage':return 0,None
    gauge=effect.get('hit_count_gauge_ref')
    if gauge is not None:
        if not isinstance(gauge,str) or not gauge or ':' in gauge:raise ValueError('Invalid hit count resource reference')
        return 2,gauge
    stat=effect.get('stat','')
    if not isinstance(stat,str):raise ValueError('Damage family must be a string')
    parts=stat.split(':')
    if len(parts)==2 and not parts[1].lstrip('-').isdigit():
        if not parts[1]:raise ValueError('Empty hit count reference')
        return 1,parts[1]
    if len(parts)==1 and parts[0]!='dot_damage' and effect.get('scaling')=='stack_count':
        name=effect.get('scaling_ref')
        if not isinstance(name,str) or not name or ':' in name:raise ValueError('Hit scaling requires a simple reference name')
        return 1,name
    return 0,None

def scale_reference(effect):
    if effect.get('scaling')!='stack_count':return 0,None
    if not effect.get('scaling_ref'):
        if effect.get('type')=='buff':raise ValueError('Buff stack scaling requires scaling_ref')
        return 0,None
    name=effect['scaling_ref']
    if not isinstance(name,str) or not name or ':' in name:raise ValueError('Invalid scale reference name')
    if effect.get('type')=='buff':return (2 if effect.get('duration') not in (None,-1) else 1),name
    if effect.get('type')=='damage' and effect.get('stat')=='dot_damage' and effect.get('tick_interval'):return 3,name
    return 0,None

def pack(words,index,L,effect,keys,states,fields):
    hit,hname=hit_reference(effect);scale,sname=scale_reference(effect);at=L['REFERENCE_DEFINITION_BASE']+index*4
    words[at:at+4]=[hit|(scale<<2),(keys[hname]+1 if hit else 0)|((keys[sname]+1 if scale else 0)<<9),(states[hname] if hit else 0)|((states[sname] if scale else 0)<<8),0]
    if scale:words[L['DEFINITION_BASE']+index*L['DEFINITION_WORDS']+fields['FLAGS']] |= 4
