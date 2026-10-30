"""Explicit product CUBIN selection using the existing immutable CLI audit.

This never installs an image as an NVRTC cache entry. Every selected image
retains its original PTX/object/link owners and is re-audited before dispatch.
"""
from contextlib import contextmanager
import importlib.util
from functools import lru_cache
import json
import os
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENV='NIKKE_SHARED_CUDA_ARTIFACTS'
SOURCES=frozenset(('gpu/product_battle_entry.slang',))


@contextmanager
def audit_imports():
    previous=list(sys.path);bytecode=sys.dont_write_bytecode
    sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
    try:yield
    finally:
        sys.path[:]=previous;sys.dont_write_bytecode=bytecode


def descriptor_file():
    value=os.environ.get(ENV)
    if value is None:return None
    path=Path(value)
    if not value or not path.is_absolute() or path.is_symlink() or not path.is_file() or path.stat().st_size>65536:
        raise ValueError('共通CUDAの保存CUBIN設定は既存の絶対ファイルパスで指定してください。')
    return path


def select(source):
    path=descriptor_file()
    if path is None:raise ValueError('Explicit saved CUBIN configuration required')
    document=json.loads(path.read_text(encoding='utf-8'))
    if (type(document) is not dict or set(document)!= {'schema','programs'}
            or type(document['schema']) is not int or document['schema']!=1
            or type(document['programs']) is not dict or not document['programs']
            or not set(document['programs'])<=SOURCES):
        raise ValueError('Invalid product CUBIN descriptor')
    if source not in document['programs']:raise ValueError('この共通CUDA入口の保存CUBINは未準備です: '+source)
    program=document['programs'][source]
    if type(program) is not dict or set(program)!= {'battle_package','request'} or type(program['request']) is not dict:
        raise ValueError('Invalid product CUBIN owner/request')
    request=program['request']
    if set(request) not in ({'package','capture'},{'package','capture','producer_package','producer_capture'}):
        raise ValueError('Invalid product CUBIN provenance paths')
    for value in (program['battle_package'],*request.values()):
        if not isinstance(value,str) or not value or not Path(value).is_absolute() or not Path(value).is_dir():
            raise ValueError('Product CUBIN provenance requires existing absolute directories')
    return program


@lru_cache(maxsize=1)
def proof_cli():
    # Use this runtime's audit code, never execute code from a configured owner.
    with audit_imports():
        spec=importlib.util.spec_from_file_location('_nikke_product_proof_cli',ROOT/'scripts/nikke_gpu.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module


@contextmanager
def saved_program(source,capture):
    program=select(source)
    previous=list(sys.path);bytecode=sys.dont_write_bytecode
    try:
        with audit_imports(),_audited_program(source,capture,program) as receipt:
            audit_path=list(sys.path);audit_bytecode=sys.dont_write_bytecode
            sys.path[:]=previous;sys.dont_write_bytecode=bytecode
            try:yield receipt
            finally:
                sys.path[:]=audit_path;sys.dont_write_bytecode=audit_bytecode
    except (KeyError,TypeError,ImportError) as error:
        raise ValueError('Saved CUBIN execution/audit metadata incomplete: '+str(error)) from error


@contextmanager
def _audited_program(source,capture,program):
    try:cli=proof_cli()
    except ImportError as error:raise ValueError('Product CUBIN audit dependencies unavailable') from error
    from portable_backend import source_hashes
    from portable_phase_audit import Journal
    journal=Journal(capture/'phases.jsonl')
    try:
        with cli.forbid_gpu():
            owner=journal.invoke('product_cubin_owner',cli.verify_package,Path(program['battle_package']))
            if (owner.get('purpose','sealed')!='sealed' or cli.compiler_only(owner)
                    or owner.get('selected_cases') or cli.SUITES[owner['suite']]['source']!=source
                    or owner['golden']['source_sha256']!=source_hashes(source)):
                raise ValueError('Saved product CUBIN owner does not match current battle source')
    except (KeyError,TypeError) as error:
        raise ValueError('Incomplete product CUBIN owner') from error
    cli.write(capture/'linked-artifact-request.json',program['request'])
    cli.write(capture/'artifact-owner.json',dict(package_id=owner['package_id'],source=source))
    started=time.perf_counter()
    journal.emit('product_cubin_admission','entered')
    admitted=False
    try:
        with cli.saved_linked_provider(owner,capture,'cuda',journal) as receipt:
            if receipt is None:raise ValueError('Saved product CUBIN receipt missing')
            journal.emit('product_cubin_admission','returned',elapsed_seconds=time.perf_counter()-started)
            admitted=True
            import portable_backend
            from portable_phase_audit import observe
            with observe(portable_backend,journal):yield receipt
            from portable_linked_artifact import verify_phases
            verify_phases([json.loads(line) for line in journal.path.read_text(encoding='utf-8').splitlines()],receipt)
    except BaseException as error:
        if not admitted:journal.emit('product_cubin_admission','raised',exception=type(error).__name__,elapsed_seconds=time.perf_counter()-started)
        raise
