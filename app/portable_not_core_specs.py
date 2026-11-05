"""Disjoint binary64 state for256 definitions by five native casters."""
BANK0=252952
BANK1=522688
SEEN=524248
SHOT=260656
CELLS0=500
CELLS=1280


def allocate(limits):
    assert limits['DEFINITIONS']*5==CELLS
    limits.update(NOT_CORE_BANK0_BASE=BANK0,NOT_CORE_BANK1_BASE=BANK1,NOT_CORE_SEEN_BASE=SEEN,NOT_CORE_SHOT_BASE=SHOT,NOT_CORE_CELLS0=CELLS0,NOT_CORE_CELLS=CELLS)


def address(definition,owner):
    assert 0<=definition<256 and 0<=owner<5
    i=definition*5+owner
    return (BANK0+i*2 if i<CELLS0 else BANK1+(i-CELLS0)*2),SEEN+i//32,1<<(i%32)
