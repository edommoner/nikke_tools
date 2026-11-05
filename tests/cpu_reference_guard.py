"""Pure CPU fixture stages must not compile or execute shared programs."""
from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def forbid_execution():
    import portable_backend,portable_slang_generation
    def stop(*args,**kwargs):raise RuntimeError('Build/execute forbidden in CPU reference stage')
    with patch.object(portable_backend,'build',stop),patch.object(portable_backend,'execute',stop),patch.object(portable_slang_generation,'build',stop):
        yield


def catalogue_cohort(root,name,adapter=None):
    """Frozen CPU inputs retained from the retired registry, without packaging code."""
    import array,importlib.util,json,sys
    from pathlib import Path
    config=json.loads((Path(root)/'tests/fixtures/cpu-catalogue-cohorts.json').read_text())[name]
    if adapter is None:
        spec=importlib.util.spec_from_file_location('_cpu_cohort_'+name.replace('-','_'),Path(root)/config['script'])
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    rows,_=adapter.prepare_selected(config['frozen_cases'])
    if [r[0] for r in rows]!=config['frozen_cases']:raise AssertionError('Frozen CPU cohort order changed')
    words=array.array('I',[len(rows)])
    for _,case,_ in rows:words.extend(case)
    if sys.byteorder!='little':words.byteswap()
    return config,adapter,rows,words.tobytes()
