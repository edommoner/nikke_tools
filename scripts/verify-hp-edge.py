"""Independent whole-squad CPU/GPU HP-transition acceptance for staged v35."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
import sys
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
s=load('hp_edge_survival_oracle','scripts/verify-survival-detail.py')
from calculator.buff_manager import BuffManager
N=s.N;B=s.B;E=s.E

def fixtures():
    for case in ('self-cross','already-below','rearm-after-heal','second-cross-counter','squad-observer-order','adjacent-observers','adjacent-max-transition','reentrant-heal'):
        b=s.v.body(1);b['_debug_hp_events']=True
        # A future attack creates frame witnesses without changing the battle.
        b['enemy']['patterns']=[s.lethal(at=100)]
        extra={n:[] for n in N};changed=N[1] if case.startswith('adjacent-') else N[0]
        extra[changed].append(E('reduce hp','instant','current_hp_reduce',50,'self',event='every:0.2s',max_trigger=2 if case in ('already-below','rearm-after-heal','second-cross-counter') else 1))
        if case in ('rearm-after-heal','second-cross-counter'):
            extra[changed].append(E('restore hp','instant','heal_hp_pct',100,'self',event='every:0.35s',max_trigger=1))
        timing='hp_below_count:60:2' if case=='second-cross-counter' else 'hp_below:60'
        extra[changed].append(B('self edge witness','atk_pct',17,event=timing,max_stack=100))
        if case=='squad-observer-order':
            for n in N:extra[n].append(B('squad edge witness','atk_pct',13,event='event:ally_hp_below:60'))
        if case in ('adjacent-observers','adjacent-max-transition','reentrant-heal'):
            for n in N:
                extra[n].append(B('adjacent low witness','atk_pct',11,event='event:adjacent_hp_below:60'))
                extra[n].append(B('adjacent max witness','atk_pct',7,event='event:adjacent_hp_max'))
        if case=='adjacent-max-transition':
            extra[changed].append(E('healing while full','instant','heal_hp_pct',100,'self',event='every:0.1s',max_trigger=1))
            extra[changed].append(E('recover maximum','instant','heal_hp_pct',100,'self',event='every:0.3s',max_trigger=1))
        if case=='reentrant-heal':extra[changed].append(E('heal inside edge','instant','heal_hp_pct',100,'self',event='hp_below:60'))
        yield case,b,extra
    for case in ('epsilon-cross','epsilon-no-cross','registration-high-first','registration-low-first','distinct-numeric-spellings','duplicate-key-descriptors','multiple-exact-counts','health-change-inside-edge','startup-max-hp-allies','max-hp-expiry','reduce-all-sequential','heal-all-sequential','lifesteal-to-max','incoming-crossings','received-heal-after-edge','revival-suppresses-edge'):
        b=s.v.body(2);b['_debug_hp_events']=True;b['enemy']['patterns']=[s.lethal(at=100)]
        extra={n:[] for n in N}
        def witness(n,timing,power=17):extra[n].append(B('edge witness '+str(len(extra[n])),'atk_pct',power,event=timing,max_stack=100))
        if case.startswith('epsilon-'):
            extra[N[0]].append(E('reduce hp','instant','current_hp_reduce',40,event='every:0.2s',max_trigger=1))
            witness(N[0],'hp_below:'+('59.9999995' if case=='epsilon-cross' else '59.999998'))
        elif case.startswith('registration-'):
            extra[N[0]].append(E('large decrease','instant','current_hp_reduce',80,event='every:0.2s',max_trigger=1))
            for threshold in ((80,40) if case.endswith('high-first') else (40,80)):witness(N[0],'hp_below:'+str(threshold),threshold)
        elif case in ('distinct-numeric-spellings','duplicate-key-descriptors','multiple-exact-counts'):
            extra[N[0]]+=[E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=3),E('restore hp','instant','heal_hp_pct',100,event='every:0.15s',max_trigger=5)]
            if case=='distinct-numeric-spellings':
                for raw in ('60.0','60'):witness(N[0],'hp_below:'+raw)
            else:
                timings=['hp_below:60','hp_below_count:60:2'] if case=='duplicate-key-descriptors' else ['hp_below_count:60:2','hp_below_count:60:3']
                e=B('multiple timing witness','atk_pct',17,max_stack=100);e['trigger']['timing']=timings;extra[N[0]].append(e)
        elif case=='health-change-inside-edge':
            extra[N[0]]+=[E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1),B('capacity inside edge','max_hp_only_pct',100,'all_allies',event='hp_below:60')]
            for n in N:witness(n,'hp_below:60');witness(n,'event:ally_hp_below:60')
        elif case in ('startup-max-hp-allies','max-hp-expiry'):
            extra[N[0]].append(B('capacity','max_hp_only_pct' if case.startswith('startup') else 'hp_only_caster_based_pct',100,'all_allies',**({} if case.startswith('startup') else dict(duration=.3))))
            for n in N:witness(n,'hp_below:80');witness(n,'event:adjacent_hp_max')
        elif case in ('reduce-all-sequential','heal-all-sequential'):
            extra[N[0]].append(E('decrease everyone','instant','current_hp_reduce',50,'all_allies',event='every:0.2s',max_trigger=1))
            if case=='heal-all-sequential':extra[N[0]].append(E('heal everyone','instant','heal_hp_pct',100,'all_allies',event='every:0.3s',max_trigger=1))
            for n in N:witness(n,'hp_below:60');witness(n,'event:ally_hp_below:60');witness(n,'event:adjacent_hp_below:60');witness(n,'event:adjacent_hp_max')
        elif case=='lifesteal-to-max':
            extra[N[0]]+=[E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1),B('lifesteal','lifesteal_pct',100000)]
            for n in N:witness(n,'event:adjacent_hp_max')
        elif case in ('incoming-crossings','received-heal-after-edge'):
            b['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.2,until={'time':.8},spec=dict(coeff=100,atk=1000000 if case=='incoming-crossings' else 1,target='all',hits=3,interval=.2,pierce=True))]
            extra[N[0]].append(B('remain alive','undying',1,'all_allies'))
            if case=='received-heal-after-edge':extra[N[0]].append(E('decrease everyone','instant','current_hp_reduce',50,'all_allies',event='every:0.15s',max_trigger=1))
            for n in N:
                witness(n,'hp_below:90');witness(n,'event:ally_hp_below:90');witness(n,'event:adjacent_hp_max')
                if case=='received-heal-after-edge':extra[n].append(E('received heal','instant','heal_hp_pct',100,event='received_hit',max_trigger=1))
        else:
            b['enemy']['patterns']=[s.lethal(at=.2)]
            extra[N[1]].append(E('revive','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
            for n in N:witness(n,'hp_below:60');witness(n,'event:ally_hp_below:60');witness(n,'event:adjacent_hp_below:60');witness(n,'event:adjacent_hp_max')
        yield case,b,extra
