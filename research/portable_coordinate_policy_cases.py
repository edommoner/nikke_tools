"""Authored policy expressions; no native operation times become GPU inputs."""
import copy
from portable_coordinate_manual_cases import fixtures as manual
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    base=manual()[0];rows=[]
    def add(label,control,*,owner=0,duration=3.):
        c=copy.deepcopy(base);c.update(name='coordinate-policy/'+label,cover_policies=True,duration=duration,seed=401+len(rows));c['controls']=[{} for _ in range(5)];c['controls'][owner]=copy.deepcopy(control)
        c['combat']['weapons'][0].update(capacity=7,interval=.2,reload=.4)
        from calculator import timeline
        from world_frame_native import roster_names
        for i,n in enumerate(roster_names(c)):c['combat']['weapons'][i]['cooldown']=timeline._NIKKE[n].get('burst_cooldown',40.)
        for i in range(3):c['combat']['weapons'][i]['stage']=i+1
        c['effects'] += [instant('burst_charge_pct',100,'all_allies','initial'),field('fullburst_duration',-9,'self','short-fb')];c['owners'] += [0,0];rows.append(c);return c
    add('own-full-burst',{'cover':{'policy':'own_full_burst'}})
    add('own-full-burst-extend',{'cover':{'policy':'own_full_burst','extend':.3}})
    add('own-full-burst-negative-extend',{'cover':{'policy':'own_full_burst','extend':-.2}})
    add('other-caster-does-not-cover',{'cover':{'policy':'own_full_burst'}},owner=4)
    add('before-end',{'reload':{'policy':'before_fb_end','lead':.3}})
    add('before-end-zero',{'reload':{'policy':'before_fb_end','lead':.3,'duration':0}})
    add('finish-by-end',{'reload':{'policy':'finish_by_fb_end','margin':.1}})
    add('own-end-anchor',{'reload':{'anchor':'own_fb_end','offset':-.3}})
    add('combat-anchor',{'reload':{'anchor':'combat_start','offset':.3,'duration':.1}})
    c=add('named-buff-end',{'reload':{'policy':'finish_by_own_buff_end','buff':'finite','margin':.1}});c['effects'].append(field('atk_pct',10,'all_allies','finite',duration=1.2));c['owners'].append(0)
    c=add('named-buff-other-owner',{'reload':{'policy':'finish_by_own_buff_end','buff':'finite','margin':.1}});c['effects'].append(field('atk_pct',10,'all_allies','finite',duration=1.2));c['owners'].append(4)
    c=add('named-buff-infinite',{'reload':{'policy':'finish_by_own_buff_end','buff':'finite'}});c['effects'].append(field('atk_pct',10,'all_allies','finite'));c['owners'].append(0)
    c=add('next-cycle',{'reload':{'policy':'into_fb','margin':.1}},duration=41.5)
    c=add('dry-check',{'reload':{'policy':'before_fb_end','lead':.3,'if_dry':True}},duration=43.);c['combat']['weapons'][0]['capacity']=40;next(e for e in c['effects'] if e['name']=='initial')['trigger']['timing'].append('every:20s')
    c=add('gate-open',{'reload':{'anchor':'fb_end','offset':-.3,'gate':{'burst_stage':'3','burst_user':'앨리스'}}})
    c=add('gate-closed',{'reload':{'anchor':'fb_end','offset':-.3,'gate':{'burst_stage':'3','burst_user':'N102'}}})
    c=add('cover-wins-reload',{'cover':{'policy':'own_full_burst'},'reload':{'policy':'before_fb_end'}})
    c=add('sequence-preempts',{'cover':{'policy':'own_full_burst'}});c['controls'][1]={'sequence':[dict(action='cover',t=.8,duration=.2)]}
    c=add('cover-disabled',{'cover':{'policy':'own_full_burst'}});c['effects'].append(field('cover_disabled',1,'self','disabled'));c['owners'].append(0)
    c=add('partial-clips',{'reload':{'policy':'finish_by_fb_end','margin':.1}});c['combat']['weapons'][0]['clip_count']=3;c['weapon_metadata']['clip_count']=3
    return rows
