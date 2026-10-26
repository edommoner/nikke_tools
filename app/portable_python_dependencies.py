"""Read pinned validation dependencies without installing or changing environments."""
import importlib,importlib.metadata,re

REQUIRED_TESTS=frozenset(('test_coordinate_power_v1.py','test_coordinate_landing_v1.py'))
REQUIREMENTS_FILE='requirements-validation.txt'

def requirements(root,patterns):
    if not REQUIRED_TESTS.intersection(patterns):return []
    rows=[]
    for raw in (root/REQUIREMENTS_FILE).read_text(encoding='utf-8').splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):continue
        match=re.fullmatch(r'(gmpy2)==([0-9][A-Za-z0-9.!+_-]*)',line)
        if match is None:raise ValueError('Validation dependency must be a pinned gmpy2 version')
        name,version=match.groups()
        if rows:raise ValueError('Duplicate validation dependency')
        rows.append(dict(distribution=name,module=name,required_version=version))
    if not rows:raise ValueError('Missing pinned validation dependency')
    return rows

def check(root,patterns):
    rows=[]
    for required in requirements(root,patterns):
        row=dict(required,passed=False,installed_version=None,importable=False)
        try:row['installed_version']=importlib.metadata.version(required['distribution'])
        except importlib.metadata.PackageNotFoundError:row['issue']='missing_distribution'
        else:
            if row['installed_version']!=required['required_version']:row['issue']='version_mismatch'
            else:
                try:
                    module=importlib.import_module(required['module'])
                    row.update(importable=True,module_path=str(module.__file__),loaded_version=str(module.version()),mpfr_version=str(module.mpfr_version()))
                    if row['loaded_version']!=required['required_version']:row['issue']='import_version_mismatch'
                    else:row['passed']=True
                except (ImportError,OSError,AttributeError) as error:
                    row.update(issue='import_failed',error=type(error).__name__+': '+str(error))
        rows.append(row)
    return dict(schema=1,passed=all(row['passed'] for row in rows),dependencies=rows,
                requirements_file=REQUIREMENTS_FILE if rows else None,installation_performed=False,
                gpu_calls=0,calculation_verified=False,scope='Selected validation tests only; package metadata and import availability, not GPU or numerical correctness')
