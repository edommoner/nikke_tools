"""Check current source without treating historical battle proofs as current."""
import json
from pathlib import Path
from portable_slang_generation import source_hashes


def check(root,cli,suite):
    root=Path(root).resolve()
    if suite not in cli.SUITES:raise ValueError('Unknown source baseline suite')
    config=cli.SUITES[suite]
    registered=json.loads((root/config['golden']).read_text(encoding='utf-8'))
    actual=source_hashes(root,config['source'])
    manifest=None
    if (root/'gpu-package.json').exists():manifest=cli.verify_package(root)
    registered_current=registered.get('source_sha256')==actual
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
    return dict(schema='source-baseline-check-v1',suite=suite,verified=True,
        origin=origin,registered_source_current=registered_current,
        source_sha256=actual,package_id=manifest['package_id'] if manifest else None,
        active_suite=manifest['suite'] if manifest else None,
        calculation_verified=False,gpu_execution_verified=False,gpu_calls=0,
        scope='Source identities only; historical golden/certificate and execution checks remain separate')
