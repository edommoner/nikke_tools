"""Attest current native/GPU session boundaries without widening certification."""
import copy,hashlib,importlib.util,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
SOURCE='2e1a265a58622cde3bdeef9c4bd9c9e3ad0d4e9c'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,v):(P/(n+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(raw):
    text=raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n')
    text='\n'.join(line for line in text.split('\n') if not re.match(r'^\s*#line\b',line))
    text=re.sub(r'"([^"\n]+)"',lambda m:'"'+m[1].replace('\\','/').split('/')[-1]+'"' if '/' in m[1] or '\\' in m[1] or m[1]=='slang-cuda-prelude.h' else m[0],text)
    return hashlib.sha256(text.encode()).hexdigest()

def main():
    m=load('portable-combat-metal');w=load('windows-portable-combat-v48')
    gates=load('portable-session-identity-global-gates');transfer=load('portable-session-identity-transfer-completed')
    assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1149 and len(m['rejected_cases'])==206
    assert len(m['mode_session_cpu_regressions'])==41 and m['known_mode_cpu_differences']==[]
    assert gates['passed'] and gates['complete'] and len(gates['gates'])==21
    assert transfer['passed'] and transfer['remote_turn_status']=='completed' and transfer['parts']==transfer['total_parts']
    assert w['passed'] and w['gpu_execution_verified'] and w['execution']['commit']==SOURCE
    assert w['execution']['exit_code']==0 and not w['execution']['timed_out'] and w['execution']['below_normal_priority'] and w['execution']['timeout_seconds']==120
    assert w['postcheck']['remaining_verification_processes']==0
    for key in ('head','status'):assert w['postcheck']['original_'+key+'_after']==w['execution']['original_'+key+'_before']
    keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
    for key in keys:assert m[key]==w[key],key
    assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
    for key in ('source_sha256','validation_sha256'):
        for path,digest in m[key].items():assert sha(R/path)==digest,path
    generated={}
    for backend,suffix in [('cuda','cu'),('metal','metal')]:
        path=P/'portable-build'/('event_runtime.'+suffix);assert sha(path)==m['generated_sha256'][backend]
        generated[backend]=normalized(path.read_bytes())
        assert generated[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
    save('portable-generated-v48-comparison',dict(passed=True,source_commit=SOURCE,compared_keys=keys,normalized_sha256=generated,all_frame_depth_words_also_equal=True))
    for backend in ('metal','cuda'):
        old=load('portable-session-identity-existing-'+backend+'-parity')
        assert old['passed'] and old['previous_inputs']==1345 and old['current_inputs']==1355
        assert old['all_prior_input_and_output_bytes_equal'] and old['no_output_normalization']
        assert old['source_sha256']==m['source_sha256'] and old['input_sha256']==m['input_sha256'] and old['output_sha256']==m['output_sha256']
    old=json.loads(subprocess.check_output(['git','show','169a6a3:research/portable-combat-metal.json'],cwd=R))
    by_name={c['name']:r for c,r in zip(m['cases'],m['results'])}
    assert all(r==by_name[c['name']] for c,r in zip(old['cases'],old['results']))
    roster=load('portable-roster-battles-metal');prior_roster=json.loads(subprocess.check_output(['git','show','169a6a3:research/portable-roster-battles-metal.json'],cwd=R))
    assert roster['passed'] and len(roster['cases'])==58 and all(c['passed'] and not c['differences'] for c in roster['cases'])
    strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
    assert [strip(c) for c in roster['cases']]==[strip(c) for c in prior_roster['cases']]
    api=load('portable-api-metal');assert api['passed'] and len(api['session_identity_execution'])==4
    for n in ('portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock'):assert load(n)['passed'],n
    spec=importlib.util.spec_from_file_location('session_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    from portable_burst_oracle import observe
    rows=[]
    for case,gpu in zip(v.fixtures(),m['results']):
        if not case.get('mode_session_reference'):continue
        assert not case.get('known_mode_cpu_difference')
        native=observe(case);assert len(native['queries'])==len(gpu['queries'])
        v.contains(gpu['queries'],native['queries'],case['name'])
        for who,expected in native.get('weapon_timings',{}).items():v.contains(gpu['weapons'][who],expected,case['name']+'.physical-clock')
        rows.append(dict(name=case['name'],passed=True,native=native))
    assert len(rows)==41
    save('portable-session-identity-native',dict(passed=True,cases=rows,source_commit=SOURCE,known_mode_cpu_differences=[],cpu_trace_used_as_gpu_input=False))
    counts={'unit':131,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}
    outputs={}
    for name,count in counts.items():
        gate=next(g for g in gates['gates'] if g['name']==name);text=Path(gate['log']).read_text()
        assert gate['exit_code']==0 and f'Ran {count} tests' in text and text.rstrip().endswith('OK')
        outputs[name]=dict(tests=count,output=text)
    save('portable-session-identity-unit-tests',dict(passed=True,tests=131,native_runtime_tests=15,additional_native_tests=10,groups=outputs))
    parity=load('portable-session-end-parity');benchmark=load('portable-session-end-benchmark')
    assert parity['passed'] and parity['positive_inputs']==1149 and parity['all_output_words_equal']
    assert parity['production_source_sha256']==benchmark['production_source_sha256']==m['source_sha256']
    assert benchmark['passed'] and benchmark['production_change_adopted'] is False
    measurements={}
    for name,workload in benchmark['workloads'].items():
        assert all(len(rows)==4 and rows[0]['warmup'] and all(not r['warmup'] for r in rows[1:]) for rows in workload['samples'].values())
        assert len({r['output_sha256'] for rows in workload['samples'].values() for r in rows})==1
        ranges={v:[min(r['transport']['gpu_seconds'] for r in rows[1:]),max(r['transport']['gpu_seconds'] for r in rows[1:])] for v,rows in workload['samples'].items()}
        overlap=max(ranges['redundant'][0],ranges['central'][0])<=min(ranges['redundant'][1],ranges['central'][1])
        measurements[name]=dict(median_gpu_seconds=workload['median_gpu_seconds'],ratio=workload['central_to_redundant_ratio'],ranges=ranges,ranges_overlap=overlap)
    assert all(row['ranges_overlap'] for row in measurements.values())
    audit=load('portable-catalog-readiness')
    assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==29 and audit['full_character_verified']==0
    save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v48.json',scope=m['scope']))
    previous=json.loads(subprocess.check_output(['git','show','169a6a3:research/portable-combat-checkpoint.json'],cwd=R));save('portable-combat-v47-checkpoint',previous)
    cp=copy.deepcopy(previous)
    cp.update(verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE),
              previous_checkpoint=dict(report='portable-combat-v47-checkpoint.json',proof_commit='169a6a3',original_report='portable-combat-checkpoint.json'),
              positive_cases=1149,rejections=206,batched_inputs=1355,unit_tests=131,native_runtime_tests=15,additional_native_tests=10,
              windows_report='windows-portable-combat-v48.json',windows_checks_this_stage=1,windows_execution=w['execution'],windows_postcheck=w['postcheck'],
              cuda_comparison={k:True for k in keys},generated_source_comparison='portable-generated-v48-comparison.json',validation_receipt='portable-session-identity-validation.json',
              existing_parity='portable-session-identity-existing-metal-parity.json',regressions={k:value for k,value in m.items() if k.endswith('_cpu_regressions')},
              unresolved_raw_cpu_mode_cases=[],known_mode_cpu_differences=[],native_session_identity=True,end_callbacks_use_restored_base_capacity=True,
              session_end_added_gpu_arrays=0,session_end_added_gpu_scalars=0,session_end_efficiency_evaluated=True,session_end_efficiency_adopted=False,
              session_end_efficiency_measurements=measurements,session_end_efficiency_decision='Keep the fixed verified source: sample ranges overlap in both workloads.',
              missing_families=audit['missing_families'],normal_ui_connected=False,normal_ui_backend='cpu',all_characters_supported=False,full_goal_complete=False,full_character_verified=0,
              next_work=['Connect stack mutation/init/immunity and remaining lifecycle, world, control and effect families for all 203 characters',
              'Certify all character variants against independent reference behavior before normal UI GPU admission'])
    for k in ('source_sha256','input_sha256','output_sha256','validation_sha256'):cp[k]=m[k]
    save('portable-combat-checkpoint',cp)
    reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v48','portable-generated-v48-comparison','portable-session-identity-existing-metal-parity','portable-session-identity-existing-cuda-parity',
             'portable-session-identity-global-gates','portable-session-identity-transfer-completed','portable-session-identity-timing-order','portable-session-identity-native','portable-session-identity-unit-tests',
             'portable-session-identity-initial-failure','portable-session-end-parity','portable-session-end-benchmark','portable-combat-checkpoint',
             'portable-roster-battles-metal','portable-api-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal',
             'portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-catalog-readiness']
    save('portable-session-identity-validation',dict(passed=True,source_commit=SOURCE,positive_cases=1149,rejections=206,native_mode_cases=41,added_cases=10,api_added_cases=4,
         unit_tests=131,native_runtime_tests=15,additional_native_tests=10,real_profiles=58,unchanged_prior_input_output_cases=1345,windows_runs=1,
         known_mode_cpu_differences=[],efficiency_evaluated=True,efficiency_production_change_adopted=False,full_goal_complete=False,full_character_verified=0,
         artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},
         tool_sha256={str(p.relative_to(R)):sha(p) for p in [P/'verify-session-identity.py',P/'build-session-identity-cases.py',P/'benchmark-session-end.py',P/'run-session-identity-gates.py',P/'seal-session-identity.py']}))
    print('Session identity sealed: 1149/206; native modes 41 without exceptions; full goal remains incomplete')

if __name__=='__main__':main()
