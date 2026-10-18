"""Lifecycle collisions and cross-effect charge interactions, without imports."""
def fixtures(d):
    v=d.v;N=d.N;B=d.B;E=d.E
    cases=['same-name-two-owners','expiry-recreate-before-release','cleanse-then-new-same-name','expired-boost-keeps-collected','zero-cap-companion','negative-cap-companion','release-inside-HP-edge','live-second-pool-receives-release','other-caster-capacity-bonus','fractional-gear-and-potency']
    for case in cases:
        _,b,x=next(row for row in d.fixtures() if row[0]=='charge-full-HP')
        if case=='same-name-two-owners':
            x[N[1]][0:0]=[B('IFAK fixture','heal_overcharge_store_atk_pct',110,duration=.6),E('second owner release','instant','heal_overcharge_discharge',0,'all_allies',event='event:state_end:IFAK fixture',target_effect='IFAK fixture')]
            x[N[3]].append(E('other owner heal','instant','heal_hp_pct',20,N[1],event='every:0.17s',max_trigger=3))
        if case=='expiry-recreate-before-release':
            x[N[0]].insert(1,E('recreate before release','instant','buff_stack_init',1,event='event:state_end:IFAK fixture',target_effect='IFAK fixture',max_trigger=1))
        if case=='cleanse-then-new-same-name':
            x[N[0]][0]['polarity']='harmful';x[N[4]][0]['max_trigger']=1
            x[N[2]].append(E('cleanse old pool','instant','debuff_cleanse',0,N[0],event='every:0.3s',max_trigger=1))
            x[N[0]].append(B('IFAK fixture','heal_overcharge_store_atk_pct',150,event='every:0.4s',max_trigger=1,duration=.3))
        if case in ('expired-boost-keeps-collected','other-caster-capacity-bonus'):
            owner=N[0] if case.startswith('expired') else N[2]
            x[owner].append(B('temporary capacity','accumulate_max_scale_pct',50 if owner==N[0] else 33.3,N[0],event='every:0.2s',max_trigger=1,duration=.21 if owner==N[0] else 1,target_effect='IFAK fixture'))
        if case in ('zero-cap-companion','negative-cap-companion'):
            x[N[0]].extend([B('nonpositive companion','heal_overcharge_store_atk_pct',0 if case.startswith('zero') else -150,duration=.5),E('nonpositive release','instant','heal_overcharge_discharge',0,'all_allies',event='event:state_end:nonpositive companion',target_effect='nonpositive companion')])
        if case=='release-inside-HP-edge':
            x[N[0]][0]['target']=N[1];x[N[4]][0].update(target=N[1],fixed_value=300,max_trigger=1)
            x[N[3]].insert(0,B('HP space','max_hp_only_pct',100,'all_allies'))
            x[N[0]].insert(1,E('edge releases stored heal','instant','heal_overcharge_discharge',0,'all_allies',event='event:adjacent_hp_max',target_effect='IFAK fixture',max_trigger=1))
        if case=='live-second-pool-receives-release':
            x[N[4]][0]['max_trigger']=3
            x[N[1]][0:0]=[B('secondary pool','heal_overcharge_store_atk_pct',180,'all_allies',event='every:0.5s',max_trigger=1,duration=.5),E('secondary release','instant','heal_overcharge_discharge',0,'all_allies',event='event:state_end:secondary pool',target_effect='secondary pool')]
        if case=='fractional-gear-and-potency':
            c=b['profile']['chars'][N[0]];c['equip_skills']['atk_pct']=[11.11,11.11,12.34];c['cube']={'name':'렐릭 힐링 큐브','level':4}
            x[N[3]]+=[B('source received potency','heal_received_pct',33.3,N[0]),B('recipient potency','heal_received_pct',16.7,N[1])]
        yield 'charge-extra-'+case,b,x
