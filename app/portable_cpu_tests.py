"""One CPU-only unittest worker, preserving every selected group and its logs."""
import contextlib,os,re,sys,time,unittest
from pathlib import Path


def validate_groups(root,patterns):
    if len(set(patterns))!=len(patterns):raise ValueError('Duplicate CPU test group')
    for pattern in patterns:
        if not re.fullmatch(r'test_[A-Za-z0-9_]+\.py',pattern) or not (root/'tests'/pattern).is_file():
            raise ValueError('CPU test file missing or invalid: '+pattern)


def run_groups(root,capture,patterns,write):
    """Execute in registry order; failure stops before any later group or GPU."""
    root=Path(root);capture=Path(capture);validate_groups(root,patterns)
    if (capture/'cpu-tests.json').exists():raise FileExistsError('Fresh CPU test receipt required')
    for pattern in patterns:
        for suffix in ('.stdout.log','.stderr.log'):
            if (capture/(pattern+suffix)).exists():raise FileExistsError('Fresh CPU test logs required')
    before_path=list(sys.path);rows=[];loader=unittest.TestLoader()
    try:
        for pattern in patterns:
            started=time.perf_counter()
            with (capture/(pattern+'.stdout.log')).open('x',encoding='utf-8') as stdout,(capture/(pattern+'.stderr.log')).open('x',encoding='utf-8') as stderr,contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
                suite=loader.discover(str(root/'tests'),pattern=pattern)
                result=unittest.TextTestRunner(stream=stderr,verbosity=1).run(suite)
                success=result.wasSuccessful() and result.testsRun>0
                if result.testsRun==0:stderr.write('Required CPU group discovered zero tests\n')
            rows.append(dict(pattern=pattern,exit_code=0 if success else 1,elapsed_seconds=time.perf_counter()-started,
                tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),runner_pid=os.getpid()))
            write(capture/'cpu-tests.json',rows)
            if not success:break
        if not patterns:write(capture/'cpu-tests.json',rows)
    finally:sys.path[:]=before_path
    return rows


def complete(rows,patterns):
    return bool([r.get('pattern') for r in rows]==list(patterns) and all(type(r.get('exit_code')) is int and r['exit_code']==0 and type(r.get('tests')) is int and r['tests']>0 and r.get('failures')==0 and r.get('errors')==0 for r in rows))
