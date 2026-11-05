"""Literal effective-defense target contracts, without GPU-derived expectations."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    seed=ammo()[0];rows=[]
    def add(label,defenses=(100,100,50,200,99),picked=(2,4),target='allies_below_def',kind='buff'):
        c=copy.deepcopy(seed);c.pop('contract');c['name']='below-def-'+label
        for a,d in zip(c['environment']['allies'],defenses):a['base_defense']=d
        e=field('def_pct',10,target,'below-def-witness','on_attack',duration=.05)
        if kind=='instant':e=instant('heal_hp_pct',1,target,'below-def-witness','on_attack')
        c['effects']=[seed['effects'][0],e];c['owners']=[0,0]
        if kind=='instant':c['effects'].insert(1,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(1,0)
        c.setdefault('patterns',[]).append(dict(id='witness-hit',kind='attack',delay=.225,spec=dict(atk=1000,coeff=100,target='all',pierce=True)))
        c['contract']=dict(picked=[list(picked)]*3,lazy=kind=='buff' and isinstance(target,str));rows.append(c);return c
    def prefix(c,e,owner=0):c['effects'].insert(1,e);c['owners'].insert(1,owner)
    add('strict-ties')
    add('all-equal',defenses=(100,)*5,picked=())
    c=add('negative-and-zero',defenses=(100,)*5,picked=(1,2))
    for who,value in [(0,-100),(1,-200),(2,-101)]:prefix(c,field('def_pct',value,['리타','크라운','앨리스'][who],'negative-'+str(who)))
    add('nextafter-boundary',defenses=(100,99.99999999999999,100.00000000000001,100,50),picked=(1,4))
    c=add('owner-percent',picked=(1,2,4));prefix(c,field('def_pct',100,'self','owner-defense'))
    c=add('candidate-percent',picked=(4,));prefix(c,field('def_pct',200,'앨리스','candidate-defense'))
    c=add('caster-flat',picked=(1,2,3,4));prefix(c,field('def_caster_based_pct',100,'리타','flat-defense'),owner=3)
    c=add('percent-before-flat',defenses=(100,150,175,200,250),picked=(1,2,3));prefix(c,field('def_pct',100,'self','percent'));prefix(c,field('def_caster_based_pct',50,'self','flat'))
    c=add('dead-filter');c['patterns'].insert(0,dict(id='kill',kind='attack',delay=0,spec=dict(atk=1e12,coeff=100,target='slot:3',ignore_taunt=True)));c['contract']['picked']=[[4]]*3
    c=add('list-self',target=['self','allies_below_def']);c['contract']['lazy']=False
    c=add('instant',kind='instant')
    c=add('expires-between-activations');prefix(c,field('def_pct',100,'self','temporary-defense',duration=.05));c['contract']['picked']=[[1,2,4],[2,4],[2,4]]
    c=add('dynamic-not-base',defenses=(100,90,80,200,200),picked=(1,));prefix(c,field('def_pct',100,'앨리스','candidate-raise'))
    return rows
