"""Bounded, batch-position-independent private control-state validation."""
import math,struct
from portable_specs import LIMITS as L
from portable_charge_control_specs import OWNER_BASE,CLICK_BASE,WORDS


def validate_state(block,policy):
    assert len(policy)==WORDS,'Partial control policy shape'
    mask=policy[5] if policy[1]==2 else 0
    for who in range(5):
        at=L['WORLD_CONTROL_STATE_BASE']+who*32;row=block[at+17]
        assert 0<=row<=8,'Control state must contain a bounded logical row, never an input address'
        assert all(block[at+i] in (0,1) for i in (18,19,23)),'Partial control flags'
        if row:
            assert mask&(1<<who) and row<=policy[OWNER_BASE+who*8],'Unknown partial control owner or row'
            assert policy[CLICK_BASE+(who*8+row-1)*16]==1,'Partial state references a non-tap row'
        if block[at+23]:
            last=struct.unpack('<d',struct.pack('<II',*block[at+30:at+32]))[0]
            assert math.isfinite(last) and last>=0,'Nonfinite or negative last full-charge clock'
