"""Literal cast/landing phases, frozen hit counts and excluded buff ordering."""
def verify(case,native):
    c=case['contract'];o=native['full_burst_landing'];calls=o['calls'];hits=o['hits'];delayed=c['delayed']
    assert len(calls)==(2 if delayed else 1) and len(hits)==c['hits'],(case['name'],o)
    assert all(r['name']=='landing' for r in calls+hits)
    cast=calls[0];assert cast['owner']==0 and not cast['full'] and not cast['resolved'] and cast['latched'] is None and cast['excluded']==[]
    assert abs(cast['time']-(.1 if c['stage']==2 else .2))<1e-12
    if delayed:
        land=calls[1];assert land['owner']==0 and land['full'] and land['resolved'] and land['latched']==c['latched_count'] and land['excluded']==sorted(c['excludes'])
        assert abs(land['time']-35/60)<1e-12 and land['time']>cast['time']
    for row in hits:assert row['owner']==0 and row['full']==delayed and abs(row['time']-(35/60 if delayed else cast['time']))<1e-12
    if c['reference']:
        assert [v['value'] for v in o['count_reads']]==[1,2] and o['count_reads'][0]['caller']=='_handle_damage_eff'
    elif c['missing']:assert [v['value'] for v in o['count_reads']]==[None,None]
    else:assert o['count_reads']==[]
    return dict(**verify_trace(case,o['packets']),verified=True,reference_model_gap=False,handler_calls=len(calls),cast_time=cast['time'],delayed=delayed,latched=c['latched_count'] if delayed else None,notifications=len(hits),count_reads=o['count_reads'])

def verify_trace(case,trace):
    row=next(i for i,e in enumerate(case['effects']) if e.get('name')=='landing');c=case['contract'];parent=[v for v in trace if v['row']==row]
    amount=6300 if c['extra']=='magnitude-before' else 3150 if c['delayed'] else 1075
    assert [v['amount'] for v in parent]==[amount]*c['hits'],(case['name'],'parent quantities',parent)
    assert all(v['created']<=v['landed'] for v in trace)
    if c['delayed']:assert all(v['created']==v['landed'] and abs(v['created']-35/60)<1e-12 for v in parent)
    else:assert all(abs(v['landed']-v['created']-1/60)<1e-12 for v in parent)
    if c['extra']=='legacy':assert trace[0]['row']==row+1 and trace[0]['amount']==1575
    if c['extra']=='child':assert [v['amount'] for v in trace]==[3150,1260,3150,1323,3150,1386]
    return dict(parent_packets=len(parent),parent_amount=amount if parent else None,all_packets=len(trace))
