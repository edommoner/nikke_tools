"""Shared negative wire cases for the optional stat-applied event tag."""
from portable_specs import LIMITS as L

def rejection_programs(cases,compile_case):
    dot=next(c for c in cases if c['name']=='named-state-stat-applied-dot_dmg_pct')
    ordinary=next(c for c in cases if c['name']=='named-state-0-self-live-expiry')
    programs=[];expected=[]
    for name,case,index,tag in [('tag-range',dot,0,L['DEFINITIONS']+1),('tag-on-marker',ordinary,0,1),('tag-on-other-stat',ordinary,1,1)]:
        words,meta=compile_case(case);at=L['HEALTH_DEFINITION_BASE']+index*L['HEALTH_DEFINITION_WORDS']+2
        words[at]=(words[at]&3)|(tag<<2)
        programs.append((words,meta));expected.append(dict(name='wire-stat-applied-'+name,status=64))
    return programs,expected
