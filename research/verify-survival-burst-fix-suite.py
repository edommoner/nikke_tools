"""Source-bound survival and burst regressions with one warm GPU interpreter."""
import argparse,hashlib,importlib.util,json
from contextlib import redirect_stdout
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('burst_fix_survival','scripts/verify-staged-survival.py')
burst=load('burst_fix_reference','scripts/verify-burst-stage-detail.py')
ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--focus-b1',action='store_true');args=ap.parse_args()
files=list(json.loads((ROOT/'research/detail-staged-survival-initial-quick.json').read_text(encoding='utf-8'))['source_sha256'])
files+=['research/verify-survival-burst-fix-suite.py','scripts/verify-burst-stage-detail.py','scripts/verify-control-detail.py','research/detail-coverage-burst-gauge.json','research/detail-coverage-burst-stage.json']
if args.backend=='ptx':files=[p for p in files if 'detail_effects-sm86.' not in p]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
def heal_fixtures():
    for target in ('allies_lowest_hp:1','allies_top_atk:2','allies_lowest_hp_excl:2'):
        b=m.v.body(1);b['enemy']['patterns']=[m.lethal(at=100)]
        extra={m.N[0]:[m.B('lazy received healing','heal_received_pct',80,target,event='every:0.2s',duration=1),m.E('make room','instant','current_hp_reduce',50,'all_allies',event='every:0.3s',max_trigger=1),m.E('delayed heal','instant','heal_hp_pct',10,'all_allies',event='every:0.4s',max_trigger=1)]}
        yield 'healing-query-'+target,b,extra
def repeated_fixtures():
    names={'raw-mode-모더니아-True','raw-new-라푼젤-death','raw-new-앤 : 미라클 페어리-death','raw-new-마나-death'}
    for name,b,extra in m.fixtures():
        if name not in names:continue
        b['duration']=180
        for p in b['enemy']['patterns']:p['until']={'time':180};p['spec'].update(hits=3,interval=55)
        yield name+'-180-repeated',b,extra
before=json.loads((ROOT/'research/detail-coverage-burst-gauge.json').read_text(encoding='utf-8'))
current=json.loads((ROOT/'research/detail-coverage-burst-stage.json').read_text(encoding='utf-8'))
was={x['character'] for x in before['results'] if x['supported']}
burst_count=2*len(list(burst.scenarios()))+2*sum(x['supported'] and x['character'] not in was for x in current['results'])
groups=[('burst',None),('heal',list(heal_fixtures())),('full',list(m.fixtures())),('regression',list(m.v.fixtures(False))),('long',list(m.v.long_fixtures()))]
if args.focus_b1:groups=[x for x in groups if x[0] in ('heal','full')]
if args.backend=='native':groups.append(('repeated-long',list(repeated_fixtures())))
device=m.v.v.v.Cuda()
try:
    for label,planned in groups:
        print('Running '+args.backend+' '+label,flush=True);rows=[]
        prefix='b1' if args.focus_b1 else 'burstfix'
        path=ROOT/f'research/detail-survival-{prefix}-{args.backend}-{label}.json'
        with path.with_suffix('.log').open('w',encoding='utf-8') as log,redirect_stdout(log):
            if label=='burst':rows=burst.verify(device,args.backend);expected=burst_count
            else:
                expected=len(planned)
                for name,b,extra in planned:
                    try:
                        row=m.compare(device,name,b,extra,args.backend)
                        if label=='repeated-long':row['positive_control']=row['incoming_hits']>=2 and bool(row['cpu_revives']);row['passed'] &= row['positive_control']
                    except Exception as error:row=dict(name=name,passed=False,error=repr(error));print(json.dumps(row),flush=True)
                    rows.append(row)
                    if not row['passed']:break
        assert hashes=={p:sha(p) for p in files}
        passed=len(rows)==expected and all(x['passed'] for x in rows)
        report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=passed,objective_complete=False,abi=m.g.DETAIL_ABI,stage_only=True,focused_b1=args.focus_b1,planned_cases=expected,not_run_cases=expected-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if not passed:raise SystemExit(1)
        print('Passed '+args.backend+' '+label+' '+str(len(rows)),flush=True)
finally:device.close()
