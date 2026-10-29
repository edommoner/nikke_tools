"""Full CPU admission followed by a byte-frozen handoff, never execution.

Uses the original owner's staged and saved-link auditors. No native battle,
compiler, execution claim or GPU consumer is introduced here.
"""
import json,os,sys,time
from pathlib import Path
from portable_admission_readset import ReadSet
from portable_admission_snapshot import INVENTORY,binding,canonical,digest,freeze,hex_string
from portable_staged_preflight import exclusive

SCHEMA='prepared-admission-evidence-v1'


def cached_owner_modules(controller,owner):
    """Previously imported audit helpers must have the owner's exact bytes."""
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        path=Path(filename).resolve()
        try:relative=path.relative_to(controller)
        except ValueError:continue
        if relative.parts[0] not in ('app','research') or not (owner/relative).is_file():continue
        if path.read_bytes()!=(owner/relative).read_bytes():
            raise ValueError('Cached audit helper differs from original owner: '+str(relative))


def unclaimed(transaction,capture):
    if os.path.lexists(transaction/'gpu-execution-claimed.json') or os.path.lexists(capture):
        raise ValueError('Preparation requires the original unconsumed GPU attempt')


def prepare(cli,owner_root,expected_owner_id,transaction,request,out):
    owner_root=Path(owner_root).resolve();transaction=Path(transaction).resolve();out=Path(out).resolve()
    if not hex_string(expected_owner_id,64):raise ValueError('External owner package ID required')
    # Reject a wrong external anchor before importing any code from that owner.
    header=cli.load(owner_root/'gpu-package.json')
    if header.get('package_id')!=expected_owner_id or cli.package_id(header)!=expected_owner_id:
        raise ValueError('External owner package ID mismatch')
    if any(out==p or p in out.parents or out in p.parents for p in (owner_root,transaction,cli.ROOT.resolve())):
        raise ValueError('Preparation output must be separate from packages and transaction')
    out.mkdir(parents=True,exist_ok=False);start=time.monotonic();original_path=list(sys.path)
    try:
        with cli.forbid_gpu(),ReadSet() as reads:
            controller=cli.verify_package(cli.ROOT)
            owner_manifest=cli.verify_package(owner_root)
            if (owner_manifest['package_id']!=expected_owner_id or owner_manifest['suite']!=controller['suite']
                or owner_manifest['golden']!=controller['golden'] or cli.is_development(controller)
                or cli.compiler_only(controller) or cli.is_development(owner_manifest) or cli.compiler_only(owner_manifest)):
                raise ValueError('Sealed controller/owner and complete golden must agree')
            cached_owner_modules(cli.ROOT.resolve(),owner_root)
            owner=cli.module(owner_root/'scripts/nikke_gpu.py')
            if owner.ROOT.resolve()!=owner_root:raise ValueError('Original owner root changed')
            c=owner.load(transaction/'transaction.json');capture=Path(c['gpu_capture']).resolve()
            if c['backend']!='cuda':raise ValueError('Prepared saved-CUBIN handoff requires CUDA')
            if out==capture or out in capture.parents or capture in out.parents:raise ValueError('Preparation output overlaps future capture')
            unclaimed(transaction,capture)
            from portable_staged_preflight import admit
            with owner.forbid_gpu():
                staged=admit(owner,owner_manifest,transaction,'cuda',capture)
                linked=owner.saved_linked_admission(owner_manifest,request)
                raw=(transaction/'input.bin').read_bytes()
                input_receipt=owner.transport_input_receipt(owner_manifest,raw,staged['input']['input_words'])
                if input_receipt!=staged['input']:raise ValueError('Audited prepared input changed')
                artifact=Path(linked['artifact']).resolve();image=artifact.read_bytes()
                receipt=linked['receipt']
                if len(image)!=receipt['artifact_bytes'] or digest(image)!=receipt['artifact_sha256']:raise ValueError('Audited CUBIN changed')
                if staged.get('all_native_preflight_verified') is not True:raise ValueError('Native preflight incomplete')
            cached_owner_modules(cli.ROOT.resolve(),owner_root)
            # Include manifests and complete parent-checked source closures,
            # including packages examined by the original chain auditors.
            for row in reads.rows():
                if row['path']!='gpu-package.json':continue
                path=Path(row['root'])/row['path'];m=json.loads(path.read_bytes())
                if m.get('package_id')!=cli.package_id(m):raise ValueError('Observed package identity changed')
                reads.require_package(path.parent,m)
            reads.require_package(cli.ROOT,controller);reads.require_package(owner_root,owner_manifest)
            unclaimed(transaction,capture)
            bind=binding(dict(owner_package_id=expected_owner_id,controller_package_id=controller['package_id'],
                transaction_nonce=staged['transaction_nonce'],input_sha256=input_receipt['input_sha256'],
                artifact_sha256=digest(image),future_capture=str(capture)))
            rows=reads.rows()
        certificate=dict(schema=SCHEMA,binding=bind,owner_root=str(owner_root),transaction=str(transaction),
            request=request,owner_manifest_sha256=next(r['sha256'] for r in rows if Path(r['root'])/r['path']==owner_root/'gpu-package.json'),
            golden_sha256=digest(canonical(owner_manifest['golden'])),staged=staged,linked_receipt=receipt,
            input_source=str(transaction/'input.bin'),artifact_source=str(artifact),
            read_set_sha256=digest(canonical(rows)),read_set_files=len(rows),
            preparation_verified=True,execution_admitted=False,calculation_verified=False,gpu_calls=0,
            scope='Full CPU preparation only; authenticated execution claim and independent post-audit remain required')
        evidence=out/'evidence';evidence.mkdir();cert=evidence/'certificate.json';exclusive(cert,certificate)
        raw_cert=cert.read_bytes();inventory=dict(schema=INVENTORY,binding=bind,files=rows+[
            dict(root=str(evidence),path=cert.name,bytes=len(raw_cert),sha256=digest(raw_cert))])
        exclusive(out/'inventory.json',inventory)
        snapshot=freeze(inventory,out/'snapshot.zip')
        unclaimed(transaction,capture)
        result=dict(schema=SCHEMA,binding=bind,certificate_sha256=digest(raw_cert),snapshot=snapshot,
            preparation_verified=True,execution_admitted=False,calculation_verified=False,gpu_calls=0,
            seconds=time.monotonic()-start)
        exclusive(out/'result.json',result);return result
    except BaseException as error:
        exclusive(out/'failure.json',dict(schema=SCHEMA,error=type(error).__name__+': '+str(error),
            preparation_verified=False,execution_admitted=False,calculation_verified=False,gpu_calls=0))
        raise
    finally:sys.path[:]=original_path
