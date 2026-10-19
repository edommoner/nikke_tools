"""Compare native carriers/deadlines and clock phase after GPU readback."""
from portable_removal_oracle import observe

def aggregate(rows):
    merged={}
    for r in rows:
        key=(r['definition'],r['stacks'],r['lazy_pending'],r['expiry'],r.get('enemy_generation'))
        merged[key]=merged.get(key,0)|r['recipients']
    return sorted((d,s,l,e,g,m) for (d,s,l,e,g),m in merged.items())

def compare(case,gpu,contains):
    cpu=observe(case);contains(gpu['queries'],cpu['queries'],case['name']+'.native')
    active=[]
    for row in gpu['carriers']:
        if not row['active']:continue
        r=dict(row);effect=case['effects'][r['definition']]
        if effect['type']=='damage' and effect.get('tick_interval'):
            b=gpu['periodic_bindings'][r['definition']]
            r['recipients']=sum(1<<(t+5) for t in b['target_order']) if b['flags']&1 else 1<<(gpu['timers'][r['definition']]['target_slot']+5)
        r['expiry']=r['end'];active.append(r)
    assert aggregate(active)==aggregate(cpu['carriers']),(case['name'],'native instances and deadlines',aggregate(active),aggregate(cpu['carriers']))
    clocks=[dict(definition=i,due=t['due'],expiry=t['expiry']) for i,t in enumerate(gpu['timers']) if t['active']]
    assert clocks==cpu['timers'],(case['name'],'native clocks',clocks,cpu['timers'])
    return cpu
