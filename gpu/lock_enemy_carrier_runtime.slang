// Only selection is new: carrier activation/expiry/removal stay in MODE19.
void lockEnemyCarrierCapture(inout Runtime s,uint row,uint64_t when,uint index)
{
    physicalLockPulse(s,row,when);if(s.error!=0)return;
    // Obtain an ordinary actor-set lease, initially empty. No private pool.
    actorSetCapture(s,0,index);if(s.error!=0)return;
    uint pulse=PL_PULSE_AT(s,s.lockPulseCount-1);
    if(results[pulse+3]==0xffffffffU)return;
    if(s.locks.count==0){s.error=64;return;}
    uint slot=s.locks.slots[s.locks.count-1],generation=s.locks.generations[s.locks.count-1];
    uint binding=actorBinding(s,slot),at=actorPoolSet(s,index);
    if(results[actorPoolAt(s,slot)+1]==0||results[actorPoolAt(s,slot)]!=generation||commands[binding]!=results[pulse+3]||commands[binding+1]!=results[pulse+4]||generation!=results[pulse+5]){s.error=64;return;}
    results[at]=1;results[at+1+slot/32]=1U<<(slot%32);
    results[at+8]=slot;results[at+9]=generation;results[at+10]=commands[binding];results[at+11]=commands[binding+1];
}
