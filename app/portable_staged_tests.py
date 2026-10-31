"""All registered unit tests, in fresh bounded stages of one run transaction."""
from portable_product_programs import configuration as product_configuration
import os
from pathlib import Path
from portable_cpu_tests import complete,run_groups,validate_groups,validate_dependency_files,discovered_cases
from portable_comparison_groups import partition
from portable_staged_preflight import context,exclusive,outside,terminal_cpu_stage


def plan(cli,m,size):
    names=product_configuration(cli.SUITES,m)['tests']
    validate_groups(cli.ROOT,names)
    validate_dependency_files(cli.ROOT,names,included={r['path'] for r in m['files']})
    return [[names[i] for i in indices] for indices in partition(len(names),size)]


def case_plan(cli,m,size,split_pattern,case_group_size):
    groups=plan(cli,m,size)
    if size!=1 or split_pattern not in product_configuration(cli.SUITES,m)['tests']:
        raise ValueError('Case partition requires one registered test file per group')
    ids=[case.id() for case in discovered_cases(cli.ROOT,split_pattern)]
    chunks=[[ids[i] for i in indices] for indices in partition(len(ids),case_group_size)]
    expanded=[];selections=[]
    for group in groups:
        if group==[split_pattern]:
            for chunk in chunks:expanded.append(group);selections.append({split_pattern:chunk})
        else:expanded.append(group);selections.append(None)
    return expanded,selections


def validate_plan(cli,m,c):
    if 'test_groups' not in c:
        if {'test_group_size','test_case_groups','split_test_pattern','test_case_group_size'}&set(c):raise ValueError('Incomplete staged test plan')
        return
    keys={'split_test_pattern','test_case_group_size','test_case_groups'}
    if keys&set(c):
        if not keys<=set(c):raise ValueError('Incomplete staged test case plan')
        expected,selections=case_plan(cli,m,c.get('test_group_size'),c['split_test_pattern'],c['test_case_group_size'])
        if c['test_case_groups']!=selections:raise ValueError('Staged test case coverage changed')
    else:expected=plan(cli,m,c.get('test_group_size'))
    if c['test_groups']!=expected:
        raise ValueError('Staged test registry/partition changed')


def case_selection(c,index):
    return c['test_case_groups'][index] if 'test_case_groups' in c else None


def selected_coverage(rows,selection):
    if selection is None:return all('case_ids' not in row for row in rows)
    return (set(selection)=={row['pattern'] for row in rows}
            and all(row.get('case_ids')==selection[row['pattern']] and row['tests']==len(row['case_ids']) for row in rows))


def run_group(cli,transaction,index,capture):
    from portable_phase_audit import Journal
    from portable_python_dependencies import check
    transaction=Path(transaction).resolve();m,c=context(cli,transaction)
    if ('test_groups' not in c or type(index) is not int or not 0<=index<len(c['test_groups'])):
        raise ValueError('Staged test group outside plan')
    capture=outside(capture,[cli.ROOT,transaction,Path(c['gpu_capture'])]);capture.mkdir(parents=True,exist_ok=False)
    exclusive(transaction/('test-claim-'+str(index)+'.json'),dict(capture=str(capture),nonce=c['nonce'],group_index=index))
    j=Journal(capture/'phases.jsonl')
    try:
        cli.check_records(transaction,cli.load(transaction/'artifacts.json')['files'])
        terminal_cpu_stage(cli,transaction,m,'preflight-plan')
        patterns=c['test_groups'][index]
        validate_groups(cli.ROOT,patterns)
        validate_dependency_files(cli.ROOT,patterns,included={r['path'] for r in m['files']})
        deps=j.invoke('staged_test_dependencies',check,cli.ROOT,patterns)
        exclusive(capture/'python-dependencies.json',deps)
        if not deps['passed']:raise ValueError('Staged test dependencies unavailable')
        # This CLI process is already the wrapper's fresh bounded Job child.
        # Unit tests retain their original group runner, logs and assertions.
        selection=case_selection(c,index)
        rows=j.invoke('staged_test_group',run_groups,cli.ROOT,capture,patterns,cli.write,**(dict(selected_cases=selection) if selection is not None else {}))
        if not complete(rows,patterns) or not selected_coverage(rows,selection):raise ValueError('Staged test group incomplete or failed')
        context(cli,transaction)
        result=dict(mode='staged-preflight-test-group-only',package_id=m['package_id'],
            transaction_nonce=c['nonce'],transaction_sha256=cli.sha((transaction/'transaction.json').read_bytes()),
            group_index=index,patterns=patterns,child_pid=os.getpid(),tests=sum(r['tests'] for r in rows),
            test_group_verified=True,all_cpu_tests_verified=False,calculation_verified=False,gpu_calls=0,driver_load_calls=0)
        if selection is not None:result['selected_cases']=selection
        exclusive(capture/'result.json',result);return result
    except BaseException as error:
        exclusive(capture/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_calls=0));raise
    finally:cli.collect(capture,capture/'artifacts.json')


