"""Live candidate changes, immutable harmful membership and passive recovery."""
import copy
from portable_random_cleanse_cases import fixtures as basic
from portable_burst_recipient_cases import instant


def fixtures():
    rows=[];seeds=basic()
    all5=list(range(5));four=list(range(4))
    def add(label,index,pools,picked,before,after,down=None):
        c=copy.deepcopy(seeds[index]);c['name']='random-cleanse-mixed-'+label
        c['effects'][-1]['trigger']['timing']=['on_attack']
        c['contract']=dict(owner=0,pools=pools,picked=picked,before=before,after=after,down=down or [[],[],[]]);rows.append(c);return c
    clean=dict(beneficial=all5);first=dict(first=[0],beneficial=all5);locked=dict(locked=[4],beneficial=all5)
    add('clear-then-empty',1,[[0],[],[]],[[0],[],[]],[first,clean,clean],[clean]*3)
    add('irremovable-reselected',3,[[4]]*3,[[4]]*3,[locked]*3,[locked]*3)
    c=add('expiry-before-second',3,[[4],[],[]],[[4],[],[]],[locked,clean,clean],[locked,clean,clean]);c['effects'][0]['duration']=.05
    dead=dict(locked=[4],beneficial=four)
    c=add('down-retained-but-ineligible',3,[[4],[],[]],[[4],[],[]],[locked,dead,dead],[locked,dead,dead],[[],[4],[4]])
    c['effects'][0]['persist_on_revive']=True
    lethal=dict(id='kill-last',kind='attack',delay=.05,spec=dict(atk=1e12,coeff=100,target='slot:5',pierce=True,ignore_taunt=True))
    c['patterns']=[lethal]
    c=add('revive-retained-reeligible',3,[[4],[],[4]],[[4],[],[4]],[locked,dead,locked],[locked,dead,locked],[[],[4],[]])
    c['effects'][0]['persist_on_revive']=True;c['patterns']=[copy.deepcopy(lethal)]
    c['effects'].append(instant('revive',50,'allies_down_top_atk_excl:1','restore-last','every:0.15s'));c['owners'].append(0)
    c=add('revive-reapplies-passive',3,[[4],[],[4]],[[4],[],[4]],[locked,dict(beneficial=four),dict(beneficial=all5,locked=[4])],[locked,dict(beneficial=four),dict(beneficial=all5,locked=[4])],[[],[4],[]])
    c['patterns']=[copy.deepcopy(lethal)];c['effects'].append(instant('revive',50,'allies_down_top_atk_excl:1','restore-last','every:0.15s'));c['owners'].append(0)
    c=add('reapply-before-each-cleanse',1,[[0]]*3,[[0]]*3,[dict(beneficial=all5,first=[0])]*3,[clean]*3);c['effects'][0]['trigger']['timing']=['on_attack']
    picks={0:[[],[],[]],1:[[0],[4],[0]],3:[[0,4,2],[1,3,4],[4,2,3]],4:[[0,4,2,3],[3,2,4,1],[4,1,2,3]],5:[[0,4,2,3,1],[2,4,3,0,1],[0,2,1,3,4]]}
    from world_frame_native import roster_names
    for count,selected in picks.items():
        membership=dict(locked=all5,beneficial=all5)
        c=add('count-'+str(count),3,[all5]*3,selected,[membership]*3,[membership]*3)
        c['effects'][0]['target']=roster_names(c);c['effects'][-1]['target']='allies_random_with_debuff:'+str(count);c['contract']['count']=count
    return rows
