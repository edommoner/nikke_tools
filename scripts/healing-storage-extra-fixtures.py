"""Additional authored interactions, not CPU-derived GPU input data."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('storage_extra_base',ROOT/'scripts/verify-healing-storage.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
v=m.v;N=v.N;B=v.B;E=v.E
def hit(at=.4,atk=100000,pierce=True,target='slot:1',hits=2,interval=.2):
    return dict(id='reserve interaction',kind='attack',delay=at,until={'time':1.2},spec=dict(coeff=100,atk=atk,target=target,pierce=pierce,hits=hits,interval=interval))
def fixtures():
    for case in ('overlap-newest','overlap-equal-time','snapshot-caster-growth','caster-growth-before','recipient-growth-is-not-capacity','expired-reapplication','lazy-lowest-target','ordered-duplicates','received-and-outgoing','source-down','source-revives','recipient-down-revives','HP-predicate','decoy-before-storage','invincible-before-storage','max-HP-grant-does-not-fill'):
        b=v.body(1.4);x={n:[] for n in N};storage=B('main reserve','heal_overcharge_store',5)
        if case=='lazy-lowest-target':storage['target']='allies_lowest_hp:2'
        if case=='ordered-duplicates':storage['target']=['self','all_allies','self']
        if case in ('source-down','source-revives'):storage['target']='all_allies'
        if case=='expired-reapplication':storage.update(duration=.2);storage['trigger']['timing']=['every:0.4s']
        if case=='caster-growth-before':storage['trigger']['timing']=['every:0.2s'];storage['max_trigger']=1
        x[N[0]].append(storage)
        x[N[1]].append(E('body heal','instant','heal_hp_pct',20,'all_allies' if case in ('source-down','source-revives') else N[0],event='every:0.5s' if case=='expired-reapplication' else 'every:0.3s' if case=='caster-growth-before' else 'every:0.1s',max_trigger=2 if case=='expired-reapplication' else 1))
        if case=='caster-growth-before':x[N[1]][0]['fixed_value']=200
        if case.startswith('overlap'):
            x[N[0]].append(B('second reserve','heal_overcharge_store',3,event='battle_start' if case=='overlap-equal-time' else 'every:0.05s',max_trigger=1))
            b['enemy']['patterns']=[hit(atk=200000)]
        if case in ('snapshot-caster-growth','caster-growth-before'):
            x[N[0]].append(B('caster maximum','max_hp_only_pct',100,event='every:0.4s' if case=='snapshot-caster-growth' else 'every:0.1s',max_trigger=1))
        if case=='recipient-growth-is-not-capacity':
            storage['target']=N[1];x[N[1]].append(B('recipient maximum','max_hp_only_pct',100));x[N[1]][0]['target']=N[1];x[N[1]][0]['fixed_value']=200
        if case=='ordered-duplicates':x[N[1]][0]['target']=[N[0],'all_allies',N[0]]
        if case=='received-and-outgoing':x[N[1]].append(B('healer potency','outgoing_heal_pct',50));x[N[0]].append(B('receiver potency','heal_received_pct',25))
        if case in ('source-down','source-revives','recipient-down-revives'):
            b['enemy']['patterns']=[v.s.lethal(at=.25)]
            if case.endswith('revives'):x[N[2]].append(E('revive','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
            if case=='recipient-down-revives':x[N[1]].append(E('post-revival healing','instant','heal_hp_pct',100,N[0],event='every:0.6s',max_trigger=1))
        if case=='HP-predicate':
            x[N[0]].append(B('full-body health witness','atk_pct',17,event='passive',condition=['self_hp_above:99']))
            b['_debug_scalar_query']={'who':0,'key':0};b['enemy']['patterns']=[hit(atk=50000)]
        if case=='decoy-before-storage':x[N[0]].append(B('decoy first','decoy',100));b['enemy']['patterns']=[hit(pierce=True)]
        if case=='invincible-before-storage':x[N[0]].append(B('invincible first','invincible',1,duration=.8));b['enemy']['patterns']=[hit(atk=50000)]
        if case=='max-HP-grant-does-not-fill':x[N[0]].append(B('maximum and current grant','max_hp_pct',100,event='every:0.4s',max_trigger=1))
        yield 'storage-extra-'+case,b,x
