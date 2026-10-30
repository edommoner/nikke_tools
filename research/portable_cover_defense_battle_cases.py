"""Original SOW parties and sequential literal cover/hit operations."""
import copy

def fixtures():
    import engine_worker
    from detail_coverage import body_for
    from portable_original_catalogue_cases import selected_rows
    from portable_original_incoming_profiles import attack
    original=selected_rows(['original-catalogue/hp-shield/솔져 O.W./favorite-0/30s'])[0];rows=[]
    for scenario in ('phases','pierce','broken','shared-shield'):
        row=copy.deepcopy(original);row['name']='cover-defense/Soldier-OW/'+scenario
        if scenario=='shared-shield':row['body']=dict(body_for(['솔져 O.W.','센티','드레이크','자칼','메어리'],30),duration=30,seed=4301,burst_gauge_mode='accumulate')
        prepared=engine_worker.evaluate(dict(row['body'],_portable_static_inputs=True));names=[c['name'] for c in prepared['chars']]
        amount=2500000. if scenario=='broken' else 350000. if scenario=='shared-shield' else 100000.
        pierce=scenario in ('pierce','shared-shield')
        row['patterns']=[dict(id='world',kind='idle',until=dict(time=30)),*[attack(f'phase-{phase}-{who}',phase+who*.5,amount,target='slot:'+str(who+1),ignore=True,pierce=pierce) for phase in (7.5,11.,16.5) for who in range(5)]]
        row['body']['enemy']['patterns']=copy.deepcopy(row['patterns'])
        row['declared_manual_sequences']={name:[dict(action='cover',t=phase+who*.5-.1,duration=.25) for phase in (7.5,11.,16.5)] for who,name in enumerate(names)}
        row['cover_defense']=[dict(name=name,base_defense=1000.*(2**i)) for i,name in enumerate(names)]
        row['contract']=dict(scenario=scenario,definitions=len(prepared['effects']),names=names,boosted_owners=[names[i] for i in sorted(range(5),key=lambda i:prepared['base_atk'][i],reverse=True)[:3]])
        rows.append(row)
    return rows
