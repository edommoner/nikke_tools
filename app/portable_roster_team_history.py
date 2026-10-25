"""Strict view of the existing roster team-history overflow protocol.

The GPU retains 1024 leading observations and counts subsequent omissions.
Validate that protocol before passing a copy to the legacy no-overflow decoder.
Full native event totals, state, damage, RNG and packet history stay compared.
"""
import array
CAPACITY=1024
def legacy_view(block,battle,head):
    notes=battle['team_hits'];count=block[head+1];omitted=block[head+5]
    assert count==min(len(notes),CAPACITY),'Roster retained team history length'
    assert omitted==max(0,len(notes)-CAPACITY),'Roster omitted team history count'
    assert not any(block[head+6:head+12]),'Roster reserved team history fields'
    if omitted==0:return block,battle
    copied=array.array('I',block);copied[head+5]=0
    expected=dict(battle,team_hits=notes[:CAPACITY])
    return copied,expected
