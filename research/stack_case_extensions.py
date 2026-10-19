"""Cross-feature authored stimuli; no CPU-computed battle schedules."""
import copy

def cases(buff,op,notify,query,case):
    rows=[]
    def add(name,effects,script,**kw):rows.append(case(name,effects,script,**kw));return rows[-1]
    start=[notify(0),notify(0),notify(0)]
    def on(effect,event):e=copy.deepcopy(effect);e['trigger']['timing']=[event];return e
    for target,budget in [('all_allies_excl_self',None),('allies_weapon:UNKNOWN',None),('allies_weapon:UNKNOWN',1),('allies_weapon_top_atk:UNKNOWN:1',1)]:
        e=op('buff_stack_add',2,target=target)
        if budget is not None:e['max_trigger']=budget
        add('own-ignores-target-'+target+'-'+str(budget),[buff(),e],[notify(0),notify(1,7),query(1)])
    for stat in ('buff_max_stack_add','debuff_stack_add'):
        add('empty-lazy-budget-'+stat,[buff(),op(stat,2,target='allies_weapon_top_atk:UNKNOWN:1',max_trigger=1)],[notify(0),notify(1,7),query(1)])
    add('budget-consumed-without-matching-carrier',[buff(),op('buff_stack_add',2,max_trigger=1)],[notify(0,7),notify(.1),notify(.2,7),query(.2)])
    for duration,extra in [(2,{}),(None,{'duration_values':{'10':2}}),(None,{}),(1e30,{})]:
        add('capped-positive-refresh-'+str(duration)+'-'+str(bool(extra)),[buff(max_stack=3,duration=duration,**extra),op('buff_stack_add',1)],start+[notify(1,7),query(1)])
    generic=[buff(name='harmful',polarity='harmful'),buff(name='irremovable',polarity='harmful_irremovable'),buff(name='beneficial'),buff(name='unlimited',max_stack=-1,polarity='harmful'),op('debuff_stack_remove',10,target_effect='')]
    add('generic-polarity-and-unlimited-filter',generic,start+[notify(1,7),query(1)])
    seed=buff();other=buff(target='all_allies');remove=op('buff_stack_remove',0);remove.update(name='removal',stat='remove_named_buff',trigger=dict(timing=['stack_reach:seed:2'],condition=[]))
    child=buff(name='child',fixed_value=10,max_stack=100,duration=-1,trigger=dict(timing=['stack_reach:seed:2'],condition=[]))
    add('captured-notices-survive-parent-removal',[seed,other,op('buff_stack_add',1),remove,child],[notify(0),notify(1,7),query(1)])
    peer=buff(target='all_allies');remove=copy.deepcopy(remove)
    add('notices-keep-original-caster',[buff(target='all_allies'),peer,op('buff_stack_add',1),remove,copy.deepcopy(child)],[notify(0,19,0),notify(0,19,1),notify(1,7),query(1)],owners=[0,1,0,0,1])
    never=dict(timing=['battle_start'],condition=[])
    add('init-first-registered-definition',[buff(max_stack=3,trigger=never),buff(fixed_value=100,source='스킬2',trigger=never),op('buff_stack_init',9)],[notify(1,7),query(1)])
    add('init-suppressed-by-other-owner',[buff(trigger=never),buff(target='all_allies'),op('buff_stack_init',3)],[notify(0,19,1),notify(1,7),query(1)],owners=[0,1,0])
    add('init-appends-when-caster-not-a-member',[buff(target='all_allies_excl_self',trigger=never),op('buff_stack_init',3)],[notify(0,7),notify(.1,7),query(.1)])
    add('init-lazy-residents-stay-distinct',[buff(target='allies_top_atk:1',trigger=never),op('buff_stack_init',3)],[notify(0,7),notify(0,7),query(0)])
    add('init-does-not-apply-duration-values',[buff(duration=None,duration_values={'10':2},trigger=never),op('buff_stack_init',3)],[notify(1,7),query(1)])
    add('init-does-not-check-immunity',[buff(trigger=never),buff(name='immune',stat='stack_change_immune',max_stack=1,duration=-1),op('buff_stack_init',3)],[notify(0),notify(1,7),query(1)])
    remove=op('debuff_stack_remove',1);remove.update(name='removal',stat='remove_named_buff',trigger=dict(timing=['hit_count'],condition=[]))
    add('init-self-reference-after-slot-reuse',[buff(scaling='stack_count',scaling_ref='seed',trigger=never),op('buff_stack_init',3),remove,on(op('buff_stack_add',1),'event:full_reload')],[notify(0,7),notify(.5,8),notify(1,7),notify(1.5),query(1.5)])
    for amount,reference in [(0.,'resource'),(-.5,'resource'),(2.,'missing')]:
        charge=dict(name='charge',source='스킬1',type='instant',stat='gauge_charge',gauge_id='resource',fixed_value=amount,target='self',trigger=dict(timing=['event:full_reload'],condition=[]))
        add('debuff-delta-reference-'+str(amount)+'-'+reference,[buff(),charge,op('debuff_stack_add',2,scaling='stack_count',scaling_ref=reference)],start+[notify(1,7),query(1)])
    for cap in (1,5):
        dot=dict(name='seed',source='스킬1',type='damage',stat='dot_damage',fixed_value=1,target='boss',duration=2,max_stack=cap,polarity='harmful',tick_interval=.5,scaling='stack_count',trigger=dict(timing=['event:full_reload'],condition=[]))
        ref=buff(name='reference',max_stack=1,duration=None,scaling='stack_count',scaling_ref='seed')
        add('dot-zero-and-refresh-'+str(cap),[dot,ref,op('debuff_stack_remove',1,target='boss')],[notify(0),notify(.25,7),query(.25),notify(.3),query(.3,1)])
    charge=dict(name='resource',source='스킬1',type='instant',stat='gauge_charge',gauge_id='resource',fixed_value=1e100,target='self',trigger=dict(timing=['event:full_reload'],condition=[]))
    dot=dict(name='seed',source='스킬1',type='damage',stat='dot_damage',fixed_value=1,target='boss',duration=2,max_stack=5,polarity='harmful',tick_interval=.5,scaling='stack_count',scaling_ref='resource',trigger=dict(timing=['event:full_reload'],condition=[]))
    add('dot-captured-huge-value-clamps-before-narrowing',[charge,dot,buff(name='reference',max_stack=1,duration=None,scaling='stack_count',scaling_ref='seed'),op('debuff_stack_add',.5,target='boss')],[notify(0),notify(.25,7),query(.25)])
    for stat in ('max_hp_pct','max_hp_only_pct','atk_pct'):
        add('init-quantity-'+stat,[buff(stat=stat,fixed_value=10,trigger=never),op('buff_stack_init',3)],[notify(1,7),query(1)])
    for stat in ('max_hp_pct','max_hp_only_pct'):
        add('mutate-quantity-'+stat,[buff(stat=stat,fixed_value=10),op('buff_stack_add',2),on(op('debuff_stack_remove',3),'hit_count')],[notify(0),notify(.2,7),query(.2),notify(.3,8),query(.3,1)])
    enemies=[dict(hp=100000),dict(hp=100000,kind=5,identity=0),dict(hp=100000,kind=5,identity=1)]
    dormant=dict(timing=['full_charge_hit'],condition=[])
    for mode in ('expiry','partial-removal','reinitialize'):
        seed=buff(stat='received_dmg_pct',target='all_enemies',duration=.5 if mode!='partial-removal' else -1,trigger=dormant)
        init=op('buff_stack_init',3,trigger=dict(timing=['event:full_reload'],condition=[]))
        listener=buff(name='end observer',max_stack=100,duration=-1,trigger=dict(timing=['event:state_end:seed'],condition=[]))
        effects=[seed,init,listener]
        script=[notify(0),[0,4,0,0,0,-1,0,0]]
        if mode=='partial-removal':
            for target,event in [('boss','on_attack'),('all_enemies','hit_count')]:
                removal=op('buff_stack_add',name='remove '+target,target=target,remove_scope='target',trigger=dict(timing=[event],condition=[]));removal['stat']='remove_named_buff';effects.append(removal)
            script += [notify(.1,7),query(.1),notify(.2,8),query(.2,1)]
        else:
            if mode=='reinitialize':effects.append(op('buff_stack_init',3,name='reinitialize',trigger=dict(timing=['event:state_end:seed'],condition=[])))
            script += [[.5,4,0,0,0,-1,0,0],query(.5)]
        c=add('shared-enemy-end-is-per-resident-'+mode,effects,script);c['combat']['targets']=copy.deepcopy(enemies)
    e=buff(stat='received_dmg_pct',target='all_enemies',trigger=never)
    c=add('init-shared-enemy-generation-and-mutation',[e,on(op('buff_stack_init',3),'event:full_reload'),op('debuff_stack_add',1,target='all_enemies')],[notify(0),query(0),query(0,1,1),[.1,22,0,0,1,-1,0,0],[.2,21,0,0,1,-1,100000,0],notify(.3,7),query(.3,2,1),query(.3,3,0),query(.3,4,2)])
    c['combat']['targets']=copy.deepcopy(enemies)
    field=buff(stat='received_dmg_pct',target='all_enemies',trigger=dict(timing=['hit_count'],condition=[]))
    immune=buff(name='immune',stat='stack_change_immune',target='all_enemies',max_stack=1,trigger=never)
    c=add('init-shared-enemy-immunity-is-generation-bound',[field,immune,on(op('buff_stack_init',1,target_effect='immune'),'event:full_reload'),op('debuff_stack_add',1,target='all_enemies')],[notify(0,8),notify(.1),notify(.2,7),query(.2),[.3,22,0,0,1,-1,0,0],[.4,21,0,0,1,-1,100000,0],notify(.5,8),notify(.6,7),query(.6,1,1),query(.6,2,0)])
    c['combat']['targets']=copy.deepcopy(enemies)
    for stat in ('stack_change_immune','buff_max_stack_add'):
        c=add('enemy-marker-has-no-damage-modifier-'+stat,[buff(name='immune',stat=stat,target='all_enemies',max_stack=1),op('debuff_stack_add',1,target='all_enemies',target_effect='immune')],[notify(0),notify(.2,7),query(.2)])
        c['combat']['targets']=copy.deepcopy(enemies)
    init_a=op('buff_stack_init',3,name='init-a',max_trigger=256);init_a['trigger']['timing']=['on_attack']*8
    init_b=op('buff_stack_init',3,name='init-b',max_trigger=252);init_b['trigger']['timing']=['on_attack']*8
    listener=buff(name='listener',max_stack=1,max_trigger=1000,trigger=dict(timing=['stack_reach:seed:4'],condition=[]))
    add('508-residents-deferred-original-owner-notices',[buff(target='all_allies_excl_self',trigger=never),init_a,init_b,on(op('buff_stack_add',1),'event:full_reload'),listener],[notify(0,7) for _ in range(32)]+[notify(1,19,1),query(1)],owners=[0,0,0,1,0])
    for nested in (False,True):
        child=buff(name='stack child',fixed_value=10,max_stack=1,trigger=dict(timing=['stack_reach:seed:3'],condition=['self_hp_above:95']))
        hp=buff(name='hp child',fixed_value=100,max_stack=1,trigger=dict(timing=['hp_below:95'],condition=[])) if not nested else op('debuff_stack_remove',1,name='hp child',trigger=dict(timing=['hp_below:95'],condition=[]))
        add('hp-stack-child-before-boundary-'+str(nested),[buff(stat='max_hp_pct',fixed_value=10),op('buff_stack_add',2),child,hp],[notify(0),notify(.2,7),query(.2)])
    other=buff(name='other hp',stat='max_hp_pct',fixed_value=10,max_stack=1)
    remove=op('buff_stack_add',1,name='remove other',target_effect='other hp',trigger=dict(timing=['stack_reach:seed:3'],condition=[]));remove['stat']='remove_named_buff'
    tail=buff(name='tail',fixed_value=10,max_stack=1,trigger=dict(timing=['stack_reach:seed:3'],condition=['self_hp_above:95']))
    add('nested-removal-defers-derived-hp-until-stack-children',[buff(stat='max_hp_pct',fixed_value=10),other,op('buff_stack_add',2),remove,tail],[notify(0),notify(.2,7),query(.2)])
    dot=dict(name='seed',source='스킬1',type='damage',stat='dot_damage',fixed_value=1,target='boss',duration=2,max_stack=1,polarity='harmful',tick_interval=.5,scaling='stack_count',trigger=dict(timing=['event:full_reload'],condition=[]))
    add('dot-expired-unretired-zero-survives-refresh',[dot,op('debuff_stack_remove',1,target='boss')],[notify(0),notify(.25,7),notify(3),query(3)])
    for stat in ('buff_stack_add','buff_stack_init'):
        seed=buff(trigger=dict(timing=['full_charge_hit'],condition=[])) if stat=='buff_stack_init' else buff()
        gate=buff(name='gate',duration=-1)
        timed=op(stat,3 if stat=='buff_stack_init' else 1,max_trigger=1,tick_interval=.25,duration=1,target='allies_with_buff:gate',trigger=dict(timing=['event:full_reload'],condition=[]))
        removal=op('buff_stack_add',name='remove gate',target_effect='gate',trigger=dict(timing=['hit_count'],condition=[]));removal['stat']='remove_named_buff'
        add('periodic-'+stat+'-does-not-recheck-activation-budget-target',[seed,gate,timed,removal],[notify(0),[0,4,0,0,0,-1,0,0],notify(.1,8),[.25,4,0,0,0,-1,0,0],[.5,4,0,0,0,-1,0,0],query(.5)])
    passive=op('buff_max_stack_add',1,trigger=dict(timing=['passive'],condition=[]))
    add('passive-max-operation-uses-common-frame-executor',[buff(trigger=dict(timing=['battle_start'],condition=[])),passive],[[0,4,0,0,0,-1,0,0],[.1,4,0,0,0,-1,0,0],[.2,4,0,0,0,-1,0,0],query(.2)])
    forced=op('buff_stack_add',name='force slot',trigger=dict(timing=['full_charge_fire'],condition=[]));forced.update(stat='force_skill_use',target_skill='스킬2');forced.pop('target_effect')
    add('forced-slot-stack-operation-uses-common-executor',[buff(),op('buff_stack_add',1,source='스킬2'),forced],[notify(0),notify(.2,11),query(.2)])
    empty_passive=op('buff_max_stack_add',1,max_trigger=1,target='allies_weapon:UNKNOWN',trigger=dict(timing=['passive'],condition=[]))
    add('passive-activation-retains-empty-target-budget',[buff(),empty_passive],[[0,4,0,0,0,-1,0,0],notify(.1),[.2,4,0,0,0,-1,0,0],query(.2)])
    timed=op('buff_stack_add',1,max_trigger=1,tick_interval=.25,duration=1,trigger=dict(timing=['passive'],condition=[]))
    add('passive-periodic-stack-callback-does-not-spend-another-budget',[buff(trigger=dict(timing=['battle_start'],condition=[])),timed],[[0,4,0,0,0,-1,0,0],[.25,4,0,0,0,-1,0,0],[.5,4,0,0,0,-1,0,0],query(.5)])
    conditional=op('buff_max_stack_add',1,max_trigger=1,duration=1,target='allies_weapon:UNKNOWN',trigger=dict(timing=['passive'],condition=['self_hp_above:0']))
    add('finite-conditional-passive-rechecks-empty-budget-target',[buff(),conditional],[[0,4,0,0,0,-1,0,0],notify(.1),[.2,4,0,0,0,-1,0,0],query(.2)])
    for duration in (2,None):
        charge=dict(name='charge source',source='스킬1',type='instant',stat='gauge_charge',gauge_id='source',fixed_value=2,target='self',trigger=dict(timing=['event:full_reload'],condition=[]))
        later=dict(charge,name='charge later',fixed_value=5,trigger=dict(timing=['hit_count'],condition=[]))
        add('external-reference-is-not-own-stack-'+str(duration),[charge,buff(scaling='stack_count',scaling_ref='source',duration=duration),op('buff_stack_add',2),later],[notify(0),notify(.5,7),notify(.6,8),query(.6)])
    for stat in ('hp_caster_based_pct','hp_only_caster_based_pct'):
        add('init-caster-hp-flat-'+stat,[buff(stat=stat,fixed_value=10,target='all_allies',trigger=dict(timing=['full_charge_hit'],condition=[])),op('buff_stack_init',3)],[notify(1,7),query(1)],environment=dict(allies=[dict(base_hp=1000000),dict(base_hp=2000000)]+[dict(base_hp=1000000) for _ in range(3)]))
    add('init-snapshot-hp-does-not-run-normal-grant',[buff(stat='max_hp_from_max_hp_pct',fixed_value=10,trigger=dict(timing=['full_charge_hit'],condition=[])),op('buff_stack_init',3)],[notify(1,7),query(1)])
    for initialized,refresh in [(True,False),(True,True),(False,False)]:
        gate=buff(name='gate',duration=-1)
        seed=buff(duration=None,duration_values={'10':2},trigger=dict(timing=['full_charge_hit'],condition=['self_state:gate']))
        removal=op('buff_stack_add',name='remove gate',target_effect='gate',trigger=dict(timing=['hit_count'],condition=[]));removal['stat']='remove_named_buff'
        script=[notify(0),notify(.5,7 if initialized else 12)]
        if refresh:script.append(notify(.75,12))
        script.extend([notify(1,8),query(1)])
        add('birth-runtime-policy-init-'+str(initialized)+'-refresh-'+str(refresh),[gate,seed,op('buff_stack_init',3),removal],script)
    gate=buff(name='gate',duration=-1)
    seed=buff(duration=None,duration_values={'10':2},trigger=dict(timing=['full_charge_hit'],condition=['self_state:gate']))
    alias=buff(source='스킬2',duration=None,duration_values={'10':2},trigger=dict(timing=['full_charge_fire'],condition=['self_state:gate']))
    removal=op('buff_stack_add',name='remove gate',target_effect='gate',trigger=dict(timing=['hit_count'],condition=[]));removal['stat']='remove_named_buff'
    add('initialized-runtime-carrier-is-not-merged-with-finite-alias',[gate,seed,alias,op('buff_stack_init',3),removal],[notify(0),notify(.5,7),notify(.75,11),notify(1,8),query(1)])
    return rows
