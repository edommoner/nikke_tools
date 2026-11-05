"""Down versus passive/preserved lost-HP ATK after a native50% revival."""
import copy
from portable_lost_hp_attack_cases import fixtures as attack_fixtures
from portable_burst_recipient_cases import instant

def fixtures():
    rows=[]
    for mode in ('passive','preserved','down'):
        c=copy.deepcopy(attack_fixtures()[1]);c['name']='lost-hp-attack-revival-'+mode;c['duration']=.3
        c['effects'][-1]['trigger']['timing']=['every:0.1s'];c['effects'][1]['trigger']['timing']=['passive']
        if mode=='passive':c['effects'][0]['trigger']['timing']=['passive']
        if mode=='preserved':c['effects'][0]['persist_on_revive']=True
        if mode!='down':
            c['effects'].insert(-1,dict(instant('revive',50,'allies_down_top_atk_excl:1','revive','event:ally_down'),max_trigger=1));c['owners'].insert(-1,1)
        c['patterns']=[dict(id='kill',kind='attack',delay=.05,spec=dict(atk=1e8,coeff=100,target='slot:1',hits=1,pierce=True))]
        c['contract'].update(damage=[0 if mode=='down' else 3000,0,0,0,0],packets=[] if mode=='down' else [1500,1500],rates=[] if mode=='down' else [50,50],hp_rates=[] if mode=='down' else [50,50],sample_names=[] if mode=='down' else ['parts-source']*2,scalar_values=[0] if mode=='down' else [0,50,100],owner_hp=0 if mode=='down' else 5000,owner_down=mode=='down')
        rows.append(c)
    return rows
