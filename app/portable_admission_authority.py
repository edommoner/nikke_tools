"""Authenticate a terminal CPU preparation and own its one original GPU attempt.

No kernel launch or native comparison. Serialized success flags cannot create
an in-process authority. Failed/partial claims are retained, never retried.
"""
import copy,json,os,sys
from pathlib import Path
from portable_admission_snapshot import binding,canonical,digest,file_sha
from portable_admission_prepare import verified_result,unclaimed
from portable_admission_handoff import Handoff
from portable_staged_preflight import exclusive,host
from windows_validation_observer import compare_snapshots

PROTOCOL='snapshot-prepared-v1'
_TOKEN=object()


def is_windows():return os.name=='nt'
def same(a,b):return canonical(a)==canonical(b)
def base_python():return Path(getattr(sys,'_base_executable',sys.executable)).resolve()


class Authority:
    def __init__(self,token,receipt,anchors,transaction,owner,consumer,output):
        if token is not _TOKEN:raise ValueError('Only full preparation authentication creates authority')
        self._token=token;self._receipt=copy.deepcopy(receipt);self._anchors=anchors
        self._transaction=transaction;self._owner=owner;self._consumer=consumer;self._output=output;self._used=False
    @property
    def receipt(self):return copy.deepcopy(self._receipt)


