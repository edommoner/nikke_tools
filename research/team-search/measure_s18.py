"""Resumable S18 CPU profiles, paired non-interference, bounded evidence."""
import argparse, concurrent.futures, copy, json, os, pathlib, random, shutil, socket, subprocess, sys, threading, time
sys.dont_write_bytecode=True
import bucket_log as b
RESERVE=int(20.5*1024**3); BUDGET=200*1024**2

def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')

def prepare(out):
    import measure_s9 as s9
    inp=s9.INPUT;body=json.loads(pathlib.Path(inp['benchmark']).read_text())[0];body.update(inp['settings']);body['compute_backend']='cpu'
    excluded={tuple(r['members']) for file in ('s9-dataset.jsonl','s1-results.jsonl') for r in s9.read(s9.HERE/file)}
    rng=random.Random(180206);rows=[]
    for name in s9.NAMES:
        while True:
            # Target first gives its burst priority; fillers are uniform random,
            # rejected only by S1 coverage and exact ordered exclusions.
            squad=(name,*rng.sample([n for n in s9.NAMES if n!=name],4))
            if squad not in excluded and s9.s1.covered(squad,s9.CHARS):break
        excluded.add(squad);rows.append(dict(id=len(rows),target=name,members=list(squad)))
    save(out/'body.json',body);save(out/'selection.json',dict(seed=180206,selected=rows,standard_squads_per_character=1))

