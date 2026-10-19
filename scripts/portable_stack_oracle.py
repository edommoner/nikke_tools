"""Native carrier/expiry/budget/binding reference, evaluated after GPU readback."""
from portable_removal_oracle import observe

def compare(case,gpu,contains):
    if case.get('stack_bullet_reference'):
        from portable_bullet_oracle import observe as physical
        cpu=physical(case);contains(gpu['queries'],cpu['queries'],case['name']+'.native-physical')
        active=[r for r in gpu['carriers'] if r['active']];assert len(active)==len(cpu['carriers'])
        for a,b in zip(active,cpu['carriers']):contains(a,b,case['name']+'.native-physical-carrier')
        return cpu
    cpu=observe(case);contains(gpu['queries'],cpu['queries'],case['name']+'.native')
    active=[r for r in gpu['carriers'] if r['active']]
    assert len(active)==len(cpu['carriers']),(case['name'],'resident count',active,cpu['carriers'])
    for a,b in zip(active,cpu['carriers']):
        a=dict(a);effect=case['effects'][a['definition']]
        if effect.get('type')=='damage' and effect.get('tick_interval'):
            binding=gpu['periodic_bindings'][a['definition']]
            a['recipients']=sum(1<<(t+5) for t in binding['target_order']) if binding['flags']&1 else 1<<(gpu['timers'][a['definition']]['target_slot']+5)
        expected=dict(b);expected['end']=expected.pop('expiry')
        if 'enemy_generation' in expected and 'enemy_generation' not in a:expected.pop('enemy_generation')
        contains(a,expected,case['name']+'.carrier')
    clocks=[dict(definition=i,due=t['due'],expiry=t['expiry']) for i,t in enumerate(gpu['timers']) if t['active']]
    assert clocks==cpu['timers'],(case['name'],'clocks',clocks,cpu['timers'])
    for row,count in cpu['budgets'].items():assert gpu['timers'][int(row)]['activations']==count,(case['name'],'budget',row,count)
    return cpu
