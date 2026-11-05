"""Whole-squad lost-HP/cover-revival GPU parity; no CPU replay in GPU inputs."""
import argparse,ast,copy,hashlib,importlib.util,inspect,json,math,random,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
s=load('scaling_survival_oracle','scripts/verify-survival-detail.py');N=s.N;B=s.B;E=s.E
from calculator.buff_manager import BuffManager

def body(duration=1,raw=False,names=None,scalar=None):
    b=s.v.body(duration,raw,names);b.update(_debug_hp_events=True)
    if scalar is not None:b['_debug_scalar_query']={'who':scalar,'key':0}
    b['enemy']['patterns']=[s.lethal(at=100)]
    return b

def fixtures():
    for variant in ('full-health','half-health','heal-rearms-value','stacks-do-not-multiply','receiver-health-does-not-scale','max-HP-denominator','source-down-buff-remains','source-revives','stacks-with-bullets','finite-runtime-gate','scaled-maximum','scaled-maximum-revival','stacked-HP-gain'):
        name='lost-'+variant;b=body(1,scalar=1);extra={n:[] for n in N};kw={}
        if variant in ('stacks-do-not-multiply','stacks-with-bullets','stacked-HP-gain'):kw.update(event='every:0.05s',max_stack=3)
        if variant=='stacks-with-bullets':kw['duration_bullets']=20
        if variant=='finite-runtime-gate':kw.update(event='passive',duration=.1)
        e=B('lost HP power','max_hp_pct' if variant=='stacked-HP-gain' else 'max_hp_only_pct' if variant.startswith('scaled-maximum') else 'atk_pct',1.5,N[0] if variant.startswith('scaled-maximum') or variant=='stacked-HP-gain' else N[1],scaling='lost_hp_pct',**kw)
        if variant=='finite-runtime-gate':e['trigger']['condition']=['self_hp_below:60']
        extra[N[0]].append(e)
        if variant in ('half-health','heal-rearms-value','stacks-do-not-multiply','receiver-health-does-not-scale','stacks-with-bullets','finite-runtime-gate','scaled-maximum','stacked-HP-gain'):
            owner=N[1] if variant=='receiver-health-does-not-scale' else N[0];extra[owner].append(E('reduce health','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1))
        if variant in ('heal-rearms-value','scaled-maximum'):extra[N[0]].append(E('restore health','instant','heal_hp_pct',100,event='every:0.4s',max_trigger=1))
        if variant in ('source-down-buff-remains','source-revives','scaled-maximum-revival'):
            b['enemy']['patterns']=[s.lethal(at=.2)]
            if variant!='source-down-buff-remains':extra[N[2]].append(E('revive source','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
        yield name,b,extra
    variants=('no-broken-cover','only-broken-revives','recipient-maximum','healing-cannot-revive','ordinary-heal-living-positive','repeat-revival','random-includes-caster','random-excludes-down','cover-condition-rearms','overmaximum-percentage','stack-reference','empty-budget-then-break','ordered-list-duplicates','revive-then-heal','registered-timer-source-down')
    for variant in variants:
        b=body(2,scalar=0);extra={n:[] for n in N};random_case=variant.startswith('random-') or variant in ('empty-budget-then-break','ordered-list-duplicates','registered-timer-source-down')
        if variant!='no-broken-cover':b['enemy']['patterns']=[dict(id='break covers',kind='attack',delay=.25 if variant=='empty-budget-then-break' else .1,until={'time':.7},spec=dict(coeff=100,atk=1000000 if variant=='ordinary-heal-living-positive' else 5000000,target='all' if random_case else 'slot:1',hits=2 if variant=='repeat-revival' else 1,interval=.4))]
        if variant in ('random-excludes-down','registered-timer-source-down'):b['enemy']['patterns'].append(s.lethal('slot:5' if variant=='random-excludes-down' else 'slot:1',at=.15))
        extra[N[0]]+=[E('take cover','instant','force_reload',0,'all_allies'),B('cover healed witness','atk_pct',11,event='event:cover_healed',max_stack=100)]
        if variant=='recipient-maximum':extra[N[0]].append(B('recipient cover maximum','cover_hp_pct',50))
        if variant in ('healing-cannot-revive','ordinary-heal-living-positive'):extra[N[0]].append(E('ordinary healing','instant','cover_heal_pct',100,event='every:0.3s',max_trigger=1))
        else:
            target='allies_broken_cover_random:2' if random_case else 'all_allies'
            if variant=='ordered-list-duplicates':target=['self',target,'self']
            kw=dict(event='every:0.1s' if variant=='empty-budget-then-break' else 'every:0.3s',max_trigger=2 if variant=='repeat-revival' else 1)
            if variant=='registered-timer-source-down':kw=dict(tick_interval=.3,duration=1)
            if variant=='stack-reference':
                extra[N[0]].append(B('restore factor','',event='every:0.05s',max_stack=2));kw.update(scaling='stack_count',scaling_ref='restore factor')
            extra[N[0]].append(E('revive cover','instant','cover_revive',75 if variant=='recipient-maximum' else 150 if variant=='overmaximum-percentage' else 50,target,**kw))
        if variant=='cover-condition-rearms':
            e=B('broken-cover power','atk_pct',50,event='passive');e['trigger']['condition']=['not_self_cover_alive'];extra[N[0]].append(e)
        if variant=='revive-then-heal':extra[N[0]].append(E('heal restored cover','instant','cover_heal_pct',25,'all_allies',event='every:0.4s',max_trigger=1))
        yield 'cover-'+variant,b,extra

def real_fixtures():
    for character in ('목단','비스킷'):
        for variant in ('no-shots','incoming','accumulate','revival'):
            names=[character,N[1],N[3],N[2],N[0]] if character=='목단' else [N[0],character,N[3],N[2],N[4]]
            if variant=='revival':names=['라푼젤',N[0],N[1],character,N[3]]
            b=body(30,True,names);b['burst_gauge_mode']='accumulate' if variant=='accumulate' else 'fixed';extra={n:[] for n in names}
            if variant in ('incoming','accumulate'):
                extra[names[0]].append(B('test survival support','undying',1,'all_allies'))
                if character=='비스킷':extra[names[0]].append(E('initial cover','instant','force_reload',0,'all_allies'))
                b['enemy']['patterns']=[dict(id='damage',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=5000000 if character=='비스킷' else 800000,target='all' if character=='비스킷' else 'slot:1',hits=6 if character=='비스킷' else 60,interval=4 if character=='비스킷' else .5,pierce=character=='목단'))]
            if variant=='revival':b['enemy']['patterns']=[s.lethal('slot:4',2.8)]
            yield 'raw-'+character+'-'+variant,b,extra
