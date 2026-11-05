"""Identical malformed boolean attack-flag inputs for CUDA and Metal."""
import copy
import struct
from portable_specs import LIMITS as L,FIELDS as F


def rejection_programs(cases,compile_case):
    programs=[];rows=[]
    for stat in ('pierce_enabled','armor_break_enabled'):
        case=next(c for c in cases if c['name']==f'attack-flag-presence-0-{stat}-1-self')
        original,metadata=compile_case(case)
        index=next(i for i,e in enumerate(case['effects']) if e['stat']==stat)
        at=L['DEFINITION_BASE']+index*L['DEFINITION_WORDS']
        changes=[('kind-'+str(kind),{at+F['KIND']:kind}) for kind in (1,2,3,4)]
        changes += [('enemy',{L['HEALTH_DEFINITION_BASE']+index*L['HEALTH_DEFINITION_WORDS']+3:1}),
                    ('damage-flags',{at+F['DAMAGE_FLAGS']:64})]
        for name,value in [('nan',float('nan')),('infinity',float('inf')),('negative-infinity',float('-inf'))]:
            lo,hi=struct.unpack('<II',struct.pack('<d',value));changes.append((name,{at+F['VALUE']:lo,at+F['VALUE']+1:hi}))
        for word in range(8):changes.append(('packet-'+str(word),{L['DAMAGE_DEFINITION_BASE']+index*8+word:1}))
        for name,updates in changes:
            words=list(original)
            for offset,value in updates.items():words[offset]=value
            programs.append((words,copy.deepcopy(metadata)))
            rows.append(dict(name='attack-flag-invalid-'+stat+'-'+name,status=64))
    return programs,rows
