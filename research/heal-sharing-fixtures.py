"""Authored interactions and real Rem/Nayuta squads, import-safe."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=load('sharing_runtime','scripts/staged-heal-sharing-runtime.py').install()
v=load('sharing_squad_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E

def fixtures():
    variants=['no-links','single','equal','Rem-zero-RL','Rem-two-RL','external-heal','overlap-chain','duplicates','stacked','expired','lazy','conditional','full-HP','received-potency','outgoing-potency','storage','lifesteal','down-revive','nested-HP-heal','notification-original-only']
    for variant in variants:
        b=v.body(1.1,scalar=1);x={n:[] for n in N}
        x[N[4]].append(B('room for healing','max_hp_only_pct',100,'all_allies'))
        target=[N[0],N[1]];kw={}
        if variant=='single':target=N[0]
        if variant=='equal':target='all_allies'
        if variant=='Rem-zero-RL':target=[N[0]]
        if variant=='Rem-two-RL':target=N[:3]
        if variant in ('Rem-zero-RL','Rem-two-RL'):x[N[2]].append(B('burst links','heal_split',1,'all_allies'))
        if variant=='overlap-chain':x[N[2]].extend([B('chain links','heal_split',1,[N[1],N[2]]),B('disconnected','heal_split',1,N[3:])])
        if variant=='duplicates':target=[N[0],N[1],N[0],N[1]]
        if variant=='stacked':kw.update(event='every:0.1s',max_stack=3)
        if variant=='expired':kw['duration']=.15
        if variant=='lazy':target=['self','allies_lowest_hp_excl:2']
        if variant=='conditional':kw.update(event='passive',condition=['self_hp_below:60'])
        if variant!='no-links':x[N[0]].append(B('primary links','heal_split',1,target,**kw))
        if variant=='full-HP':x[N[4]][0]['target']=N[1:]
        if variant=='received-potency':x[N[3]]+=[B('original potency','heal_received_pct',100,N[0]),B('shared potency not reapplied','heal_received_pct',500,N[1])]
        if variant=='outgoing-potency':x[N[4]].append(B('outgoing potency','outgoing_heal_pct',50))
        if variant=='storage':x[N[3]].append(B('recipient reserve','heal_overcharge_store',20,'all_allies'))
        heal_target=N[1] if variant=='external-heal' else N[0]
        if variant=='lifesteal':x[N[0]].append(B('personal drain','lifesteal_pct',150))
        else:x[N[4]].append(E('external recovery','instant','heal_hp_pct',150 if variant=='storage' else 30,heal_target,event='every:0.3s',max_trigger=2))
        if variant=='down-revive':
            b['enemy']['patterns']=[v.s.lethal('slot:2',at=.1)]
            x[N[3]].append(E('late revival','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.4s',max_trigger=1))
        if variant=='nested-HP-heal':
            x[N[4]][-1]['fixed_value']=400
            x[N[0]].append(E('deep HP deficit','instant','current_hp_reduce',70,'all_allies',event='every:0.1s',max_trigger=1))
            x[N[1]].append(E('nested adjacent heal','instant','heal_hp_pct',10,N[1],event='event:adjacent_hp_max',max_trigger=1))
        if variant in ('nested-HP-heal','notification-original-only'):
            for n in N:x[n].append(B('received witness','atk_pct',7,event='event:heal_received',max_stack=10))
        yield 'sharing-'+variant,b,x

def real_fixtures():
    for variant,names in [
        ('zero-RL',['렘','리타','앨리스','모더니아','마르차나']),
        ('two-RL',['렘','리타','라플라스','센티','모더니아']),
        ('Crown',['렘','크라운','리타','앨리스','모더니아']),
        ('storage',['렘','마르차나','리타','앨리스','모더니아']),
        ('Nayuta',['나유타','렘','리타','앨리스','모더니아'])]:
        b=v.body(30,True,names);b['burst_gauge_mode']='accumulate'
        b['enemy']['patterns']=[dict(id='small incoming',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=60000,target='all',hits=50,interval=.5,pierce=True))]
        yield 'raw-sharing-'+variant,b,{}
