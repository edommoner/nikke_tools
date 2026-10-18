"""Received-healing charge interactions and complete raw Delta definitions."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=load('charge_runtime','scripts/staged-heal-charge-runtime.py').install()
v=load('charge_squad_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E
def fixtures():
    variants=['empty','full-HP','damaged','lifesteal','storage','shared-heal','late-bonus','expired-bonus','wrong-bonus-name','source-ATK-snapshot','refresh','ordered-duplicates','early-discharge','cleanse-no-release','named-removal','down-source']
    for variant in variants:
        b=v.body(1.2,scalar=1);x={n:[] for n in N};kw={}
        if variant=='refresh':kw.update(event='every:0.2s',max_trigger=2)
        x[N[0]].append(B('IFAK fixture','heal_overcharge_store_atk_pct',150,duration=.6,**kw))
        if variant!='empty':
            if variant=='lifesteal':x[N[0]].append(B('fixture lifesteal','lifesteal_pct',15))
            else:x[N[4]].append(E('external charged heal','instant','heal_hp_pct',30,N[0],event='every:0.15s',max_trigger=4))
        x[N[0]].append(E('IFAK release','instant','heal_overcharge_discharge',0,'all_allies' if variant!='ordered-duplicates' else [N[1],N[2],N[1]],event='every:0.4s' if variant=='early-discharge' else 'event:state_end:IFAK fixture',target_effect='IFAK fixture',**({'max_trigger':1} if variant=='early-discharge' else {})))
        if variant in ('damaged','storage','shared-heal'):
            x[N[3]].append(B('room for healing','max_hp_only_pct',100,'all_allies'))
        if variant=='storage':x[N[3]].append(B('gray recovery buffer','heal_overcharge_store',20,'all_allies'))
        if variant=='shared-heal':x[N[3]].append(B('shared allocated recovery','heal_split',1,[N[0],N[1]]))
        if variant in ('late-bonus','expired-bonus','wrong-bonus-name'):
            x[N[0]].append(B('live capacity bonus','accumulate_max_scale_pct',50,event='every:0.2s',max_trigger=1,duration=.1 if variant=='expired-bonus' else 1,target_effect='unrelated' if variant=='wrong-bonus-name' else 'IFAK fixture'))
        if variant=='source-ATK-snapshot':x[N[2]].append(B('later ATK','atk_pct',100,N[0],event='every:0.2s',max_trigger=1))
        if variant in ('cleanse-no-release','named-removal'):
            if variant=='cleanse-no-release':
                x[N[0]][0]['polarity']='harmful';x[N[2]].append(E('cleanse pool','instant','debuff_cleanse',0,N[0],event='every:0.3s',max_trigger=1))
            else:x[N[0]].append(E('remove charged pool','instant','remove_named_buff',0,event='every:0.3s',max_trigger=1,target_effect='IFAK fixture'))
        if variant=='down-source':b['enemy']['patterns']=[v.s.lethal('slot:1',at=.3)]
        for n in N:x[n].append(B('release-received witness','atk_pct',2,event='event:heal_received',max_stack=20))
        yield 'charge-'+variant,b,x
def real_fixtures():
    subject='델타 : 닌자 시프'
    for variant,names in [('healer',[subject,'크라운','리타','앨리스','모더니아']),('taunter-negative',[subject,'헬름','리타','앨리스','모더니아']),('Rem-sharing',['렘',subject,'크라운','리타','모더니아']),('Marciana-storage',['마르차나',subject,'크라운','리타','모더니아'])]:
        b=v.body(30,True,names);b['burst_gauge_mode']='accumulate'
        b['enemy']['patterns']=[dict(id='small incoming',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=60000,target='all',hits=50,interval=.5,pierce=True))]
        yield 'raw-charge-'+variant,b,{}
