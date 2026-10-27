"""Transport wire limits shared by Python validation and generated Swift guard."""
import hashlib
from pathlib import Path
MAX_INPUT_WORDS=131072
LARGE_OUTPUT_WORDS=(655360,786432,806912,1048576,1310720,1507328,1769472,1769856,2032000,2064786)
MAX_OUTPUT_WORDS=max(LARGE_OUTPUT_WORDS)

def metal_guard(widths=LARGE_OUTPUT_WORDS):
    terms=' || '.join('outputWords == '+str(value) for value in widths)
    return '    guard inputWords > 0 && inputWords <= '+str(MAX_INPUT_WORDS)+' && outputWords > 0 && (outputWords <= 524288 || '+terms+') else { throw ProbeError("Invalid wire layout") }'

def check_metal(root,output_words=None):
    path=Path(root)/'scripts/run-metal-probe.swift';raw=path.read_bytes();text=raw.decode()
    if text.splitlines().count(metal_guard())!=1:raise ValueError('Metal/Python wire admission differs; regenerate the reviewed Swift guard before CPU preparation')
    if output_words is not None and (type(output_words) is not int or output_words<1 or output_words>MAX_OUTPUT_WORDS or output_words>524288 and output_words not in LARGE_OUTPUT_WORDS):raise ValueError('Unregistered Metal output stride')
    return dict(schema='metal-wire-preflight-v1',passed=True,swift_sha256=hashlib.sha256(raw).hexdigest(),input_word_limit=MAX_INPUT_WORDS,output_word_limit=MAX_OUTPUT_WORDS,large_output_words=list(LARGE_OUTPUT_WORDS),selected_output_words=output_words,gpu_calls=0,scope='Static exact transport guard agreement; no device access, calculation or compiled layout certification')
