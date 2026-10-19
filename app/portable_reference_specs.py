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

def pack(words,index,L,effect,keys,states):
    mode,name=hit_reference(effect);at=L['REFERENCE_DEFINITION_BASE']+index*4
    if mode:words[at:at+4]=[mode,keys[name]+1,states[name],0]
