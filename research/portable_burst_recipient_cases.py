"""Caster-owned reentry and instant recipients for both GPU transports."""
import copy
from portable_recipient_extension_cases import fixtures as recipient_fixtures
from world_frame_native import roster_names


def instant(stat,value,target,name,timing='battle_start'):
    return dict(name=name,source='스킬1',type='instant',stat=stat,fixed_value=value,
                target=target,trigger=dict(timing=[timing],condition=[]))


def fixtures():
    base=copy.deepcopy(recipient_fixtures()[-1]);base.update(duration=2,effects=[base['effects'][0]],owners=[0])
    for i,w in enumerate(base['combat']['weapons']):w['stage']=[1,1,2,3,3][i]
    rows=[]
    for label,target,owners,timing,value in [
        ('baseline',None,[],'burst_cast',1),
        ('self','self',[0],'burst_cast',1),
        ('all','all_allies',[0],'burst_cast',1),
        ('two-casters','all_allies',[0,1],'burst_cast',1),
        ('precast','all_allies',[0],'battle_start',1),
        ('stage2','all_allies',[2],'burst_cast',2),
        ('nonmatching-value','all_allies',[0],'burst_cast',2)]:
        c=copy.deepcopy(base);c['name']='reentry-'+label
        for owner in owners:
            c['effects'].append(instant('burst_reentry',value,target,'reentry-'+str(owner),timing));c['owners'].append(owner)
        rows.append(c)
    names=roster_names(base)
    for label,target in [('present',names[4]),('absent','프리카'),('overlap',[names[4],'all_allies'])]:
        c=copy.deepcopy(base);c.update(name='instant-heal-'+label,
            effects=[instant('current_hp_reduce',50,'all_allies','initial-health'),instant('heal_hp_pct',10,target,'heal')],owners=[0,0])
        for ally in c['environment']['allies']:ally['base_hp']=10000
        rows.append(c)
    c=copy.deepcopy(rows[-3]);c['name']='instant-heal-colon-name';c['names']=names[:4]+['아니스 : 스타']
    c['effects'][-1]['target']='아니스 : 스타';rows.append(c)
    for timing in ('battle_start','full_burst_start'):
        c=copy.deepcopy(base);c['name']='instant-b3-heal-'+timing
        for i,w in enumerate(c['combat']['weapons']):w['stage']=[1,2,3,3,3][i]
        c['effects'].extend([instant('current_hp_reduce',50,'all_allies','initial-health'),instant('heal_hp_pct',10,'allies_burst_casted_burst3','b3-heal',timing)]);c['owners'].extend([0,0])
        for ally in c['environment']['allies']:ally['base_hp']=10000
        rows.append(c)
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    words,_,_=compile_case(fixtures()[2]);d=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];p=L['RECIPIENT_BASE']+8
    rows=[]
    for label,at,value in [('no-combat',3,0),('enemy-target',p,4),
                           ('stat',d+F['STAT'],1),('zero-value',d+F['VALUE']+1,0),
                           ('nan-value',d+F['VALUE']+1,0x7ff80000),
                           ('enemy-buff',L['HEALTH_DEFINITION_BASE']+4+3,1)]:
        raw=list(words);raw[at]=value;rows.append(('reject/reentry-'+label,raw,None))
    return rows
