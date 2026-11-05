"""Literal strict stat predicates; no packing or computed battle schedule."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo_fixtures
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(ammo_fixtures()[0]);base.pop('contract');rows=[]
    def add(label,values=(20,),threshold='0',*,query_values=None,results=None,damage=(6000,6600,7200),stack=3,owner=0):
        c=copy.deepcopy(base);c['name']='accuracy-predicate-'+label
        if owner!=0:
            c['combat']['weapons'][0].update(mode='charge',charge=10,interval=10,min_cycle=10)
            c['combat']['weapons'][owner].update(mode='auto',interval=.1,min_cycle=.1,capacity=10)
        effects=[field('crit_rate',-100,'self','no-crit')]+[field('accuracy_pct',v,'self','accuracy-'+str(i)) for i,v in enumerate(values)]
        effects.append(field('atk_pct',10,'self','accuracy-witness',timing='on_attack',duration=10,max_stack=128,condition=['self_stat_above:accuracy_pct:'+threshold]))
        c.update(effects=effects,owners=[owner]*len(effects))
        c['contract']=dict(owner=owner,query_values=query_values if query_values is not None else [[20.]]*3,results=results if results is not None else [True]*3,damage=list(damage),stack=stack,ammo=7)
        rows.append(c);return c
    add('absent',(),query_values=[[0.]]*3,results=[False]*3,damage=(6000,)*3,stack=0)
    add('positive')
    for label,value in [('zero',0),('negative',-20),('minimum-negative',-5e-324)]:
        add(label,(value,),query_values=[[float(value)]]*3,results=[False]*3,damage=(6000,)*3,stack=0)
    add('equal',(20,),threshold='20',results=[False]*3,damage=(6000,)*3,stack=0)
    add('above-next',(20.000000000000004,),threshold='20',query_values=[[20.000000000000004]]*3)
    add('below-next',(20,),threshold='20.000000000000004',results=[False]*3,damage=(6000,)*3,stack=0)
    add('negative-threshold',(-1,),threshold='-2',query_values=[[-1.]]*3)
    add('minimum-positive',(5e-324,),query_values=[[5e-324]]*3)
    add('cancel',(20,-20),query_values=[[0.]]*3,results=[False]*3,damage=(6000,)*3,stack=0)
    add('ordered-sum-positive',(1e16,-1e16,1),query_values=[[1.]]*3)
    add('ordered-sum-zero',(1e16,1,-1e16),query_values=[[0.]]*3,results=[False]*3,damage=(6000,)*3,stack=0)
    c=add('expires',query_values=[[20.],[0.],[0.]],results=[True,False,False],damage=(6000,6600,6600),stack=1);c['effects'][1]['duration']=.1
    c=add('arrives',query_values=[[0.],[20.],[20.]],results=[False,True,True],damage=(6000,6000,6600),stack=2);c['effects'][1]['trigger']['timing']=['every:0.1s'];c['effects'][1]['max_trigger']=1
    add('last-owner',owner=4)
    c=add('foreign-self',query_values=[[0.]]*3,results=[False]*3,damage=(6000,)*3,stack=0);c['owners'][1]=4
    c=add('ally-applies');c['owners'][1]=4;c['effects'][1]['target']=roster_names(c)[0]
    c=add('stack-before',values=(10,),query_values=[[10.],[20.],[30.]]);c['effects'][1].update(max_stack=3);c['effects'][1]['trigger']['timing']=['on_attack']
    c=add('stack-after',values=(10,),query_values=[[0.],[10.],[20.]],results=[False,True,True],damage=(6000,6000,6600),stack=2);c['effects'][1].update(max_stack=3);c['effects'][1]['trigger']['timing']=['on_attack'];c['effects'][1],c['effects'][2]=c['effects'][2],c['effects'][1]
    c=add('first-condition-false',query_values=[[],[],[]],results=[False]*3,damage=(6000,)*3,stack=0);c['effects'][-1]['trigger']['condition'].insert(0,'self_hp_below:1')
    c=add('last-condition-false',results=[False]*3,damage=(6000,)*3,stack=0);c['effects'][-1]['trigger']['condition'].append('self_hp_below:1')
    c=add('two-conditions',query_values=[[20.,20.]]*3);c['effects'][-1]['trigger']['condition'].append('self_stat_above:accuracy_pct:10')
    c=add('finite-witness',damage=(6000,)*3,stack=1);c['effects'][-1]['duration']=.05
    c=add('permanent-witness',query_values=[[20.],[0.],[0.]],results=[True,False,False],damage=(6000,6600,6600),stack=1);c['effects'][-1]['duration']=-1;c['effects'][1]['duration']=.1
    c=add('level-value');c['effects'][1].pop('fixed_value');c['effects'][1]['values']={'1':-20,'10':20}
    return rows
