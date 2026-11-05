"""Exact descriptor/storage contracts using real shared append functions.

This is a compiler/state boundary proof, never a canonical battle certificate.
"""
import importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_specs import LIMITS as L,FIELDS as F,STATS
s=importlib.util.spec_from_file_location('append_probe_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=115680,OUTPUT=3616)
SOURCE='gpu/resident_append_probe.slang'
STRICT_WIRE_DIMENSIONS=True


def prepare():
    cases=[('empty',0,0,0),('enemy-first',1,0,0),('enemy-last',1,511,0),('enemy-refresh',1,1,1),
           ('infinite-first',2,0,0),('infinite-last',2,511,0),('infinite-refresh',2,1,1),
           ('watch-duplicate-owner',3,0,0),('watch-all-2048',4,0,0)]
    rows=[]
    for name,op,prefill,refresh in cases:
        count=256 if op==4 else 2 if op==3 else 1
        words=[0]*suite.INPUT;words[:4]=[op,count,prefill,refresh]
        for row in range(count):
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
            words[at+F['OWNER']]=row if op==3 else 0
            words[at+F['STAT']]=STATS['infinite_ammo'] if op==2 else 0
            words[L['HEALTH_DEFINITION_BASE']+row*L['HEALTH_DEFINITION_WORDS']+3]=int(op==1)
            words[at+F['TRIGGER_COUNT']]=8 if op==4 else 2 if op==3 else 0
            for slot in range(words[at+F['TRIGGER_COUNT']]):
                event=L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8
                # Unique immutable watcher keys, or two duplicate keys/owner.
                # Values are descriptor labels, not measured battle history.
                words[event+4]=row*8+slot if op==4 else 1
                words[event+7]=(-11)&0xffffffff
        rows.append(('resident-append/'+name,words,dict(name=name,op=op,prefill=prefill,refresh=refresh)))
    return rows,None


def native_reference(domain):
    # Independent literal list contracts: empty, first, final valid slot,
    # refresh without duplicate, per-owner deduplication, complete descriptor set.
    op=domain['op'];n=domain['prefill'];refresh=domain['refresh'];sentinel=0xffffffff
    enemy=[sentinel]*512;infinite=[sentinel]*512;ordered=[sentinel]*512;watch=[sentinel]*2048
    header=[0,0x41505031,0,0,0,0,0,0x53a09b7e,0x6409ae12,0xa5a5a5a5]+[0]*22
    if op in (1,2):
        members=[0] if refresh else [*range(1,n+1),0]
        ordered[:len(members)]=members
        (enemy if op==1 else infinite)[:len(members)]=members
        header[2 if op==1 else 3]=len(members);header[5]=len(members);header[6]=n+1
    if op in (3,4):
        members=[0,8] if op==3 else list(range(2048));watch[:len(members)]=members;header[4]=len(members)
    return header+enemy+infinite+ordered+watch


def compare(block,domain):
    expected=native_reference(domain)
    assert len(block)==suite.OUTPUT and list(block)==expected,'Resident append state/guard differs'
    return expected


def validate_rejection(block,name):raise AssertionError('Every append descriptor case must execute')
