"""Check current source without treating historical battle proofs as current."""
import hashlib,json
from pathlib import Path
from portable_slang_generation import source_hashes
from portable_product_programs import configuration,registered_golden


def check(root,cli,suite,*,product_program=None):
    root=Path(root).resolve()
    if suite not in cli.SUITES:raise ValueError('Unknown source baseline suite')
    manifest=None
    if (root/'gpu-package.json').exists():manifest=cli.verify_package(root)
    selection=dict(suite=suite)
    if product_program is not None:selection['product_program']=product_program
    elif manifest is not None and manifest['suite']==suite:selection=manifest
    if manifest is not None and manifest['suite']==suite and selection.get('product_program')!=manifest.get('product_program'):
        raise ValueError('Requested product program differs from active package')
    config=configuration(cli.SUITES,selection)
    registered=registered_golden(root,config,allow_unsealed=manifest is not None and manifest.get('purpose')=='development')
    actual=source_hashes(root,config['source'])
    registered_current=registered is not None and registered.get('source_sha256')==actual
    origin='registered-golden'
    if not registered_current:
        if manifest is None or manifest.get('purpose')!='development':
            raise ValueError('Registered source baseline is stale: '+suite)
        # Parent/peer checks may use this source proof only when every file
        # belongs to the verified active development closure. This does not
        # transplant a peer battle's output, native hashes or certificate.
        active=manifest['golden'].get('source_sha256',{})
        if not actual or any(active.get(name)!=digest for name,digest in actual.items()):
            raise ValueError('Requested source is outside the verified development closure: '+suite)
        origin='verified-development-closure'
    result=dict(schema='source-baseline-check-v1',suite=suite,verified=True,
        origin=origin,registered_source_current=registered_current,
        source_sha256=actual,package_id=manifest['package_id'] if manifest else None,
        active_suite=manifest['suite'] if manifest else None,
        calculation_verified=False,gpu_execution_verified=False,gpu_calls=0,
        scope='Source identities only; historical golden/certificate and execution checks remain separate')
    if 'product_program' in selection:result['product_program']=selection['product_program']
    return result


def inventory(root,cli):
    """Group registered historical baselines without native calls or generation."""
    root=Path(root).resolve()
    if (root/'gpu-package.json').exists():
        raise ValueError('All-registered source inventory requires the producer checkout')
    groups={}
    for name,c in cli.SUITES.items():
        if c.get('development_only') or c.get('compiler_only') or not c.get('source') or not c.get('golden'):continue
        groups.setdefault((c['source'],c['golden']),[]).append(name)
    sources={};rows=[];counts=dict(current=0,stale=0,unavailable=0)
    for (source,golden),names in sorted(groups.items()):
        row=dict(suites=sorted(names),source=source,golden=golden)
        try:
            if source not in sources:
                try:sources[source]=(source_hashes(root,source),None)
                except (OSError,ValueError) as e:sources[source]=(None,type(e).__name__+': '+str(e))
            actual,error=sources[source]
            if error is not None:raise ValueError(error)
            registered=json.loads((root/golden).read_text(encoding='utf-8'))
            if not isinstance(registered,dict) or not isinstance(registered.get('source_sha256'),dict):
                raise ValueError('Registered golden has no source closure')
            expected=registered['source_sha256']
            row['status']='current' if expected==actual else 'stale'
            row['changed_files']=sorted(name for name in set(expected)|set(actual) if expected.get(name)!=actual.get(name))
        except (OSError,ValueError,TypeError) as e:
            row.update(status='unavailable',reason=type(e).__name__+': '+str(e))
        counts[row['status']]+=1;rows.append(row)
    identities=[(source,golden,sorted(names)) for (source,golden),names in sorted(groups.items())]
    return dict(schema='registered-source-closure-inventory-v1',audit_completed=True,
        scope='Distinct registered nondevelopment/noncompiler source+golden pairs; source identities only',
        counts=counts,baseline_pairs=len(rows),unique_source_entries=len(sources),
        registered_names=sum(len(r['suites']) for r in rows),
        all_registered_source_current=bool(rows) and counts['current']==len(rows),
        registry_selection_sha256=hashlib.sha256(json.dumps(identities,ensure_ascii=False).encode()).hexdigest(),
        auditor_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,
        gpu_calls=0,native_battle_calls=0,compiler_invocations=0,
        calculation_verified=False,full_goal_complete=False)
