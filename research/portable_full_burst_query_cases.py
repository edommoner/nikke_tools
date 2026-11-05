"""Deferred HP basis and query-only zero-hit witnesses, statically authored."""
import copy
from portable_full_burst_landing_cases import fixtures as landing
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    seeds={c['name'].removeprefix('full-burst-landing-'):c for c in landing()};rows=[]
    for mode in ('max_hp_additive','max_hp_replacement'):
        for kind,seed in [('three','three-hits'),('reference','latched-reference'),('zero','zero'),('negative','negative'),('later-hp','three-hits'),('ignored-live-1024','latched-reference'),('callback-hp','three-hits'),('parts','three-hits'),('zero-parts','zero')]:
            c=copy.deepcopy(seeds[seed]);c['name']='full-burst-query-'+mode+'-'+kind;c['contract']=dict(kind=kind,mode=mode)
            row=next(i for i,e in enumerate(c['effects']) if e.get('name')=='landing');c['effects'][row].update(scaling=mode,scaling_hp_pct=20)
            if kind in ('zero','zero-parts'):c['effects'][row]['fixed_value']=1e308
            c['effects'].append(field('max_hp_only_pct',100,'self','entry-hp','full_burst_start'));c['owners'].append(0)
            if kind=='later-hp':c['effects'].insert(row+1,field('max_hp_only_pct',100,'self','later-hp','burst_cast'));c['owners'].insert(row+1,0)
            if kind=='ignored-live-1024':
                c['effects'].append(dict(instant('gauge_charge',1024,'self','live-count','full_burst_start'),gauge_id='cast-count'));c['owners'].append(0)
            if kind=='callback-hp':c['effects'].append(field('max_hp_only_pct',100,'self','child-hp','hit_count:landing:1',max_stack=9));c['owners'].append(0)
            if kind in ('parts','zero-parts'):
                c['effects'][row]['hits_parts']=True
                c['effects'].append(field('part_dmg_pct',50,'self','part-factor'));c['owners'].append(0)
                c['patterns'].append(dict(id='parts',kind='parts',targets=[dict(name='near',hp=1e8,reach=1),dict(name='far',hp=1e8,reach=5)]))
            rows.append(c)
    c=copy.deepcopy(seeds['zero']);c['name']='full-burst-query-zero-overflow-ordinary';next(e for e in c['effects'] if e.get('name')=='landing')['fixed_value']=1e308;c['contract']=dict(kind='zero',mode=None);rows.append(c)
    return rows