def evaluate(body,target,logged):
    r=subprocess.run([sys.executable,'-B',str(b.ROOT/'research/team-search/profile_s18.py')],
        input=json.dumps(dict(body=body,target=target,logged=logged)),text=True,capture_output=True,timeout=1800,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if r.returncode:raise RuntimeError(r.stderr[-6000:]+r.stdout[-1000:])
    return json.loads(r.stdout)

def one(row,out):
    path=out/'runs'/f"{row['id']:03}.json"
    if path.exists():
        old=json.loads(path.read_text())
        if old['selection']!=row:raise ValueError('Resume selection mismatch')
        return old
    body=json.loads((out/'body.json').read_text());body['squad']=row['members'];t=time.perf_counter()
    baseline=evaluate(body,row['target'],False);logged=evaluate(body,row['target'],True)
    if baseline['payload']!=logged['payload']:raise AssertionError('Non-interference')
    result=dict(selection=row,non_interference=True,payload_digest=logged['payload_digest'],
        baseline_digest=baseline['payload_digest'],baseline_seconds=baseline['seconds'],logged_seconds=logged['seconds'],
        wall_seconds=time.perf_counter()-t,host=socket.gethostname(),profile=logged['profile'],
        total_damage=baseline['payload']['total_damage'])
    save(path,result);return result

def run(out,workers,limit):
    if shutil.disk_usage(out).free<RESERVE+BUDGET:raise RuntimeError('Storage reserve + peak budget')
    (out/'runs').mkdir(exist_ok=True);stop=threading.Event();samples=[];started=time.perf_counter()
    def monitor():
        while not stop.is_set():
            free=shutil.disk_usage(out).free;samples.append(dict(time=time.time(),free_bytes=free))
            save(out/'storage.json',dict(min_free=min(s['free_bytes'] for s in samples),samples=samples))
            size=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
            if free<RESERVE or size>BUDGET:os._exit(3)
            stop.wait(10)
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    rows=json.loads((out/'selection.json').read_text())['selected'];rows=rows[:limit] if limit else rows
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            for r in pool.map(lambda row:one(row,out),rows):
                print(json.dumps(dict(id=r['selection']['id'],seconds=r['wall_seconds'])),flush=True)
        save(out/'run.json',dict(host=socket.gethostname(),workers=workers,squads=len(rows),reference_runs=2*len(rows),wall_seconds=time.perf_counter()-started))
    finally:stop.set();thread.join()

def build(out):
    from l2_score import target_supported
    selection=json.loads((out/'selection.json').read_text());chars={}
    supplement_selection=out/'supplement/selection.json'
    supplement_rows={v['id']:v for v in json.loads(supplement_selection.read_text())['selected']} if supplement_selection.exists() else {}
    for row in selection['selected']:
        original_row=row
        r=json.loads((out/'runs'/f"{row['id']:03}.json").read_text())
        if r['selection']!=original_row or not r['non_interference'] or r['payload_digest']!=r['baseline_digest']:
            raise AssertionError('Primary profile evidence identity/non-interference')
        standards=[original_row['members']]
        supplemental=out/'supplement/runs'/f"{row['id']:03}.json"
        if supplemental.exists():
            extra=json.loads(supplemental.read_text())
            if extra['selection']!=supplement_rows.get(row['id']):raise AssertionError('Supplement selection identity')
            if r['profile']['casts']!=0 or extra['profile']['casts']<=0 or extra['selection']['target']!=row['target']:
                raise AssertionError('Supplement must repair an unobserved burst, without labels')
            r=extra;row=r['selection'];standards.append(row['members'])
        if r['selection']!=row or not r['non_interference'] or r['payload_digest']!=r['baseline_digest']:
            raise AssertionError('Profile evidence identity/non-interference')
        p=r['profile'];flags=set()
        effects=p['effects']
        for e in effects:
            stat=e.get('stat','');trigger=e.get('trigger',{});target=e.get('target','self')
            if not target_supported(target,[v['target'] for v in selection['selected']]):flags.add('unmodelled_target:'+token(target))
            for label,terms in {'ammo':('ammo','bullet'), 'reload':('reload',), 'attack_speed':('attack_speed','fire_rate'),
                'charge_speed':('charge_speed','charge_time'), 'burst_cycle':('burst_cooldown','burst_charge','burst_stage','burst_reentry','fullburst_duration','gauge'),
                'team_conditioned':('ally','allies','squad','team')}.items():
                raw=json.dumps(e,ensure_ascii=False)
                if (label=='team_conditioned' and any(x in json.dumps(trigger) for x in terms)) or (label!='team_conditioned' and any(x in stat for x in terms)):flags.add(label)
            if e.get('scaling'):flags.add('scaling:'+str(e['scaling']))
            if stat=='atk_caster_based_pct':flags.add('atk_transfer')
            if stat in ('atk_buff_mag_pct','received_dmg_buff_mag_pct'):flags.add('named_buff_amplification')
            if stat in ('accum_split_damage','dealt_fixed_damage'):flags.add('dependent_damage')
        # Estimate each emitted effect/phase's conditional amount from actual
        # recipient query-time integrals. Maximum recipient mean avoids dilution
        # by recipients outside a dynamic target; selection itself is separate.
        buff_groups={}
        for v in p['buffs']:
            d=v['effect'];key=(token(d),v['phase']);amount=v['amount']
            if key not in buff_groups:buff_groups[key]=dict(effect=d,phase=v['phase'],amount={},recipients=[])
            q=buff_groups[key];q['recipients'].append(v['recipient'])
            for k,x in amount.items():
                if abs(x)>abs(q['amount'].get(k,0.)):q['amount'][k]=x
        for q in buff_groups.values():
            if q['effect']['stat']=='atk_caster_based_pct' and 'atk_flat' in q['amount']:
                q['caster_atk_coefficient']=q['amount']['atk_flat']/p['base_stats']['atk']
            mapping={'f1':['normal_atk_dmg_pct'],'f2':['atk_pct','atk_flat','enemy_def_down_pct','enemy_def_down_flat','def_ignore_pct'],'f3':['crit_rate','crit_rate_skill','crit_dmg','crit_dmg_skill','core_dmg_pct'],'f4':['charge_dmg_pct','charge_dmg_mag_pct'],'f5':['atk_dmg_pct','burst_dmg_pct','burst_dmg_aoe_pct','burst_dmg_single_pct','pierce_dmg_pct','armor_break_dmg_pct','dot_dmg_pct','projectile_explosion_dmg','projectile_attachment_dmg','sequential_dmg_pct','part_dmg_pct','intercept_dmg_pct'],'f6':['received_dmg','split_dmg_pct'],'f7':['element_bonus_pct']}
            q['bucket_inputs']={bucket:{k:q['amount'][k] for k in keys if k in q['amount']} for bucket,keys in mapping.items() if any(k in q['amount'] for k in keys)}
        if max(p['reconciliation'])>1e-7:flags.add('context_bucket_residual')
        if p['raw_residual']:flags.add('context_postprocessed_buff_inputs')
        if not p['casts']:flags.add('burst_not_observed')
        if not p['groups']:flags.add('no_direct_hits_observed')
        for kind in p['uncovered']:
            if kind not in ('accum_split_damage','dealt_fixed_damage'):flags.add('unmodelled_hit_kind:'+kind)
        flags.add('burst_cycle_dynamic_effects_unmodelled')
        groups=p['groups']
        for g in groups:
            # Store only scalar metadata needed for independent arithmetic.
            g['weapon']={k:g['weapon'][k] for k in ('damage_coeff','core_dmg_mult','full_charge_mult') if k in g['weapon']}
        import engine_worker
        meta=engine_worker.META[row['target']]
        chars[row['target']]=dict(groups=groups,buffs=list(buff_groups.values()),dependencies=p['dependencies'],
             flags=sorted(flags),effects=effects,base_stats=p['base_stats'],metadata=meta,
             reference=dict(casts=p['casts'],cycles=p['cycles'],phase_seconds=p['phase_seconds']),
             coverage=dict(attributed_effects=len(buff_groups),differential=False,reconciliation=p['reconciliation'],raw_residual=p['raw_residual'],uncovered=p['uncovered']),
             standard_squad=row['members'],standard_squads=standards)
    body=json.loads((out/'body.json').read_text())
    save(out/'profiles.json',dict(schema=1,settings={k:v for k,v in body.items() if k not in ('profile','squad')},characters=chars,
        method='source-attributed; query-time piecewise-constant buff integrals; one fixed standard squad plus a second context only when no burst was observed',
        limitations=['between-query timing','conditional source-hit mix','dynamic burst effects','dynamic targeting flagged']))
    if (out/'profiles.json').stat().st_size>=20*1024**2:raise RuntimeError('Profile size limit')

def token(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('action',choices=['prepare','run','build']);a.add_argument('--out',type=pathlib.Path,required=True);a.add_argument('--workers',type=int,default=20);a.add_argument('--limit',type=int)
    x=a.parse_args();x.out.mkdir(exist_ok=True,parents=True)
    if x.action=='prepare':prepare(x.out)
    elif x.action=='run':run(x.out,x.workers,x.limit)
    else:build(x.out)
if __name__=='__main__':main()
