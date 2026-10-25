"""Strict views of the existing roster team/fractional overflow protocols.

The GPU retains 1024 team / 2048 fractional leading observations and omissions.
Validate that protocol before passing a copy to the legacy no-overflow decoder.
Full native event totals, state, damage, RNG and packet history stay compared.
"""
import array
CAPACITY=1024
def legacy_view(block,battle,head,*,fractional_head=None):
    if fractional_head is not None:
        block,battle=fractional_view(block,battle,fractional_head)
    notes=battle['team_hits'];count=block[head+1];omitted=block[head+5]
    assert count==min(len(notes),CAPACITY),'Roster retained team history length'
    assert omitted==max(0,len(notes)-CAPACITY),'Roster omitted team history count'
    assert not any(block[head+6:head+12]),'Roster reserved team history fields'
    if omitted==0:return block,battle
    copied=array.array('I',block);copied[head+5]=0
    expected=dict(battle,team_hits=notes[:CAPACITY])
    return copied,expected

def fractional_view(block,battle,head):
    """Validate retained prefix and exact omissions; retain full final state."""
    notes=battle['fractional_hits'];capacity=2048
    assert block[head]==0x57465231,'Roster fractional history magic'
    assert block[head+1]==min(len(notes),capacity),'Roster retained fractional history length'
    omitted=max(0,len(notes)-capacity)
    assert block[head+3]==omitted,'Roster omitted fractional history count'
    assert not any(block[head+4:head+8]),'Roster reserved fractional history fields'
    if not omitted:return block,battle
    copied=array.array('I',block);copied[head+3]=0
    return copied,dict(battle,fractional_hits=notes[:capacity])
