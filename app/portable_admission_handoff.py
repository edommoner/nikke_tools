"""Frozen admission bytes for the existing CUDA transport, never permission.

External snapshot/certificate anchors must come from authenticated preparation
and the future execution claim. This reader neither makes that claim nor
proves calculation or environment preservation.
"""
import contextlib,copy,json,threading
from pathlib import Path,PurePosixPath,PureWindowsPath
from unittest.mock import patch
from portable_admission_snapshot import Snapshot,binding,canonical,digest,hex_string,relative
from portable_admission_prepare import SCHEMA
from portable_linked_artifact import valid_receipt,STAGE
from portable_device_linker import validate_cubin

_PROVIDER=threading.Lock()


def origin(path):
    if type(path) is not str:raise ValueError('Absolute frozen origin required')
    result=PureWindowsPath(path) if PureWindowsPath(path).is_absolute() else PurePosixPath(path)
    if not result.is_absolute():raise ValueError('Absolute frozen origin required')
    return result


def origin_key(path):
    p=origin(path)
    return ('windows',str(p).casefold()) if isinstance(p,PureWindowsPath) else ('posix',str(p))


class Handoff:
    def __init__(self,cli,path,expected_sha256,*,certificate_sha256,expected_binding,expected_suite,expected_golden,consumer_package_id,header_materials=None):
        if not hex_string(consumer_package_id,64):raise ValueError('Explicit consumer package ID required')
        self.consumer_id=consumer_package_id;self._material_descriptor=copy.deepcopy(header_materials);self._materials=None
        if not hex_string(certificate_sha256,64):raise ValueError('External certificate SHA required')
        self.cli=cli;self.path=path;self.sha=expected_sha256;self.cert_sha=certificate_sha256
        self._binding=copy.deepcopy(binding(expected_binding));self.suite=expected_suite;self._golden=copy.deepcopy(expected_golden)
        self._used=False;self._active=False;self._provider_used=False

    def __enter__(self):
        if self._used:raise RuntimeError('Single-use frozen handoff required')
        self._used=True
        self._archive=Snapshot(self.path,self.sha,expected_binding=self._binding)
        try:
            self._index={};rows=self._archive.meta['files']
            for row in rows:
                key=origin_key(str(origin(row['root'])/row['path']))
                if key in self._index:raise ValueError('Ambiguous frozen source origin')
                self._index[key]=row
            raw=self._archive.read_blob('blobs/'+self.cert_sha);cert=json.loads(raw)
            cert_rows=[r for r in rows if r['sha256']==self.cert_sha]
            if len(cert_rows)!=1 or cert_rows[0]['path']!='certificate.json':raise ValueError('Unique frozen certificate required')
            trace=[{k:r[k] for k in ('root','path','bytes','sha256')} for r in rows if r is not cert_rows[0]]
            trace.sort(key=lambda r:str(origin(r['root'])/r['path']))
            if (cert['schema']!=SCHEMA or cert['binding']!=self._binding
                or type(cert['read_set_files']) is not int or cert['read_set_files']!=len(trace)
                or cert['read_set_sha256']!=digest(canonical(trace))
                or cert['golden_sha256']!=digest(canonical(self._golden))
                or cert['preparation_verified'] is not True or cert['execution_admitted'] is not False
                or cert['calculation_verified'] is not False
                or any(type(cert[k]) is not int or cert[k]!=0 for k in ('gpu_calls','compiler_calls','native_battle_calls','driver_load_calls'))):
                raise ValueError('Frozen preparation certificate mismatch')
            self._cert=cert
            owner_raw=self._read_origin(str(origin(cert['owner_root'])/'gpu-package.json'))
            if digest(owner_raw)!=cert['owner_manifest_sha256']:raise ValueError('Frozen owner manifest mismatch')
            self._owner=json.loads(owner_raw)
            self._package(cert['owner_root'],self._owner,self._binding['owner_package_id'])
            controllers=[]
            for row in rows:
                if row['path']!='gpu-package.json':continue
                m=json.loads(self._archive.read_blob(row['blob']))
                if m.get('package_id')==self._binding['controller_package_id']:
                    self._package(row['root'],m,self._binding['controller_package_id']);controllers.append(m)
            if len(controllers)!=1:raise ValueError('Unique frozen preparation controller required')
            transaction=json.loads(self._read_origin(str(origin(cert['transaction'])/'transaction.json')))
            b=self._binding;staged=cert['staged']
            if (transaction['package_id']!=b['owner_package_id'] or transaction['nonce']!=b['transaction_nonce']
                or transaction['backend']!='cuda' or transaction['gpu_capture']!=b['future_capture']
                or transaction['manifest_sha256']!=cert['owner_manifest_sha256']
                or staged['host']!=transaction['host']
                or staged['calculation_verified'] is not False or type(staged['gpu_calls']) is not int or staged['gpu_calls']!=0
                or origin_key(transaction['package_root'])!=origin_key(cert['owner_root'])
                or origin_key(transaction['transaction'])!=origin_key(cert['transaction'])
                or staged['package_id']!=b['owner_package_id'] or staged['transaction_nonce']!=b['transaction_nonce']
                or origin_key(staged['transaction'])!=origin_key(cert['transaction'])
                or staged['transaction_sha256']!=digest(self._read_origin(str(origin(cert['transaction'])/'transaction.json')))
                or staged['all_native_preflight_verified'] is not True or staged['input']!=transaction['input']
                or staged['input']['input_sha256']!=b['input_sha256']
                or origin_key(cert['input_source'])!=origin_key(str(origin(cert['transaction'])/'input.bin'))):
                raise ValueError('Frozen transaction binding mismatch')
            receipt=cert['linked_receipt']
            if (not valid_receipt(receipt) or receipt['artifact_sha256']!=b['artifact_sha256']
                or receipt['identity']['source_closure']!=self._golden['source_sha256']
                or receipt['identity']['generated_normalized']!=self._golden['generated_normalized']
                or origin_key(cert['artifact_source'])!=origin_key(str(origin(cert['request']['capture'])/'jit-linked.cubin'))):
                raise ValueError('Frozen linked source receipt mismatch')
            # The full original audit established include traversal. Verify that
            # exact authenticated header map, without opening its mutable paths.
            headers=receipt['identity']['headers']
            if type(headers) is not dict or not headers:raise ValueError('Frozen CUDA header closure required')
            missing={name:sha for name,sha in headers.items() if origin_key(name) not in self._index}
            if self._material_descriptor is not None:
                from portable_header_materials import Materials
                self._materials=Materials(self._material_descriptor,self._binding,self.sha,self.cert_sha,missing)
            for name,sha in headers.items():
                if digest(self._header_bytes(name))!=sha:raise ValueError('Frozen CUDA header changed')
            self._cuda=self._archive.read_blob('blobs/'+receipt['identity']['source_sha256'])
            self._image=self._read_origin(cert['artifact_source']);metadata=validate_cubin(self._image)
            if metadata['sha256']!=b['artifact_sha256'] or metadata['bytes']!=receipt['artifact_bytes']:
                raise ValueError('Frozen CUBIN changed')
            self._input=self._read_origin(cert['input_source'])
            actual=self.cli.transport_input_receipt(self._owner,self._input,staged['input']['input_words'])
            if actual!=staged['input']:raise ValueError('Frozen input receipt mismatch')
            self._active=True;return self
        except BaseException:
            try:
                if self._materials is not None:self._materials.close(None,None,None)
            finally:self._archive.__exit__(None,None,None)
            raise

    def _read_origin(self,path):
        row=self._index.get(origin_key(path))
        if row is None:raise ValueError('Frozen source absent: '+path)
        return self._archive.read_blob(row['blob'])

    def _header_bytes(self,name):
        if origin_key(name) in self._index:return self._read_origin(name)
        if self._materials is not None:return self._materials.read(name)
        return self._read_origin(name)

    def _package(self,root,m,expected_id):
        if (m['schema']!=self.cli.SCHEMA or m['package_id']!=expected_id or self.cli.package_id(m)!=expected_id or m['suite']!=self.suite
            or m.get('purpose','sealed')!='sealed' or m.get('selected_cases') or m['golden']!=self._golden):
            raise ValueError('Frozen sealed package/golden mismatch')
        for item in m['files']:
            row=self._index.get(origin_key(str(origin(root)/relative(item['path']))))
            if row is None or any(row[k]!=item[k] for k in ('bytes','sha256')):raise ValueError('Frozen package closure incomplete')

    def _require_active(self):
        if not self._active:raise RuntimeError('Frozen handoff is not active')

    @property
    def certificate(self):
        self._require_active();return copy.deepcopy(self._cert)

    def summary(self):
        self._require_active()
        return dict(schema='prepared-admission-handoff-bytes-v1',binding=copy.deepcopy(self._binding),consumer_package_id=self.consumer_id,
            snapshot_sha256=self.sha,certificate_sha256=self.cert_sha,read_set_files=self._cert['read_set_files'],
            input_bytes=len(self._input),artifact_bytes=len(self._image),cuda_source_bytes=len(self._cuda),
            frozen_header_files=len(self._cert['linked_receipt']['identity']['headers']),
            handoff_bytes_verified=True,execution_admitted=False,calculation_verified=False,
            gpu_calls=0,compiler_calls=0,native_battle_calls=0,driver_load_calls=0,
            scope='Anchored frozen bytes only; authenticated execution ownership and independent GPU post-audit are still required')

    def read_input(self):
        self._require_active();return self._input,self._cert['staged']['input']['input_words']

    def image_for_source(self,raw):
        self._require_active()
        if type(raw) is not bytes or raw!=self._cuda:raise ValueError('Saved CUBIN exact CUDA bytes differ')
        return self._image,copy.deepcopy(self._cert['linked_receipt'])

    @contextlib.contextmanager
    def saved_provider(self,backend,journal):
        """Adapter for shared execute's existing compiler callback; no dispatch.

        A future caller still must authenticate and consume the one execution
        claim before it can call the shared GPU executor under this adapter.
        """
        self._require_active()
        if backend!='cuda':raise ValueError('Frozen CUBIN provider requires CUDA')
        if self._provider_used or not _PROVIDER.acquire(blocking=False):raise RuntimeError('One frozen provider at a time')
        self._provider_used=True;calls=0;supplied=False;provider_active=True
        try:
            import portable_backend
            journal.emit('prepared_handoff','bytes_verified',binding=copy.deepcopy(self._binding),consumer_package_id=self.consumer_id,snapshot_sha256=self.sha,certificate_sha256=self.cert_sha,execution_admitted=False)
            def saved(source,*,artifact_kind=None):
                nonlocal calls,supplied
                self._require_active()
                if not provider_active:raise RuntimeError('Frozen provider is not active')
                calls+=1
                if calls!=1 or artifact_kind!='cubin':raise ValueError('One explicit saved CUBIN load required')
                image,current=journal.invoke('cuda_linked_artifact',self.image_for_source,Path(source).read_bytes())
                target=Path(source).with_suffix('.cubin')
                if target.is_symlink():raise ValueError('Generated CUBIN must be a regular file')
                if target.exists():
                    if target.read_bytes()!=image:raise ValueError('Existing generated CUBIN differs')
                else:
                    with target.open('xb') as stream:stream.write(image)
                journal.emit(STAGE,'verified',receipt=current);supplied=True;return image,current
            def forbidden(*args,**kwargs):raise RuntimeError('Live compiler forbidden for frozen CUBIN')
            with patch.object(portable_backend,'compile_cuda_source',saved),patch.object(portable_backend,'compile_cuda_artifact',forbidden):
                yield
            if calls!=1 or not supplied:raise ValueError('Frozen provider did not supply exactly one CUBIN')
        finally:
            provider_active=False;_PROVIDER.release()

    def __exit__(self,*error):
        self._active=False
        try:
            if self._materials is not None:self._materials.close(*error)
        finally:self._archive.__exit__(*error)
        return False
