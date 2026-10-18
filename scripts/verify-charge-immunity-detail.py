"""Independent whole-squad parity for speed immunity and overflow conversion."""
import copy,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
audit=module('charge_immune_audit','scripts/audit-charge-immunity.py');c=audit.c;E=c.E
raw=module('charge_immune_raw','scripts/verify-cleanse-detail.py')
import detail_gpu
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda

def dynamic_cases():
    owner=c.NAMES[2]
    base=[E('skill speed','buff','charge_speed_pct',70,'all_allies'),E('skill slow','buff','charge_speed_pct',-20,'all_allies'),
          E('conversion','buff','charge_speed_overflow_conversion_pct',240,'all_allies')]
    yield 'timed-positive-immunity',{owner:base+[E('temporary immunity','buff','charge_speed_buff_immune',0,'all_allies',duration=1,event='every:2s')]},8
    yield 'fullburst-runtime-immunity',{owner:base+[E('full burst immune','buff','charge_speed_debuff_immune',0,'all_allies',event='passive',condition=['during_full_burst'])]},8
    yield 'charge-runtime-immunity',{owner:base+[E('charge immune','buff','charge_speed_buff_immune',0,'self',event='passive',condition=['during_charge'])]},8
    yield 'single-bullet-immunity',{owner:base+[E('one bullet immune','buff','charge_speed_buff_immune',0,'self',event='burst_cast',duration_bullets=1)]},8
    yield 'enemy-slow-and-ally-immunity',{owner:base+[E('enemy slow','buff','charge_speed_pct',-25,'target',polarity='harmful'),E('own negative immunity','buff','charge_speed_debuff_immune',0)]},8
    yield 'caster-based-speed-and-immunity',{owner:[E('caster speed','buff','charge_speed_caster_based_pct',75,'all_allies'),E('negative caster speed','buff','charge_speed_caster_based_pct',-25,'all_allies'),E('positive immunity','buff','charge_speed_buff_immune',0,'all_allies')]},8
    mode={'source':'스킬3','name':'authored SR mode','type':'weapon_change','target':'self','weapon_type':'SR','max_ammo':4,'damage_coeff':{'10':251},'charge_time':.3,'full_charge_mult':250,'duration':3,'trigger':{'timing':['burst_cast'],'condition':[]}}
    yield 'weapon-mode-speed-and-overflow',{owner:base+[mode]},8
    yield 'fractional-cancellation-and-group-order',{owner:[E('huge speed','buff','charge_speed_pct',1e16,'all_allies'),E('small speed','buff','charge_speed_pct',1,'all_allies'),E('huge slow','buff','charge_speed_pct',-1e16,'all_allies'),E('remove positive','buff','charge_speed_buff_immune',0,'all_allies')]},4

def compare(device,label,body,effects,backend,injected=False):
    context=raw.injected_effects(effects) if injected else c.p.custom_effects(effects)
    observed=[];old_check=BuffManager._condition_ok
    def check(self,conditions,caster,t,eff=None):
        value=old_check(self,conditions,caster,t,eff)
        if caster==body['squad'][0] and 'core_hit' in conditions:observed.append(value)
        return value
    with context:
        compiled=c.a.evaluate({**body,'_compile_gpu_detail':True});old_run=detail_gpu.run;captured={}
        def run(device,programs,script,*args,**kwargs):
            script=copy.deepcopy(script);offset=sum(row[1]==2 for row in script)
            for who in range(5):
                script.append([body['duration'],2,103,who,20,offset+who*2,0,0])
                script.append([body['duration'],2,103,who,8,offset+who*2+1,0,0])
            result=old_run(device,programs,script,*args,**kwargs);captured['stats']=result['queries'][0][offset:];return result
        with patch.object(detail_gpu,'run',run):gpu=detail_gpu.evaluate_full(device,compiled,module_backend=backend)
        with c.observe() as (states,manager,events),patch.object(BuffManager,'_condition_ok',check):cpu=c.a.evaluate(body)
        rng=list(random.getstate()[1]);bm=manager['bm'];stats={name:bm.get_buffs(name,'__enemy__',body['duration']) for name in body['squad']}
    checks={key:cpu[key]==gpu[key] for key in ('total_damage','members','base_stats','burst_timeline','seed','burst_gauge_mode','shooting_policy')}
    checks['final_random_state']=rng==gpu['_random_state'];errors=[]
    for i,name in enumerate(body['squad']):
        for j,key in enumerate(['charge_speed_pct','charge_dmg_pct']):
            actual=captured['stats'][i*2+j][0];expected=stats[name][key]
            if not math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-10):errors.append([name,key,actual,expected])
    checks['final_charge_stats']=not errors
    if injected:
        expected=body['enemy']['core_px']>=1
        checks['real_core_condition_exercised']=expected in observed
        # Both signs of the authored skill speed are blocked; equipment stays.
        checks['real_immunity_and_exempt_equipment_exercised']=0<stats[body['squad'][0]]['charge_speed_pct']<30
    row=dict(name=label,backend=backend,seed=body['seed'],mode=body['burst_gauge_mode'],passed=all(checks.values()),checks=checks,
             errors=errors,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],all_real_skills_retained=injected)
    if not row['passed']:row.update(cpu_members=cpu['members'],gpu_members=gpu['members'])
    return row

def verify(device,backend='native',quick=False):
    refs=json.loads((ROOT/'research/detail-charge-immunity-cpu-references.json').read_text(encoding='utf-8'));rows=[]
    cases=[(ref['name'],ref['input'],ref['authored_effects'],False) for ref in refs['cases']]
    for label,effects,seconds in dynamic_cases():cases.append((label,c.body_for(c.NAMES,seconds,True),effects,False))
    if not quick:
        for core in (0,50,.999,1):
            for seed in ((0,12345) if core in (0,50) else (0,)):
                name='리버렐리오';body=c.body_for([name,'리타','크라운','앨리스','모더니아'],35 if core in (0,50) else 5,True)
                body.update(seed=seed,shooting_policy='character',burst_policy='rules');body['enemy']['core_px']=core
                body['profile']['chars'][name]['equip_skills']['charge_speed_pct']=[4.3,4.3,6.2]
                effects={'리타':[E('verification skill increase','buff','charge_speed_pct',80,'all_allies'),E('verification skill reduction','buff','charge_speed_pct',-35,'all_allies')]}
                cases.append(('raw-liberalio-core-'+str(core),body,effects,True))
    for label,template,effects,injected in cases:
        for mode in (('fixed',) if quick else ('fixed','accumulate')):
            body=copy.deepcopy(template);body.update(seed=body.get('seed',0),burst_gauge_mode=mode,_debug_random_state=True)
            try:row=compare(device,label,body,effects,backend,injected)
            except Exception as error:row=dict(name=label,backend=backend,mode=mode,passed=False,error=str(error))
            rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx','both'],default='both');p.add_argument('--quick',action='store_true');p.add_argument('--output',default='research/detail-charge-immunity-verification.json');args=p.parse_args();device=Cuda()
    try:rows=sum((verify(device,b,args.quick) for b in (('native','ptx') if args.backend=='both' else (args.backend,))),[])
    finally:device.close()
    files=['scripts/verify-charge-immunity-detail.py','scripts/audit-charge-immunity.py','research/detail-charge-immunity-cpu-references.json','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(row['passed'] for row in rows),cases=rows,
        cpu_trace_used_as_gpu_input=False,scope='Charge-speed immunity, source-group rounding and overflow conversion in complete independent squads. Raw Liberalio with core/no-core and authored signed speed inputs; Red Hood still rejects pierce_range.',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
