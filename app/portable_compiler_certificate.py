"""Names and exact full-source certificates; never a compiler/cache/driver proof."""
import copy,hashlib,re
PREFIX='compiler-full--'

def alias(baseline):
    if not isinstance(baseline,str) or not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',baseline):raise ValueError('Invalid compiler baseline suite')
    return PREFIX+baseline

def full_family(suite,baseline=None):
    if suite=='compiler-full':return True
    if not isinstance(suite,str) or not isinstance(baseline,str):return False
    try:return suite==alias(baseline)
    except ValueError:return False

def certificate(suite,baseline,raw):
    if not isinstance(baseline.get('entries'),list) or not baseline['entries'] or not baseline.get('input_sha256') or not baseline.get('output_sha256'):
        raise ValueError('Full compiler certificate requires a nonempty Metal battle baseline')
    if not baseline.get('source_sha256') or set(baseline.get('generated_normalized',{}))!={'cuda','metal'}:
        raise ValueError('Paired Metal/CUDA source baseline required')
    alias(suite)
    return dict(schema=1,proof_kind='compiler-source-only',calculation_verified=False,executable_battle_verified=False,
        source_sha256=copy.deepcopy(baseline['source_sha256']),generated_normalized=copy.deepcopy(baseline['generated_normalized']),entries=[],input_sha256=None,
        baseline_suite=suite,baseline_golden_sha256=hashlib.sha256(raw).hexdigest(),
        scope='Exact full world source from the independently audited Metal '+suite+' capture; not CUDA compile/link/cache/battle/resource proof')
