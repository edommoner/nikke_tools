"""Native snapshot/landing boundaries; expectations never come from GPU output."""
import copy
from portable_parts_skill_cases import fixtures as originals
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field


def fixtures():
    base=next(c for c in originals() if c['name']=='parts-skill-true');rows=[]
    def add(label,amounts,parts,damage,notices=1,kinds=None):
        c=copy.deepcopy(base);c.update(name='parts-lifecycle-'+label,observe_parts_lifecycle=True)
        c['contract'].update(packet_damage=amounts,packet_parts=parts,damage=[damage,0,0,0,0],named_hit_notices=notices,event_kinds=kinds or ['named-hit']*notices+['packet']*len(amounts),lifecycle_opens=[('parts',1)],lifecycle_captures=[['near','far']])
        rows.append(c);return c
    c=add('named-child-snapshots-both-hits',[2000,3000,3000]*2+[2000,5000,5000]*2,['','near','far']*4,40000,4,(['named-hit']*2+['packet']*6)*2)
    c['effects'][-1].update(stat='bonus_damage:2');c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    c['effects'].insert(-1,field('part_dmg_pct',100,'self','snapshot-boost',timing='hit_count:parts-source:1'));c['owners'].insert(-1,0)
    c['contract']['lifecycle_captures']=[['near','far']]*4
    c=add('named-child-removes-basis-after-snapshot',[2000,3000,3000,2000,2000,2000],['','near','far']*2,14000,2,(['named-hit']+['packet']*3)*2)
    c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    remove=instant('remove_named_buff',1,'self','remove-part-factor','hit_count:parts-source:1');remove['target_effect']='part-factor'
    c['effects'].insert(-1,remove);c['owners'].insert(-1,0)
    c['contract']['lifecycle_captures']=[['near','far']]*2
    c=add('expiry-before-second',[2000,3000,3000,2000],['','near','far',''],10000,2,['named-hit']+['packet']*3+['named-hit','packet'])
    c['patterns'][0]['until']=dict(time=.1);c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    c=add('reopened-same-labels',[2000,3000,3000]*2,['','near','far']*2,16000,2,(['named-hit']+['packet']*3)*2)
    c['patterns'][0].update(until=dict(targets_cleared=True),after=['start','parts'],repeat=2)
    for part in c['patterns'][0]['targets']:part['hp']=1
    c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    c['contract'].update(lifecycle_opens=[('parts',1),('parts',2)],lifecycle_captures=[['near','far']]*2)
    c=add('heal-child-does-not-resample-part-amount',[2000,3000,3000],['','near','far'],8000)
    c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0)
    for effect in (field('lifesteal_pct',10,'self','lifesteal'),field('part_dmg_pct',100,'self','snapshot-boost',timing='event:heal_received')):
        c['effects'].insert(-1,effect);c['owners'].insert(-1,0)
    c['contract']['hp']=[5800,5000,5000,5000,5000]
    c['contract']['lifecycle_kinds']=['part-open','named-hit','packet','heal-notify','part-capture','packet','heal-notify','packet','heal-notify','part-close']
    c=add('destroy-group-before-child-healing',[2000,3000,3000],['','near','far'],8000)
    for part in c['patterns'][0]['targets']:part['hp']=1
    c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0)
    c['effects'].insert(-1,field('lifesteal_pct',10,'self','lifesteal'));c['owners'].insert(-1,0)
    c['contract']['hp']=[5800,5000,5000,5000,5000]
    c['contract']['lifecycle_kinds']=['part-open','named-hit','packet','heal-notify','part-destroy','part-destroy','part-capture','packet','heal-notify','packet','heal-notify','part-close']
    c=add('queued-second-after-group-destruction',[2000,3000,3000,2000],['','near','far',''],10000,2,['named-hit']*2+['packet']*4)
    c['effects'][-1]['stat']='bonus_damage:2'
    for part in c['patterns'][0]['targets']:part['hp']=1
    c['contract'].update(lifecycle_captures=[['near','far'],[]],packet_reach=[(5,3000,0,0),(0,0,0,0),(0,0,0,0),(5,3000,0,0)])
    return rows
