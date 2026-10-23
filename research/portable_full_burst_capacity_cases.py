"""Native-finite live-list boundary and physical landing reentrancy stimuli."""
import copy
from portable_full_burst_queue_cases import fixtures as queue
from target_counter_cases import marker

def fixtures():
    seed=next(c for c in queue() if c['contract']['kind']=='live-once');rows=[]
    def add(kind,loops=0,late=False,legacy=False):
        c=copy.deepcopy(seed);c['name']='full-burst-capacity-'+kind;c['effects'].pop();c['owners'].pop()
        c['contract']=dict(kind=kind,loops=loops,late=late,legacy=legacy,reject=loops==512)
        def append(e):c['effects'].append(e);c['owners'].append(0)
        if loops:
            c['combat']['trace']='summary'
            append(dict(name='loop-child',source='스킬3',type='damage',stat='damage',fixed_value=20,target='boss',land_in_full_burst=True,max_trigger=loops,trigger=dict(timing=['burst_cast','hit_count:landing:1','hit_count:loop-child:1'],condition=['during_full_burst'])))
        if late:
            counter=marker(name='landing-counter',threshold=1,families=['skill']);counter['target']='boss';counter['trigger']['timing']=['full_burst_start'];append(counter)
            for name,deferred in [('late-child',True)]+([('late-legacy',False)] if legacy else []):
                e=dict(name=name,source='스킬3',type='damage',stat='damage' if deferred else 'bonus_damage',fixed_value=20,target='boss',max_trigger=1,trigger=dict(timing=['burst_cast','event:target_counter_complete:landing-counter'],condition=['during_full_burst']))
                if deferred:e['land_in_full_burst']=True
                append(e)
        rows.append(c)
    add('on-land-next-collection',late=True)
    add('mixed-tail-next-collection',late=True,legacy=True)
    add('live-512',loops=511)
    add('live-512-and-on-land-release',loops=511,late=True)
    add('live-513-reject',loops=512)
    return rows
