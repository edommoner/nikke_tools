"""Keep real HP crossings distinct from similarly named explicit notifications."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_namespace',ROOT/'scripts/verify-staged-hp-edge.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
g=v.g;s=v.s;N=v.N;B=v.B;E=v.E
def fixtures():
    for case in ('crossing-does-not-emit-named-event','named-event-does-not-cross-hp','explicit-ally-event-retains-name'):
        b=s.v.body(2);b['_debug_hp_events']=True;b['enemy']['patterns']=[s.lethal(at=100)]
        extra={N[0]:[B('self witness','atk_pct',170,event='hp_below:60'),B('named witness','atk_pct',70,event='event:hp_below:60')]}
        if case.startswith('crossing'):extra[N[0]].append(E('reduce hp','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1))
        else:
            name='ally_hp_below:60' if case.startswith('explicit') else 'hp_below:60'
            extra[N[0]].append(B(name,'',event='every:0.2s',max_trigger=1,event_scope='recipients'))
            if case.startswith('explicit'):extra[N[0]].append(B('ally named witness','atk_pct',90,event='event:ally_hp_below:60'))
        yield case,b,extra
