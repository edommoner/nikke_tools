"""Shared malformed raw inputs, exercising GPU admission on both backends."""
import copy
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import double_words


def rejection_programs(cases,compile_case):
    case=next(c for c in cases if c.get('burst_charge_reference'))
    source,metadata=compile_case(case);at=L['BURST_REFERENCE_BASE'];d=L['DEFINITION_BASE']
    changes=[('disabled',{at:0}),('unknown-version',{at:2}),('mask',{at+1:32})]
    changes += [('reserved-'+str(i),{at+i:1}) for i in list(range(2,8))+list(range(28,32))]
    for who in range(5):
        for field in (0,2):
            for name,bits in [('nan',[0,0x7ff80000]),('inf',[0,0x7ff00000]),('negative',double_words(-1)),('large',double_words(1000001))]:
                pos=at+8+who*4+field
                changes.append((f'{who}-{field}-{name}',{pos:bits[0],pos+1:bits[1]}))
    changes += [('absent-raw-with-value',{at+1:0}),('noncombat',{3:0})]
    changes += [('kind-'+str(k),{d+F['KIND']:k}) for k in (1,2,3,4)]
    changes += [('enemy',{L['HEALTH_DEFINITION_BASE']+3:1}),('damage-flag',{d+F['DAMAGE_FLAGS']:64})]
    changes += [('packet-'+str(i),{L['DAMAGE_DEFINITION_BASE']+i:1}) for i in range(8)]
    for name,bits in [('value-nan',[0,0x7ff80000]),('value-inf',[0,0x7ff00000])]:
        changes.append((name,{d+F['VALUE']:bits[0],d+F['VALUE']+1:bits[1]}))
    programs=[];rows=[]
    for name,updates in changes:
        words=list(source)
        for pos,value in updates.items():words[pos]=value
        programs.append((words,copy.deepcopy(metadata)))
        rows.append(dict(name='burst-speed-invalid-'+name,status=64))
    return programs,rows
