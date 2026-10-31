"""Ordinary product request adapter for the existing immutable battle CLI.

No authored effects, CPU schedules or alternate product projection. The first
cohort uses the existing real API fixture; this owner compiles the normal body
product entry only, not the group/target variants or all profiles.
"""
import array,copy,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_detail as product

spec=importlib.util.spec_from_file_location('product_cross',ROOT/'research/summarize-portable-cross-gpu.py')
_cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(_cross)
SOURCE=product.SOURCE
suite=SimpleNamespace(INPUT=product.INPUT_WORDS,OUTPUT=product.OUTPUT_WORDS)
STRICT_WIRE_DIMENSIONS=True
PROGRAM=None

def configure_product(name):
    global PROGRAM,SOURCE,suite
    from portable_product_programs import PROGRAMS
    if not isinstance(name,str) or name not in PROGRAMS:raise ValueError('Unregistered product program')
    config=PROGRAMS[name];PROGRAM=name;SOURCE=config['source']
    suite=SimpleNamespace(INPUT=config['input_words'],OUTPUT=config['output_words'])

def fingerprint(payload):
    # VCS availability/dirty status differs in an unpacked immutable packet.
    # Only persistent oracle hashing omits that stamp; compare() still compares
    # the complete current CPU and GPU payload, including evaluator metadata.
    return _cross.digest({k:v for k,v in payload.items() if k!='evaluator'})

cross=SimpleNamespace(digest=fingerprint,normalized=_cross.normalized)

def prepare():
    from portable_product_programs import body_for_program
    body=body_for_program(ROOT,PROGRAM)
    prepared,run=product.prepare(body)
    source,iw,ow,words,metadata=product.compile_product(prepared)
    if (source,iw,ow)!=(SOURCE,suite.INPUT,suite.OUTPUT):
        raise ValueError('Product request requires a different entry owner')
    rows=[(f'product/{PROGRAM}-{body["duration"]:g}s' if PROGRAM else 'product/miranda-stage0-30s',words,(body,prepared,run,metadata))]
    packed=array.array('I',[len(rows),*words])
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    return product.engine_worker.evaluate(copy.deepcopy(domain[0]))

def compare(block,domain):
    if len(block)!=suite.OUTPUT:raise ValueError('Complete product readback required')
    body,prepared,run,metadata=domain
    expected=native_reference(domain)
    actual=product.decode_payload(body,prepared,run,metadata,block)
    differences=[k for k in sorted(set(actual)|set(expected))
                 if k not in actual or k not in expected or actual[k]!=expected[k]]
    if differences:raise ValueError('Product payload mismatch: '+', '.join(differences))
    return expected
