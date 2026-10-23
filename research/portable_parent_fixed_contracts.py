"""Literal integer truncation, notification-local context and delayed packet contracts."""
TIMES=[13/60,38/60]

def verify(case,native):
    kind=case['contract']['kind'];owner=case['contract']['owner'];o=native['parent_fixed'];trace=o['packets']
    reads=[900,900];amounts=[299,299];times=TIMES;totals=[1800]*5;totals[owner]=2398
    if kind=='one-hundred':amounts=[900,900];totals[owner]=3600
    elif kind in ('zero','negative'):amounts=[];totals[owner]=1800
    elif kind=='fraction-to-zero':amounts=[0,0];totals[owner]=1800
    elif kind=='scatter-two-muzzles':reads=[900]*4;amounts=[299]*4;times=[TIMES[0]]*2+[TIMES[1]]*2;totals[owner]=4796
    elif kind=='seven-pellets':reads=[903]*2;amounts=[300]*2;totals[owner]=2406
    elif kind=='all-enemies':totals=[598,0,0,0,0]
    elif kind=='context-absent-at-battle-start':reads=[0];amounts=[];totals[owner]=1800
    elif kind=='context-absent-at-hit-count':reads=[0,0];amounts=[];totals[owner]=1800
    elif kind=='context-absent-spends-budget':reads=[0];amounts=[];totals[owner]=1800
    elif kind=='budget-one':reads=[900];amounts=[299];times=[TIMES[0]];totals[owner]=2099
    elif kind=='every-second':reads=[900];amounts=[299];times=[TIMES[1]];totals[owner]=2099
    elif kind=='duplicate':reads=[900]*4;amounts=[299]*4;times=[TIMES[0]]*2+[TIMES[1]]*2;totals[owner]=2996
    elif kind=='false-condition':reads=[];amounts=[];totals[owner]=1800
    elif kind=='no-second-modifiers':reads=[900,1800];amounts=[299,599];totals[owner]=3598
    elif kind=='nested-context-empty':reads=[0,900,0,900]
    elif kind=='nonfull-only':reads=[];amounts=[];totals[owner]=2700
    elif kind=='large-quantity':reads=[999999999999903]*2;amounts=[332999999999967]*2;totals[owner]=2665999999999740
    assert native['damage']==totals,(case['name'],native['damage'],totals)
    assert [r['value'] for r in o['reads']]==reads and all(r['owner']==owner for r in o['reads']),(case['name'],o['reads'])
    if kind=='nested-context-empty':assert [r['name'] for r in o['reads']]==['nested-fixed','fixed-parent']*2
    assert [r['amount'] for r in trace]==amounts,(case['name'],trace,amounts)
    for r,t in zip(trace,times):
        assert abs(r['created']-t)<1e-12 and abs(r['landed']-t-1/60)<1e-12 and r['hit']==r['hits']==1
        assert r['recipients']==([0,1,2] if kind=='all-enemies' else [0])
    expected_shots=[2]*5
    if kind=='nonfull-only':expected_shots[owner]=3
    assert native['shots']==expected_shots
    if kind=='lifesteal':assert [a['hp'] for a in native['allies']]==[7398,5000,5000,5000,5000]
    return dict(verified=True,context_reads=len(reads),packets=len(trace),integer_truncation=True,zero_fraction_packet=kind=='fraction-to-zero')
