"""Read-only query window for unchanged mutation/mode inputs; no battle certificate."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('partial_query_diag_base',ROOT/'research/verify-world-partial-query-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_query_diagnostic import decode,native_misses,compare_misses
from world_frame_native import roster_names
LOWER,UPPER=.2,.8


def prepare():
    rows,_=base.prepare();rows=[r for r in rows if r[0] in ('partial-query-post-hit-mutation','partial-query-callback-mode')];assert len(rows)==2
    packed=array.array('I',[2])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()


def native_reference(domain):
    n=base.native_reference(domain)
    return dict(proof_kind='read-only numeric-query-observation',battle_certified=False,native_context_sha256=cross.digest(n),numeric_query_misses=native_misses(n['partial_query']['queries'],roster_names(domain[0]),lower=LOWER,upper=UPPER))


def compare(block,domain):
    assert block[0]==0
    n=native_reference(domain);compare_misses(decode(block,lower=LOWER,upper=UPPER),n['numeric_query_misses']);return n


def validate_rejection(block,name):raise AssertionError('No raw rejections in diagnostic suite')
