"""Positive original healing/shield cases and a no-injury control."""
def support(case):return case['catalogue_profile'].get('scene_witness',{}).get('family')=='Original-support'

def positive_heal(native,stat,name,who):
    field='hp' if stat=='heal_hp_pct' else 'cover_hp'
    return any(e['stat']==stat and e['name']==name and e['after'][field][who]>e['before'][field][who]
               for e in native['support_conditions']['heals'])

def verify(case,native):
    if not support(case):return
    scenario=case['catalogue_profile']['scene_witness']['scenario'];paired=scenario.startswith('Naga-Tia-')
    assert scenario in ('Naga-injured','Tia-injured','Naga-Tia-shield','Naga-Tia-injured-shield'),'Unknown support condition contract'
    injured=scenario!='Naga-Tia-shield';hits=native['battle']['hits'];events=native['support_conditions']['activations']
    from world_original_support_native import selected
    allowed=set(selected(case))
    for event in events:
        assert event['row'] in allowed and event['owner']==case['owners'][event['row']],'Original activation source identity required'
    for event in native['support_conditions']['heals']:
        row=event['row'];assert type(row) is int and 0<=row<len(case['effects']),'Original heal row required'
        effect=case['effects'][row]
        assert event['owner']==case['owners'][row] and event['name']==effect['name'] and event['stat']==effect['stat'],'Original heal source identity required'
    assert native['burst_controls']['ticks'][-1]['cycles']>=1,'Original party must reach full burst'
    assert not any(h['down'] for h in hits),'Support scene must preserve living original actors'
    if injured:
        expected_cover=1 if paired else 0
        by_name={h['pattern']:h for h in hits}
        assert by_name['hp-first']['owner']==0 and by_name['hp-first']['hp']>0,'Real initial HP injury required'
        cover=by_name['cover-first']
        assert cover['owner']==expected_cover and cover['cover']>0 and cover['hp']==0,'Real cover absorption required'
        assert by_name['hp-second']['owner']==2 and by_name['hp-second']['hp']>0,'Second injured recipient required'
        manual=[e for e in native['manual_actions']['events'] if e['kind']=='_enter_cover' and e['owner']==expected_cover]
        assert len(manual)==1 and abs(manual[0]['time']-.9)<1/60+1e-9,'Literal common cover producer required'
    else:assert not hits,'Uninjured control must retain its original empty incoming stream'
    if '나가' in case['names']:
        who=case['names'].index('나가')
        shield_rows=[i for i,(e,o) in enumerate(zip(case['effects'],case['owners'])) if o==who and
                     ('during_shield' in e.get('trigger',{}).get('condition',[]) or 'event:shield_applied' in e.get('trigger',{}).get('timing',[]))]
        assert len(shield_rows)==2
        for row in shield_rows:
            assert bool([e for e in events if e['row']==row])==paired,'Original shield condition must be positive only in paired party'
        if injured:
            assert all(positive_heal(native,'heal_hp_pct','우정의 서포트 2',i) for i in (0,2)),'Original Naga must restore both injured recipients'
        else:
            assert not any(positive_heal(native,'heal_hp_pct','우정의 서포트 2',i) for i in range(5)),'Full-health control cannot count as positive healing'
    if scenario=='Naga-injured':assert positive_heal(native,'cover_heal_pct','우정의 가드',0),'Original Naga must repair damaged cover'
    if '티아' in case['names']:
        who=case['names'].index('티아')
        cooldown=[i for i,(e,o) in enumerate(zip(case['effects'],case['owners'])) if o==who and e.get('stat')=='burst_cooldown']
        assert len(cooldown)==1 and any(e['row']==cooldown[0] for e in events),'Original cover-healed cooldown effect must apply'
        if injured:assert positive_heal(native,'cover_heal_pct','카멜레온 은신술 2',who),'Original Tia must repair damaged cover'
        if scenario=='Tia-injured':
            health=native['sampled_health_returns']
            assert any(b['kind']=='_apply_lifesteal' and b['hp'][who]>a['hp'][who] for a,b in zip(health,health[1:])),'Original Tia must actually lifesteal injured HP'
    if scenario=='Naga-Tia-injured-shield':
        hit=next(h for h in hits if h['pattern']=='shield-hit')
        assert hit['owner']==0 and hit['shield']>0 and hit['hp']==0,'Original applied shield must absorb a real later hit'

def verify_gpu(block,domain,native):
    from portable_runtime import decode
    from world_original_support_native import selected
    case,meta,*_=domain;actual=decode(block[:159744],meta)
    for row in selected(case):
        count=sum(e['row']==row for e in native['support_conditions']['activations'])
        binding=meta['binding_source_indices'].index(row)
        assert actual['timers'][binding]['activations']==count,('Original support source activation count',row,count,actual['timers'][binding]['activations'])
