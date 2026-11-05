"""Debuff immunity in independent complete five-member CPU/GPU battles."""
import copy,hashlib,importlib.util,json,random,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('immune_raw',ROOT/'scripts/verify-cleanse-detail.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c=r.v.c;E=c.E;NAMES=c.NAMES
import detail_gpu
from calculator.buff_manager import BuffManager

def scenarios():
    owner=NAMES[0]
    def guard(name='pool',stat='debuff_immune_count',value=1,target='all_allies',**kw):return E(name,'buff',stat,value,target,**kw)
    def harm(name='harm',target='all_allies',**kw):return E(name,'buff','atk_pct',-35,target,**{'event':'every:0.5s','duration':2,'polarity':'harmful',**kw})
    for stat,value in [('debuff_immune',0),('debuff_immune_count',1),('debuff_immune_count',1.5),('debuff_immune_count',0),('debuff_immune_count',-1)]:
        yield stat+'-capacity-'+str(value),{owner:[guard(stat=stat,value=value),harm()]},5,False
    yield 'named-exact-and-other-name',{owner:[guard(stat='debuff_immune:harm'),harm(),harm('other harm')]},5,False
    yield 'empty-name-never-matches-named-immunity',{owner:[guard(stat='debuff_immune:'),harm('')]},5,False
    yield 'same-name-across-casters-uses-max-not-sum',{owner:[guard(value=1),harm()],NAMES[1]:[guard(value=2)]},5,False
    yield 'ordered-distinct-pools',{owner:[guard('first'),guard('second',value=2),harm()]},5,False
    yield 'duplicate-recipients-spend-per-occurrence',{owner:[guard(target='self'),harm(target=[owner,owner,NAMES[1]])]},5,False
    yield 'full-immunity-does-not-spend-count-pool',{owner:[guard(),guard('all immunity','debuff_immune'),harm()]},5,False
    yield 'irremovable-and-beneficial-bypass',{owner:[guard(stat='debuff_immune'),harm(polarity='harmful_irremovable'),harm('negative beneficial',polarity='beneficial')]},5,False
    yield 'lazy-harm-bypasses-application-filter',{owner:[guard(stat='debuff_immune'),harm(target='allies_top_atk:2')]},5,False
    yield 'conditional-presence-not-runtime-gate',{owner:[guard(stat='debuff_immune',event='passive',condition=['during_full_burst']),harm()]},5,False
    yield 'blocked-application-still-spends-trigger-budget',{owner:[guard(stat='debuff_immune',duration=1),harm(max_trigger=1)]},5,False
    yield 'expiry-then-recharge',{owner:[guard(duration=1),guard(event='every:2s',duration=1),harm()]},5,False
    yield 'stacked-recharge',{owner:[guard(event='every:1s',max_stack=3),harm(event='every:0.25s')]},5,False
    yield 'nested-harm-before-recharge-reset',{owner:[guard(),harm(),guard(event='every:1s'),harm('nested',event='event:pool',target=owner)]},5,False
    yield 'lazy-count-is-not-forced-by-immunity-check',{owner:[guard(target='allies_random:2'),harm()]},5,False
    yield 'enemy-target-without-immunity',{owner:[harm(target='target')]},5,False
    yield 'enemy-target-general-immunity',{owner:[guard(stat='debuff_immune',target='target'),harm(target='target')]},5,False
    yield 'enemy-target-named-immunity',{owner:[guard(stat='debuff_immune:harm',target='target'),harm(target='target')]},5,False
    yield 'enemy-target-count-refresh',{owner:[guard(target='target'),guard(target='target',event='every:1s'),harm(target='target')]},5,False
    for who in ['에이드','밀크 : 블루밍 바니']:
        # Keep every real source skill. The authored harmful skill supplies a
        # positive/negative immunity stimulus without inventing boss HP damage.
        effects={'리타':[harm('부끄러움',event='every:1s',duration=1.25)]}
        yield 'raw-'+who,effects,60,who

def body_for(subject,seconds):
    names=[subject,'리타','크라운','앨리스','모더니아'] if subject else NAMES
    body=c.body_for(names,seconds,True)
    body.update(shooting_policy='character',burst_policy='rules',_debug_random_state=True)
    if subject:
        body['profile']['chars'][subject]['equip_skills']['max_ammo_pct']=200
        body['stat_deltas']={subject:{'atk':1234}}
    return body

@contextmanager
def observed():
    blocked=BuffManager._harmful_blocked;activate=BuffManager._activate;events={'blocked':0,'allowed':0,'recharges':[]}
    def check(self,who,eff):
        result=blocked(self,who,eff);events['blocked' if result else 'allowed']+=1;return result
    def application(self,eff,caster,t,*args,**kwargs):
        result=activate(self,eff,caster,t,*args,**kwargs)
        if eff.get('stat')=='debuff_immune_count':events['recharges'].append([caster,eff.get('name',''),t])
        return result
    with patch.object(BuffManager,'_harmful_blocked',check),patch.object(BuffManager,'_activate',application),c.observe() as (_,manager,_):yield events,manager



def cpu_assertions(rows):
    by={row['name']:row for row in rows}
    for label,cap in [('debuff_immune_count-capacity-1',1),('debuff_immune_count-capacity-1.5',2),('same-name-across-casters-uses-max-not-sum',2)]:
        assert by[label]['used']['pool']==[cap]*5+[0],label
    assert by['duplicate-recipients-spend-per-occurrence']['used']['pool']==[1,0,0,0,0,0]
    assert by['ordered-distinct-pools']['used']['first']==[1]*5+[0]
    assert by['ordered-distinct-pools']['used']['second']==[2]*5+[0]
    for label in ['debuff_immune-capacity-0','full-immunity-does-not-spend-count-pool','conditional-presence-not-runtime-gate']:
        assert by[label]['events']['blocked']>0 and by[label]['events']['allowed']==0,label
    assert not any(by['full-immunity-does-not-spend-count-pool']['used']['pool'])
    assert by['blocked-application-still-spends-trigger-budget']['events']['blocked']==5
    for label in ['irremovable-and-beneficial-bypass','lazy-harm-bypasses-application-filter']:
        assert by[label]['events']['blocked']==by[label]['events']['allowed']==0
    for label in ['raw-에이드','raw-밀크 : 블루밍 바니']:
        assert by[label]['events']['blocked']>0 and by[label]['events']['allowed']>0
    assert any(t>0 for who,name,t in by['raw-에이드']['events']['recharges'])
    assert by['enemy-target-without-immunity']['events']['blocked']==0
    assert by['enemy-target-count-refresh']['used']['pool']==[0,0,0,0,0,1]
    for label in ['enemy-target-general-immunity','enemy-target-named-immunity']:
        assert by[label]['events']['blocked']>0 and by[label]['events']['allowed']==0,label
