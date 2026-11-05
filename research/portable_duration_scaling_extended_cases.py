"""Mixed native consumers required by the shared duration implementation."""
import copy
from portable_duration_scaling_cases import fixtures as baseline,synthetic_fixtures,REF,gauge
from portable_burst_recipient_cases import instant

def extra_fixtures():
    seed=synthetic_fixtures()[0];rows=[]
    def add(label,values=None):
        c=copy.deepcopy(seed);c.update(name='duration-scaling-mixed-'+label,contract=dict(reference_values=values));rows.append(c);return c
    for label,policy in [('passive-finite','constant3'),('passive-ref-expired','until-expired'),('passive-zero-gauge','constant0')]:
        c=add(label);c['effects'][-1]['trigger']=dict(timing=['passive'],condition=['self_hp_above:0']);c['contract']=dict(reference_policy=policy)
        if policy=='until-expired':c['effects'][1]['duration']=.05
        if policy=='constant0':c['effects'][1]=gauge(0)
    def source(lifetimes):
        e=instant('periodic_source_refresh',0,'self','duration-source','battle_start');e.pop('fixed_value');e['periodic_source']=dict(name=REF,slots=lifetimes,base_interval=10,population_reduction_pct=0);return e
    c=add('source-decay',[3,2,1]);c['effects'].insert(2,source([.1,.2,.25]));c['owners'].insert(2,0)
    c=add('source-zero-shadows-stack',[0,0,0]);c['effects'].insert(2,source([0]));c['owners'].insert(2,0)
    c=add('gauge-zero-shadows-source',[0,0,0]);c['effects'][2:2]=[gauge(0),source([.1,.2,.25])];c['owners'][2:2]=[0,0]
    c=add('source-caster-local',[None]*3);c['effects'].insert(2,source([.1,.2,.25]));c['owners'].insert(2,0);c['owners'][-1]=4;c['combat']['weapons'][0],c['combat']['weapons'][4]=c['combat']['weapons'][4],c['combat']['weapons'][0]
    c=add('stack-operation-raw-refresh',[3]);c['effects'][-1].update(trigger=dict(timing=['battle_start'],condition=[]),polarity='beneficial');c['effects'].append(dict(instant('buff_max_stack_add',1,'self','raw-stack-refresh','on_attack'),type='buff'));c['owners'].append(0);c['observe_stack_refresh']=True
    c=add('colon-reference',[3]*3);name='duration:reference:literal';c['effects'][1]['name']=name;c['effects'][-1]['duration_scaling_ref']=name
    return rows

def fixtures():return baseline()+extra_fixtures()
