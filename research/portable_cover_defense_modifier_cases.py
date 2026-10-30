"""Original Noah probability source, independent covers and varied incoming coefficients."""
import copy,hashlib,json

def fixtures():
    import engine_worker
    from detail_coverage import body_for
    from portable_cover_defense_battle_cases import fixtures as previous
    from portable_original_incoming_profiles import attack
    seed=previous()[0];rows=[]
    for pierce in (False,True):
        row=copy.deepcopy(seed);row['name']='cover-defense/Noah-modifiers/'+('pierce' if pierce else 'covered')
        row['body']=dict(body_for(['솔져 O.W.','노아','드레이크','자칼','메어리'],30),duration=30,seed=4301,burst_gauge_mode='accumulate')
        p=engine_worker.evaluate(dict(row['body'],_portable_static_inputs=True));names=[c['name'] for c in p['chars']]
        prime=attack('noah-prime',.1,100.,target='slot:2',ignore=True,pierce=True);prime['spec'].update(hits=64,interval=.1)
        patterns=[dict(id='world',kind='idle',until=dict(time=30)),prime]
        for phase,coefficient in ((7.5,33.33),(11.,137.5),(16.5,250.)):
            for who in range(5):
                node=attack(f'phase-{phase}-{who}',phase+who*.5,100000.,target='slot:'+str(who+1),ignore=True,pierce=pierce);node['spec']['coeff']=coefficient;patterns.append(node)
        row['patterns']=patterns;row['body']['enemy']['patterns']=copy.deepcopy(patterns)
        row['declared_manual_sequences']={name:[dict(action='cover',t=phase+who*.5-.1,duration=.25) for phase in (7.5,11.,16.5)] for who,name in enumerate(names)}
        row['cover_defense']=[dict(name=name,base_defense=1000.*2**i) for i,name in enumerate(names)]
        source=[(i,r) for i,r in enumerate(p['effects']) if r['owner']=='노아' and r['effect'].get('stat')=='received_dmg_pct']
        assert len(source)==1
        source_row,record=source[0];effect=record['effect']
        assert effect['trigger']==dict(timing=['received_hit_count:1'],condition=['prob:10']) and effect['values']['10']==-8. and effect['duration']==10. and effect['target']=='all_allies'
        row['contract']=dict(scenario='noah-modifiers',definitions=len(p['effects']),names=names,pierce=pierce,original_probability=10,original_received_pct=-8.,priming_hits=64,coefficients=[33.33,137.5,250.],noah_source_row=source_row,noah_source_sha256=hashlib.sha256(json.dumps(effect,sort_keys=True,ensure_ascii=False).encode()).hexdigest())
        rows.append(row)
    return rows
