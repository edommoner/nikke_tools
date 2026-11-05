"""Native activation probes precede dispatch and stop when the budget is spent."""
import copy
from portable_random_cleanse_mixed_cases import fixtures as mixed

def fixtures():
    seed=mixed()[1];rows=[]
    for cap,pools in [(0,[]),(1,[[4],[4]]),(2,[[4]]*4)]:
        c=copy.deepcopy(seed);c['name']='random-cleanse-budget-'+str(cap);c['effects'][-1]['max_trigger']=cap
        c['contract']=dict(dispatches=cap,pools=pools,picked=copy.deepcopy(pools),remaining=dict(locked=[4],beneficial=list(range(5))))
        rows.append(c)
    c=copy.deepcopy(rows[1]);c['name']='random-cleanse-budget-empty';c['effects'].pop(0);c['owners'].pop(0)
    c['contract']=dict(dispatches=0,pools=[[],[],[]],picked=[[],[],[]],remaining=dict(beneficial=list(range(5))));rows.append(c)
    c=copy.deepcopy(rows[1]);c['name']='random-cleanse-budget-false-condition';c['effects'][-1]['trigger']['condition']=['self_hp_below:1'];c['contract'].update(dispatches=0,pools=[],picked=[]);rows.append(c)
    c=copy.deepcopy(rows[1]);c['name']='random-cleanse-budget-late-candidate';c['effects'][0]['trigger']['timing']=['every:0.1s'];c['contract'].update(dispatches=1,pools=[[],[4],[4]],picked=[[],[4],[4]]);rows.append(c)
    for c in rows:c['contract']['owner']=0
    return rows