def admit_tests(cli,m,c):
    """Recheck complete test coverage before native work and again before GPU."""
    validate_plan(cli,m,c);transaction=Path(c['transaction'])
    if 'test_groups' not in c:
        if not complete(cli.load(transaction/'cpu-tests.json'),product_configuration(cli.SUITES,m)['tests']):
            raise ValueError('Staged original CPU tests incomplete')
        return []
    pids=[];stages=[];all_rows=[]
    for index,patterns in enumerate(c['test_groups']):
        claim=cli.load(transaction/('test-claim-'+str(index)+'.json'));proof=Path(claim['capture']).resolve()
        if type(claim.get('group_index')) is not int or claim!=dict(capture=str(proof),nonce=c['nonce'],group_index=index):
            raise ValueError('Staged test claim mismatch')
        artifacts=cli.load(proof/'artifacts.json')['files'];names={r['path'] for r in artifacts}
        required={'result.json','cpu-tests.json','python-dependencies.json','phases.jsonl'}
        required.update(p+suffix for p in patterns for suffix in ('.stdout.log','.stderr.log'))
        if not required<=names:raise ValueError('Staged test artifacts incomplete')
        cli.check_records(proof,artifacts);r=cli.load(proof/'result.json');rows=cli.load(proof/'cpu-tests.json');pid=r.get('child_pid')
        if (r.get('mode')!='staged-preflight-test-group-only' or r.get('package_id')!=m['package_id']
            or r.get('transaction_nonce')!=c['nonce'] or r.get('transaction_sha256')!=cli.sha((transaction/'transaction.json').read_bytes())
            or type(r.get('group_index')) is not int or r['group_index']!=index or r.get('patterns')!=patterns
            or r.get('test_group_verified') is not True or r.get('all_cpu_tests_verified') is not False
            or r.get('calculation_verified') is not False or any(type(r.get(k)) is not int or r[k]!=0 for k in ('gpu_calls','driver_load_calls'))
            or type(pid) is not int or pid<=0 or pid in pids or not complete(rows,patterns)
            or any(row.get('runner_pid')!=pid for row in rows)
            or type(r.get('tests')) is not int or r['tests']!=sum(row['tests'] for row in rows)
            or cli.load(proof/'python-dependencies.json').get('passed') is not True):
            raise ValueError('Staged test group identity/coverage mismatch')
        selection=case_selection(c,index)
        if not selected_coverage(rows,selection) or (r.get('selected_cases')!=selection if selection is not None else 'selected_cases' in r):
            raise ValueError('Staged test case receipt coverage mismatch')
        envelope=terminal_cpu_stage(cli,proof,m,'preflight-test-group')
        if envelope.get('containment_verified') is True and envelope['child_pid']!=pid:
            raise ValueError('Staged test Job PID mismatch')
        stages.append(dict(capture=str(proof),**envelope,test_files=cli.file_records(proof,names|{'artifacts.json'})))
        pids.append(pid);all_rows.extend(rows)
    if 'test_case_groups' not in c:
        if not complete(all_rows,product_configuration(cli.SUITES,m)['tests']):raise ValueError('Staged test coverage incomplete')
    else:
        ids=[test for row in all_rows if row['pattern']==c['split_test_pattern'] for test in row.get('case_ids',[])]
        if ids!=[case.id() for case in discovered_cases(cli.ROOT,c['split_test_pattern'])]:
            raise ValueError('Staged original test IDs not covered exactly once')
    return stages
