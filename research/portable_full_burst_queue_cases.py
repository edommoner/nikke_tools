"""Live deferred queue and owned receipt-tail stimuli, no CPU execution in construction."""
import copy
from portable_full_burst_landing_cases import fixtures as landing
from world_enemy_attack_cases import field
from target_counter_cases import marker

def fixtures():
    seed=copy.deepcopy(next(c for c in landing() if c['name'].endswith('three-hits')));rows=[]
    def add(label):
        c=copy.deepcopy(seed);c['name']='full-burst-queue-'+label;c['contract']=dict(kind=label);rows.append(c);return c
    def child(name='deferred-child',parent='landing',deferred=True,full_only=True,budget=1):
        e=dict(name=name,source='스킬3',type='damage',stat='damage' if deferred else 'bonus_damage',fixed_value=20,target='boss',max_trigger=budget,trigger=dict(timing=['burst_cast','hit_count:'+parent+':1'],condition=['during_full_burst'] if full_only else []))
        if deferred:e['land_in_full_burst']=True
        return e
    def append(c,e):c['effects'].append(e);c['owners'].append(0)
    c=add('live-once');append(c,child())
    c=add('live-nested');append(c,child());append(c,child('deferred-grandchild','deferred-child'))
    c=add('live-initial-and-nested');append(c,child(full_only=False,budget=2))
    c=add('legacy-tail-next-collection');append(c,child('legacy-child',deferred=False))
    for kind in ('parts','interrupt','periodic'):
        c=add('periodic-coexist' if kind=='periodic' else kind+'-receipt-tail')
        counter=marker(name='tail-counter',threshold=1,families=['skill']);counter['target']='boss';counter['trigger']['timing']=['full_burst_start'];append(c,counter)
        append(c,dict(name='ordinary-prefix',source='스킬1',type='damage',stat='damage',fixed_value=10,target='boss',trigger=dict(timing=['full_burst_start'],condition=[])))
        e=dict(name='parts-source',source='스킬1',type='damage',stat='pierce_damage' if kind=='interrupt' else 'dot_damage' if kind=='periodic' else 'damage',fixed_value=20,target='all_enemies' if kind=='periodic' else 'boss',max_trigger=1,trigger=dict(timing=['event:target_counter_complete:tail-counter'],condition=[]))
        if kind=='periodic':
            e.update(duration=.21,tick_interval=.1,tick_start='immediate');c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=2,hp=1e8)))
        else:
            e['hits_parts']=True;append(c,field('part_dmg_pct',50,'self','part-factor'))
            c['patterns'].append(dict(id='parts',kind='parts',targets=[dict(name='near',hp=1e8,reach=1),dict(name='far',hp=1e8,reach=5)]))
        if kind=='interrupt':c['patterns'].append(dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,reach=1)]))
        append(c,e)
    return rows
