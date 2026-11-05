"""Native coordinate contracts including ordinary shape/radius skill selection."""
import copy,math
from portable_coordinate_skill_cases import fixtures as reference
from portable_coordinate_dot_cases import fixtures as dot_cases

def fixtures():
    from importlib import util
    from pathlib import Path
    path=Path(__file__).with_name('verify-coordinate-skill-short.py');s=util.spec_from_file_location('area_existing_fixtures',path);m=util.module_from_spec(s);s.loader.exec_module(m)
    rows=m.fixtures();seen={c['name'] for c in rows}
    for c in reference():
        if c['name'] not in seen:
            c['coordinate_packet_trace']=True;c['coordinate_sources']=[e['name'] for e in c['effects'] if e.get('type')=='damage'];rows.append(c)
    rows.extend(dot_cases())
    base=next(c for c in rows if c['name']=='coordinate-skill/pierce_damage/False/False/False')
    for outside in [False,True]:
        c=copy.deepcopy(base);c['name']='coordinate-area/circle-touch-'+str(outside);x=12+1e-9
        c['patterns'][0]['targets'][0]['x']=math.nextafter(x,math.inf) if outside else x
        selected=['stop'] if outside else ['stop','near'];c['contract'].update(selected=[selected],packets=[('',2000)]+[(n,2000 if n=='stop' else 3000) for n in selected],damage=[2000 if outside else 5000,0,0,0,0],event_kinds=['named-hit']+['packet']*(len(selected)+1));rows.append(c)
    for rotation in [0,45]:
        c=copy.deepcopy(base);c['name']='coordinate-area/rectangle-'+str(rotation);c['patterns'][0]['targets'][1].update(x=14,w=10,h=2,rotation=rotation)
        selected=['stop','near']+(['far'] if rotation==0 else []);c['contract'].update(selected=[selected],packets=[('',2000)]+[(n,2000 if n=='stop' else 3000) for n in selected],damage=[8000 if rotation==0 else 5000,0,0,0,0],event_kinds=['named-hit']+['packet']*(len(selected)+1));rows.append(c)
    c=copy.deepcopy(base);c['name']='coordinate-area/layer2-center';c['focus_aim_layer2']=True
    from timer_registry_cases import NAMES
    c['camera']=[NAMES[0]];c['patterns'][1]['targets'][0]['x']=15;c['effects'][-1]['trigger']['timing']=['every:0.2s'];c['contract'].update(selected=[['stop','far']],packets=[('',2000),('stop',2000),('far',3000)],damage=[5000,0,0,0,0]);rows.append(c)
    c=copy.deepcopy(next(c for c in rows if c['name']=='coordinate-skill/pierce_damage/False/False/True'));c['name']='coordinate-area/range-expiry';c['effects'][-2]['duration']=.1;c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s'];c['contract'].update(selected=[['stop','near','far'],['stop','near']],packets=[('',2000),('stop',2000),('near',3000),('far',3000),('',2000),('stop',2000),('near',3000)],damage=[13000,0,0,0,0],interrupt=[4000,0,0,0,0],notices=2,event_kinds=['named-hit']+['packet']*4+['named-hit']+['packet']*3,geometry=[['stop','near','far']]*2);rows.append(c)
    assert len(rows)==42
    return rows
