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
        expected=metadata['product_enemy_ammo'].get('output_words',E['OUTPUT_WORDS'])
        from portable_product_resource_budget import SUPPLY_OUTPUT_WORDS
        if expected not in (E['OUTPUT_WORDS'],2064786,SUPPLY_OUTPUT_WORDS):raise RuntimeError('Invalid product resource output ownership')
        gap=0
        if metadata.get('product_ammo_weighted'):
            from portable_weighted_battle_wire import LAYOUT as W
            gap=W['OUTPUT']-W['OUTPUT_BASE']
        capacity=128+(expected-E['OUTPUT_BASE']-E['RESOURCE_BASE']-gap)//8
        if metadata.get('product_ammo_cover'):
            from portable_cover_defense_wire import OUTPUT as expected
        if len(words)!=expected or count!=words[header+1] or count>capacity or any(words[header+2:header+8]):raise RuntimeError('Invalid complete product resource history')
    elif count>L['TRACE']:raise RuntimeError('Invalid resource notification count')
    trace=[]
    for i in range(count):
        at=(E['OUTPUT_BASE']+E['RESOURCE_BASE']+(i-128)*8 if extended and i>=128 else L['RESOURCE_TRACE_BASE']+i*8)
        if extended and metadata.get('product_ammo_weighted') and i>=128 and at>=W['OUTPUT_BASE']:
            at+=gap
        key=words[at+2]
        if key>=len(names):raise RuntimeError('Invalid resource notification identity')
        if extended and (words[at] not in (26,30) or words[at+1]>=5 or words[at+3]!=0):raise RuntimeError('Invalid complete resource notification')
        trace.append(dict(event=words[at],owner=words[at+1],resource=names[key],time=number(at+4),boundary=number(at+6)))
    return dict(resources=state,resource_queries=queries,resource_trace=trace,resource_trace_total=words[header+1])
