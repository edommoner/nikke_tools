"""Opt-in pending coordinates, frame geometry and ordinary receipt tails."""
import copy
from portable_coordinate_pending_cases import fixtures as legacy
from world_enemy_attack_cases import field
from target_counter_cases import marker


def fixtures():
    base=copy.deepcopy(legacy()[0]);base.pop('contract')
    base['effects'][-1].update(stat='damage',land_in_full_burst=True,hits_parts=True)
    rows=[]
    def add(label):
        case=copy.deepcopy(base);case['name']='coordinate-full-burst/'+label
        rows.append(case);return case
    def append(case,effect):case['effects'].append(effect);case['owners'].append(0)
    add('all-parts')
    case=add('pierce');case['effects'][-1].update(stat='pierce_damage',hits_parts=False)
    case=add('wide-explosion');case['effects'][-1].update(stat='projectile_explosion_damage',hits_parts=False)
    append(case,field('explosion_range',200,'self','wide'))
    case=add('three-hits');case['effects'][-1]['stat']='sequential_damage:3'
    case=add('zero-hits');case['effects'][-1]['stat']='sequential_damage:0'
    case=add('latched-reference');case['effects'][-1]['stat']='sequential_damage:cast-count'
    count=field('',0,'self','cast-count',max_stack=9);count['trigger']['timing']=['battle_start','full_burst_start'];append(case,count)
    case=add('later-cast-buff');append(case,field('atk_pct',100,'self','later','burst_cast'))
    case=add('entry-buff');append(case,field('atk_pct',100,'self','entry','full_burst_start'))
    case=add('parts-born-before-landing');case['patterns'][0]['delay']=.55
    case=add('parts-expired-before-landing');case['patterns'][0]['until']=dict(time=.3)
    for kind in ('parts','interrupt'):
        case=add(kind+'-receipt-tail')
        counter=marker(name='coordinate-tail-counter',threshold=1,families=['skill']);counter['target']='boss';counter['trigger']['timing']=['full_burst_start'];append(case,counter)
        append(case,dict(name='ordinary-prefix',source='스킬1',type='damage',stat='damage',fixed_value=10,target='boss',trigger=dict(timing=['full_burst_start'],condition=[])))
        append(case,dict(name='coordinate-child',source='스킬1',type='damage',stat='pierce_damage' if kind=='interrupt' else 'damage',fixed_value=20,target='boss',hits_parts=kind=='parts',max_trigger=1,trigger=dict(timing=['event:target_counter_complete:coordinate-tail-counter'],condition=[])))
        case['coordinate_sources']=['parts-source','ordinary-prefix','coordinate-child']
    case=add('legacy-coexists')
    effect=copy.deepcopy(legacy()[0]['effects'][-1]);effect['name']='legacy-source';append(case,effect)
    case['coordinate_sources']=['parts-source','legacy-source']
    # Literal contracts use body750 / part1125 at 25% coefficient, with the
    # original full-burst factor1.5 and part factor1.5 in their ordered layers.
    for case in rows:
        label=case['name'].split('/')[-1];selected=[['near','far']];body=750;part=1125;hits=1
        geometry=['stop','near','far'];is_marker=True;interrupt=0
        if label=='pierce':selected=[['stop','near']];is_marker=False;interrupt=750
        elif label=='wide-explosion':selected=[['stop','near','far']];is_marker=False;interrupt=750
        elif label=='three-hits':hits=3;selected=[['near','far']]*3
        elif label=='zero-hits':hits=0;selected=[]
        elif label=='entry-buff':body=1500;part=2250
        elif label=='parts-expired-before-landing':selected=[[]];geometry=['stop']
        packets=[item for targets in selected for item in [('',body)]+[(name,body if name=='stop' else part) for name in targets]]
        notices=hits
        if label.endswith('receipt-tail'):
            is_marker=False;notices=3
            targets=['near','far'] if label.startswith('parts-') else ['stop','near']
            selected=[[],['near','far'],targets]
            packets=[('',750),('near',1125),('far',1125),('',300),('',600)]+[(name,600 if name=='stop' else 900) for name in targets]
            interrupt=600 if label.startswith('interrupt-') else 0
        elif label=='legacy-coexists':packets.insert(0,('',750))
        case['contract']=dict(event_kinds=['named-hit']*notices+['packet']*len(packets),packets=packets,
            selected=selected,geometry=[geometry]*len(selected),damage=[sum(value for name,value in packets if name!='stop'),0,0,0,0],
            interrupt=[interrupt,0,0,0,0],notices=notices,marker=is_marker)
    return rows
