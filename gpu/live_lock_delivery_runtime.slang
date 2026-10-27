// Only recipient selection is new. All quantities/HP/counters/healing use landWorldSkillReceipt.
bool lockDeliveryCapture(inout Runtime s,LandingReceipt r,uint index)
{
    if(!lockPacketRow(s,r.row))return false;
    // lockPacketObserveLoaded has validated the token, snapshot and hit budget.
    uint snap=s.resourceOutput+PL_SNAPSHOTS+(r.lockSnapshot-1)*P_WORLD_ACTOR_SET_WORDS;
    uint ordinal=lockDeliveryIndex(r.hit,results[snap]),slot=0xffffffffU,generation=0;
    if(ordinal!=0xffffffffU)
    {
        uint entry=snap+8+ordinal*4;slot=results[entry];generation=results[entry+1];
        if(slot>=actorPoolCount(s)||results[actorPoolAt(s,slot)]!=generation||results[actorPoolAt(s,slot)+1]==0)
        {s.error=64;return true;} // No guessed retargeting and no silent drop.
        uint binding=actorBinding(s,slot);
        if(results[entry+2]!=commands[binding]||results[entry+3]!=commands[binding+1])
        {s.error=64;return true;}
    }
    uint at=actorPoolSet(s,index);
    if(results[at+5]!=0){s.error=64;return true;}
    for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++)results[at+i]=0;
    if(ordinal!=0xffffffffU)
    {
        results[at]=1;results[at+1+slot/32]=1U<<(slot%32);
        results[at+8]=slot;results[at+9]=generation;
        results[at+10]=commands[actorBinding(s,slot)];results[at+11]=commands[actorBinding(s,slot)+1];
    }
    results[at+5]=1;results[actorPoolHead(s)+7]++;return true;
}
