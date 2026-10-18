"""CPU semantic references for the next charge-speed immunity GPU port."""
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('charge_immune_control',ROOT/'scripts/verify-control-detail.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def overflow_scenarios():
    owner=c.NAMES[0]
    def base(speed=150,negative=-10,conversion=50):
        return [c.E('overflow skill speed','buff','charge_speed_pct',speed,'all_allies'),
                c.E('overflow slow','buff','charge_speed_pct',negative,'all_allies'),
                c.E('overflow equipment','buff','charge_speed_pct',5,'all_allies',_source_tag='equipment'),
                c.E('overflow cube','buff','charge_speed_pct',7,'all_allies',_source_tag='cube'),
                c.E('base charge damage','buff','charge_dmg_pct',40,'all_allies'),
                c.E('conversion','buff','charge_speed_overflow_conversion_pct',conversion,'all_allies')]
    for mask in range(4):
        for fixed in (False,True):
            effects=base()
            if mask&1:effects.append(c.E('positive immune','buff','charge_speed_buff_immune',0,'all_allies'))
            if mask&2:effects.append(c.E('negative immune','buff','charge_speed_debuff_immune',0,'all_allies'))
            if fixed:effects.append(c.E('fixed time','buff','charge_time_fixed',1,'all_allies'))
            yield f'overflow-mask-{mask}-fixed-{fixed}',{owner:effects},0 if fixed else [152,2,162,12][mask],40 if fixed else [66,40,71,40][mask]
    for label,speed,coefficient,expected_speed,damage in [
        ('below',80,50,92,40),('exact',88,50,100,40),('above',90,50,102,41),
        ('negative-coefficient',150,-50,162,40),('red-hood-coefficient',90,240,102,44.8)]:
        yield 'overflow-'+label,{owner:base(speed,0,coefficient)},expected_speed,damage

def scenarios():
    owner=c.NAMES[0]
    for mask in range(4):
        for fixed in (False,True):
            effects=[c.E('positive skill','buff','charge_speed_pct',60,'all_allies'),
                     c.E('negative skill','buff','charge_speed_pct',-20,'all_allies'),
                     c.E('equipment speed','buff','charge_speed_pct',5,'all_allies',source='equipment',_source_tag='equipment'),
                     c.E('cube speed','buff','charge_speed_pct',7,'all_allies',source='cube',_source_tag='cube')]
            if mask&1:effects.append(c.E('positive speed immunity','buff','charge_speed_buff_immune',0,'all_allies'))
            if mask&2:effects.append(c.E('negative speed immunity','buff','charge_speed_debuff_immune',0,'all_allies'))
            if fixed:effects.append(c.E('fixed charge','buff','charge_time_fixed',1,'all_allies'))
            yield f'mask-{mask}-fixed-{fixed}',{owner:effects},0 if fixed else [52,-8,72,12][mask]
    for positive in (True,False):
        for immune_positive in (True,False):
            effects=[c.E('group positive','buff','charge_speed_pct',60 if positive else 20,'all_allies',_quant_group='shared'),
                     c.E('group negative','buff','charge_speed_pct',-20 if positive else -60,'all_allies',_quant_group='shared'),
                     c.E('equipment speed','buff','charge_speed_pct',5,'all_allies',_source_tag='equipment'),
                     c.E('cube speed','buff','charge_speed_pct',7,'all_allies',_source_tag='cube'),
                     c.E('group immunity','buff','charge_speed_buff_immune' if immune_positive else 'charge_speed_debuff_immune',0,'all_allies')]
            expected=12 if positive==immune_positive else 52 if positive else -28
            yield f'group-positive-{positive}-immune-positive-{immune_positive}',{owner:effects},expected
    for label,effects,speed,damage in overflow_scenarios():yield label,effects,speed

if __name__=='__main__':
    rows=[];damage_expected={label:damage for label,effects,speed,damage in overflow_scenarios()}
    for label,effects,expected in scenarios():
        body=c.body_for(c.NAMES,8,True)
        for char in body['profile']['chars'].values():
            char['equip_skills']['charge_speed_pct']=0;char['equip_skills']['charge_dmg_pct']=0;char['collection_stage']='없음'
        with c.p.custom_effects(effects),c.observe() as (states,manager,events):cpu=c.a.evaluate(body)
        bm=manager['bm'];buffs={name:bm.get_buffs(name,'__enemy__',body['duration']) for name in body['squad']}
        values={name:b['charge_speed_pct'] for name,b in buffs.items()}
        assert all(value==expected for value in values.values()),(label,values,expected)
        if label in damage_expected:
            import math
            assert all(math.isclose(b['charge_dmg_pct'],damage_expected[label],rel_tol=1e-12,abs_tol=1e-12) for b in buffs.values()),(label,{name:b['charge_dmg_pct'] for name,b in buffs.items()})
        row=dict(name=label,input=body,authored_effects=effects,expected_charge_speed=expected,
                 cpu_charge_speed=values,cpu_charge_damage={name:b['charge_dmg_pct'] for name,b in buffs.items()},expected_charge_damage=damage_expected.get(label),cpu_total=cpu['total_damage'],shots=events['shots'])
        rows.append(row);print(json.dumps(dict(name=label,charge_speed=expected,shots=events['shots']),ensure_ascii=True),flush=True)
    files=['scripts/audit-charge-immunity.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,
        semantic_assertions_passed=True,cases=rows,scope='Sign-selective skill speed immunity, exempt equipment/cube sources, fixed-time override and overflow conversion; no GPU implementation claim.',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    (ROOT/'research/detail-charge-immunity-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