def terminal(cli,controller_root,controller,stage,request):
    """Use the original wrapper recipe, Job timeline and snapshot comparator."""
    saved_path=list(sys.path)
    try:wrapper=cli.module(controller_root/'scripts/run-gpu-packet.py')
    finally:sys.path[:]=saved_path
    plan=cli.load(stage/'recipe.json');facts=cli.load(stage/'execution.json');child=cli.load(stage/'child.json')
    expected=wrapper.recipe(controller['package_id'],'prepare-admission','cuda',stage,plan['original_workspace'],plan['timeout_seconds'],request)
    if not same(plan,expected):raise ValueError('Preparation recipe/request changed')
    if (facts.get('passed') is not True or facts.get('timed_out') is not False
        or any(type(facts.get(k)) is not int or facts[k]!=0 for k in ('child_exit_code','final_child_exit_code'))
        or facts.get('below_normal_priority') is not True
        or type(facts.get('timeout_seconds')) not in (int,float) or not 0<facts['timeout_seconds']<=plan['timeout_seconds']
        or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error'))):
        raise ValueError('Preparation is not a successful bounded CPU stage')
    command=cli.load(stage/'command.json')
    argv=[command['base_python'],str(controller_root/'scripts/run-gpu-packet.py'),'--_child','--capture',str(stage)]
    if (not same(command['argv'],argv) or Path(command['base_python']).resolve()!=base_python()
        or command.get('shell') is not False or command.get('cwd')!=str(controller_root)
        or type(command.get('timeout_seconds')) is not int or command['timeout_seconds']!=plan['timeout_seconds']):raise ValueError('Preparation command identity mismatch')
    if (type(child.get('pid')) is not int or type(child.get('ppid')) is not int
        or child.get('package_id')!=controller['package_id']):raise ValueError('Preparation child identity mismatch')
    rows=[json.loads(line) for line in (stage/'preparation.jsonl').read_text().splitlines()]
    child_rows=[r for r in rows if r.get('pid')==child['pid']]
    if ([r.get('state') for r in child_rows if r.get('stage')=='packet_shared_cli']!=['entered','returned']
        or any(r.get('state')=='raised' for r in child_rows)):
        raise ValueError('Preparation child journal incomplete')
    contained,pid=cli.job_contained(stage,child_rows,memory_limit_bytes=2147483648)
    job=cli.load(stage/'job.json')
    if not contained or pid!=child['pid'] or job['records'][0]['wrapper_pid']!=child['ppid']:
        raise ValueError('Preparation fresh Job/gate/timeline not verified')
    observation=cli.load(stage/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
    if not same(observation['comparison'],comparison) or comparison['missing_existing_processes']:
        raise ValueError('Preparation process preservation not verified')
    after=observation['after']['observed_unix_ns'];wait=facts.get('wait_completed_unix_ns')
    if type(wait) is not int or not 0<=after-wait<=30_000_000_000:raise ValueError('Preparation after observation is late')
    claim=cli.load(controller_root/'packet-stage-claimed-prepare-admission-cuda.json')
    if (set(claim)!={'package_id','capture','created_unix_ns'} or claim.get('package_id')!=controller['package_id'] or claim.get('capture')!=str(stage)
        or type(claim.get('created_unix_ns')) is not int or type(child.get('started_unix_ns')) is not int
        or not claim['created_unix_ns']<=child['started_unix_ns']<=child_rows[0]['wall_time_ns']):
        raise ValueError('Preparation stage ownership mismatch')
    result=cli.load(stage/'stage-result.json');proof=cli.load(stage/'proof/result.json')
    if (type(result.get('schema')) is not int or result['schema']!=1 or result.get('package_id')!=controller['package_id'] or result.get('stage')!='prepare-admission'
        or any(result.get(k) is not True for k in ('bounded_execution_verified','stage_verified','stage_complete','preparation_verified'))
        or any(result.get(k) is not False for k in ('execution_admitted','calculation_verified','compiler_verified','generation_verified','cpu_verified','smoke_verified','full_goal_complete'))
        or type(result.get('gpu_retries')) is not int or result['gpu_retries']!=0
        or not same(result.get('proof_result'),proof)
        or not verified_result(proof,stage/'proof',controller['package_id'],request)):
        raise ValueError('Preparation terminal receipt mismatch')
    preserved=cli.environment_preserved(stage,facts)
    if result.get('whole_stage_process_preservation_verified') is not True or result.get('whole_stage_environment_preservation_verified') is not preserved:
        raise ValueError('Preparation preservation scope mismatch')
    return proof,dict(containment_verified=True,process_preservation_verified=True,
        environment_preservation_verified=preserved,child_pid=pid)


def authenticate(cli,controller_root,stage,*,expected_binding,snapshot_sha256,certificate_sha256,out,header_materials=None):
    if not is_windows():raise ValueError('Execution authority requires the original Windows host')
    b=copy.deepcopy(binding(expected_binding));controller_root=Path(controller_root).resolve();stage=Path(stage).resolve();out=Path(out).resolve()
    # The external controller ID authenticates code before its wrapper imports.
    header=cli.load(controller_root/'gpu-package.json')
    if header.get('package_id')!=b['controller_package_id'] or cli.package_id(header)!=b['controller_package_id']:
        raise ValueError('External preparation controller ID mismatch')
    initial_plan=cli.load(stage/'recipe.json');initial_request=initial_plan['object_request']
    owner=Path(initial_request['owner_package']).resolve();transaction=Path(initial_request['transaction']).resolve();capture=Path(b['future_capture']).resolve()
    if any(out==p or p in out.parents or out in p.parents for p in (controller_root,stage,cli.ROOT.resolve(),owner,transaction,capture)):
        raise ValueError('Authority output must be outside source and preparation')
    unclaimed(transaction,capture)
    if os.path.lexists(cli.ROOT/'gpu-claimed-cuda.json'):raise ValueError('Consumer already owns a GPU attempt')
    out.mkdir(parents=True,exist_ok=False)
    try:
        with cli.forbid_gpu():
            consumer=cli.verify_package(cli.ROOT);controller=cli.verify_package(controller_root)
            if (cli.is_development(consumer) or cli.compiler_only(consumer) or cli.is_development(controller)
                or cli.compiler_only(controller) or consumer['suite']!=controller['suite'] or consumer['golden']!=controller['golden']):
                raise ValueError('Sealed preparation and consumer complete golden differ')
            names=['recipe.json','execution.json','command.json','child.json','job.json','observation.json','preparation.jsonl','stage-result.json','proof/result.json','proof/evidence/certificate.json','proof/inventory.json']
            anchors=[(stage,cli.file_records(stage,names)),(controller_root,cli.file_records(controller_root,['gpu-package.json','packet-stage-claimed-prepare-admission-cuda.json'])),
                (owner,cli.file_records(owner,['gpu-package.json','gpu-claimed-cuda.json'])),(transaction,cli.file_records(transaction,['transaction.json'])),(cli.ROOT,[*consumer['files'],*cli.file_records(cli.ROOT,['gpu-package.json'])])]
            plan=cli.load(stage/'recipe.json');request=plan['object_request']
            if not same(request,initial_request):raise ValueError('Preparation request changed during authentication')
            proof,envelope=terminal(cli,controller_root,controller,stage,request)
            if (proof['binding']!=b or proof['snapshot']['snapshot_sha256']!=snapshot_sha256
                or proof['certificate_sha256']!=certificate_sha256):raise ValueError('External preparation anchors differ')
            owner=Path(request['owner_package']).resolve();transaction=Path(request['transaction']).resolve();capture=Path(b['future_capture']).resolve()
            if request['expected_owner_id']!=b['owner_package_id']:raise ValueError('Original owner external ID mismatch')
            m=cli.verify_package(owner)
            if m['package_id']!=b['owner_package_id'] or m['golden']!=consumer['golden'] or m['suite']!=consumer['suite']:
                raise ValueError('Original sealed owner identity/golden mismatch')
            if any(out==p or p in out.parents or out in p.parents for p in (owner,transaction,capture)):
                raise ValueError('Authority output overlaps original attempt')
            unclaimed(transaction,capture)
            if os.path.lexists(cli.ROOT/'gpu-claimed-cuda.json'):raise ValueError('Consumer already owns a GPU attempt')
            with Handoff(cli,stage/'proof/snapshot.zip',snapshot_sha256,certificate_sha256=certificate_sha256,
                    expected_binding=b,expected_suite=consumer['suite'],expected_golden=consumer['golden'],consumer_package_id=consumer['package_id'],header_materials=header_materials) as handoff:
                cert=handoff.certificate;live=(transaction/'transaction.json').read_bytes()
                if (digest(live)!=cert['staged']['transaction_sha256'] or cert['staged']['host']!=host(cli)
                    or Path(cert['owner_root']).resolve()!=owner or Path(cert['transaction']).resolve()!=transaction
                    or digest((owner/'gpu-package.json').read_bytes())!=cert['owner_manifest_sha256']):
                    raise ValueError('Original transaction/source host changed')
                reservation=dict(package_id=b['owner_package_id'],capture=str(capture),transaction=str(transaction),transaction_nonce=b['transaction_nonce'])
                if not same(cli.load(owner/'gpu-claimed-cuda.json'),reservation):raise ValueError('Original GPU reservation mismatch')
            for root,files in anchors:cli.check_records(root,files)
            unclaimed(transaction,capture)
            receipt=dict(schema='prepared-admission-authority-v1',protocol=PROTOCOL,binding=b,consumer_package_id=consumer['package_id'],
                preparation_package_root=str(controller_root),preparation_stage=str(stage),owner_root=str(owner),transaction=str(transaction),
                header_materials=copy.deepcopy(header_materials),snapshot=str(stage/'proof/snapshot.zip'),snapshot_sha256=snapshot_sha256,certificate_sha256=certificate_sha256,host=cert['staged']['host'],envelope=envelope,
                anchors=[dict(root=str(root),files=files) for root,files in anchors],authority_verified=True,
                execution_admitted=False,calculation_verified=False,gpu_calls=0)
            exclusive(out/'authority.json',receipt)
            anchors.append((out,cli.file_records(out,['authority.json'])))
            return Authority(_TOKEN,receipt,anchors,transaction,owner,cli.ROOT,out)
    except BaseException as error:
        exclusive(out/'failure.json',dict(error=type(error).__name__+': '+str(error),authority_verified=False,execution_admitted=False,calculation_verified=False,gpu_calls=0));raise


def claim(cli,authority):
    """Durably lock the original attempt; serialized receipts cannot call this."""
    if not is_windows() or type(authority) is not Authority or authority._token is not _TOKEN or authority._used:
        raise ValueError('Fresh in-process original-host authority required')
    authority._used=True;r=authority._receipt;b=r['binding'];capture=Path(b['future_capture'])
    try:
        for root,files in authority._anchors:cli.check_records(root,files)
        snapshot=Path(r['snapshot'])
        if snapshot.is_symlink() or not snapshot.is_file() or file_sha(snapshot)!=r['snapshot_sha256'] or host(cli)!=r['host']:
            raise ValueError('Authority snapshot or source host changed before claim')
        if r.get('header_materials') is not None:
            material=Path(r['header_materials']['snapshot'])
            if material.is_symlink() or not material.is_file() or file_sha(material)!=r['header_materials']['sha256']:
                raise ValueError('Authority header materials changed before claim')
        unclaimed(authority._transaction,capture)
        if os.path.lexists(authority._consumer/'gpu-claimed-cuda.json'):raise ValueError('Consumer GPU attempt already claimed')
        record=dict(schema='prepared-execution-ownership-v1',protocol=PROTOCOL,package_id=b['owner_package_id'],nonce=b['transaction_nonce'],capture=str(capture),
            consumer_package_id=r['consumer_package_id'],preparation_package_id=b['controller_package_id'],
            authority=str(authority._output/'authority.json'),authority_sha256=digest((authority._output/'authority.json').read_bytes()),
            snapshot_sha256=r['snapshot_sha256'],certificate_sha256=r['certificate_sha256'])
        # No rollback: a partial publication is a recovery pointer, not a retry.
        exclusive(authority._transaction/'gpu-execution-claimed.json',record)
        exclusive(authority._consumer/'gpu-claimed-cuda.json',record)
        exclusive(authority._output/'claim.json',record)
        return copy.deepcopy(record)
    except BaseException as error:
        exclusive(authority._output/'claim-failure.json',dict(error=type(error).__name__+': '+str(error),partial_claims_retained=True,calculation_verified=False,gpu_calls=0));raise
