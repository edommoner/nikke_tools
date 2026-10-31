"""Typed resource readback; no quantities or chosen runtime state enter input."""
def resource_readback(words,metadata,L,number):
    names=metadata.get('resource_names',[]);state=[{} for _ in range(5)]
    for who in range(5):
        for key,name in enumerate(names):
            at=L['RESOURCE_STATE_BASE']+(who*L['RESOURCE_KEYS']+key)*5
            flags=words[at]
            state[who][name]=dict(present=bool(flags&1),value=number(at+1),cap_present=bool(flags&2),base_cap=number(at+3) if flags&2 else None)
    queries=[]
    for index in metadata.get('resource_query_indices',[]):
        at=L['RESOURCE_QUERY_BASE']+index*12;who=words[at+2];key=words[at+3];flags=words[at+4]
        if who>=5 or key>=len(names):raise RuntimeError('Invalid resource query readback')
        queries.append(dict(time=number(at),owner=who,resource=names[key],present=bool(flags&1),cap_present=bool(flags&2),value=number(at+6),base_cap=number(at+8) if flags&2 else None,effective_cap=number(at+10) if flags&2 else None))
    header=L['RESOURCE_HEADER_BASE'];count=words[header]
    extended=metadata.get('product_enemy_ammo') is not None
    if extended:
        from portable_enemy_ammo_wire import LAYOUT as E
        capacity=128+(E['OUTPUT_WORDS']-E['OUTPUT_BASE']-E['RESOURCE_BASE'])//8
        if len(words)!=E['OUTPUT_WORDS'] or count!=words[header+1] or count>capacity or any(words[header+2:header+8]):raise RuntimeError('Invalid complete product resource history')
    elif count>L['TRACE']:raise RuntimeError('Invalid resource notification count')
    trace=[]
    for i in range(count):
        at=(E['OUTPUT_BASE']+E['RESOURCE_BASE']+(i-128)*8 if extended and i>=128 else L['RESOURCE_TRACE_BASE']+i*8);key=words[at+2]
        if key>=len(names):raise RuntimeError('Invalid resource notification identity')
        if extended and (words[at] not in (26,30) or words[at+1]>=5 or words[at+3]!=0):raise RuntimeError('Invalid complete resource notification')
        trace.append(dict(event=words[at],owner=words[at+1],resource=names[key],time=number(at+4),boundary=number(at+6)))
    return dict(resources=state,resource_queries=queries,resource_trace=trace,resource_trace_total=words[header+1])
