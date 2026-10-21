// Representation and ownership only. Timers, stacks, scalar damage and landing
// callbacks remain in the common executor. Slots are protected against a new
// generation by the existing monotonic add birth ordinal, never truncated.
bool worldPeriodicClock(inout Runtime s,Definition d)
{ return worldPeriodicEnabled(s)&&d.kind==3&&f64Finite(d.interval)&&f64Less(0,d.interval); }
uint periodicDefinitionSnapshot(inout Runtime s,uint row)
{ return s.resourceOutput+P_WORLD_PERIODIC_DEFINITION_BASE+row*38; }
uint periodicPacketSnapshot(inout Runtime s,uint index)
{ return s.resourceOutput+P_WORLD_PERIODIC_PACKET_BASE+index*38; }
uint periodicSnapshotSlot(uint at,uint index)
{ return (results[at+6+index/4]>>((index%4)*8))&255; }
bool periodicSnapshotGeneration(inout Runtime s,uint at,uint slot)
{ return slot<actorPoolCount(s)&&(slot==0||results[actorPoolAt(s,slot)+10]<=results[at+1]); }
bool periodicSnapshotMember(inout Runtime s,uint at,uint slot)
{ return slot<128&&(results[at+2+slot/32]&(1U<<(slot%32)))!=0&&periodicSnapshotGeneration(s,at,slot); }
void initializeWorldPeriodic(inout Runtime s)
{
    if(!worldPeriodicEnabled(s)) return;
    for(uint i=P_WORLD_PERIODIC_DEFINITION_BASE;i<P_WORLD_PERIODIC_HEAD_BASE+16;i++) results[s.resourceOutput+i]=0;
    results[s.resourceOutput+P_WORLD_PERIODIC_HEAD_BASE]=0x57504331;
}
void savePeriodicSnapshot(inout Runtime s,uint at,uint order[128],uint count)
{
    for(uint i=0;i<38;i++) results[at+i]=0;
    results[at]=count;results[at+1]=results[actorPoolHead(s)+4];
    for(uint i=0;i<count;i++)
    {
        uint slot=order[i];results[at+2+slot/32]|=1U<<(slot%32);
        results[at+6+i/4]|=slot<<((i%4)*8);
    }
}
[noinline]
void captureWorldPeriodicDefinition(inout Runtime s,uint row,uint source,bool append)
{
    uint at=periodicDefinitionSnapshot(s,row),order[128],count=0;
    if(append)
        for(uint i=0;i<results[at];i++)
        {
            uint slot=periodicSnapshotSlot(at,i);
            if(periodicSnapshotGeneration(s,at,slot)) order[count++]=slot;
        }
    uint index=0;while(index<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,index)+5]!=0) index++;
    if(index==P_WORLD_ACTOR_SETS) { s.error=64;return; }
    Definition d=readDefinition(s.inputBase,source);
    actorSetCapture(s,33,index,d.damageRoute==0?6:d.damageRoute,d.damageCount,0,d.owner);if(s.error!=0) return;
    uint set=actorPoolSet(s,index);
    for(uint i=0;i<results[set];i++)
    {
        uint slot=results[set+8+i*4];bool found=false;
        for(uint j=0;j<count;j++) if(order[j]==slot) found=true;
        if(!found) { if(count==128) { s.error=64;break; }order[count++]=slot; }
    }
    results[set+5]=0;results[actorPoolHead(s)+7]--;
    if(s.error==0) savePeriodicSnapshot(s,at,order,count);
}
bool worldPeriodicAnyLive(inout Runtime s,uint row)
{
    uint at=periodicDefinitionSnapshot(s,row);
    for(uint i=0;i<results[at];i++)
    {
        uint slot=periodicSnapshotSlot(at,i);
        if(periodicSnapshotGeneration(s,at,slot)&&results[actorPoolAt(s,slot)+1]!=0) return true;
    }
    return false;
}
void storeWorldPeriodicPacket(inout Runtime s,uint at,LandingReceipt r)
{
    if(!worldPeriodicClock(s,readDefinition(s.inputBase,r.row))) return;
    uint index=(at-s.resourceOutput-P_LANDING_STATE_BASE)/P_LANDING_WORDS;
    if(index>=P_LANDINGS) { s.error=64;return; }
    uint from=periodicDefinitionSnapshot(s,r.row),to=periodicPacketSnapshot(s,index);
    for(uint i=0;i<38;i++) results[to+i]=results[from+i];
    results[at+7]=index+1;
}
void captureWorldPeriodicPacket(inout Runtime s,LandingReceipt r,uint index)
{
    if(r.target==0||r.target>P_LANDINGS) { s.error=64;return; }
    uint from=periodicPacketSnapshot(s,r.target-1),at=actorPoolSet(s,index),count=0;
    if(results[from]>128) { s.error=64;return; }
    for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++) results[at+i]=0;
    for(uint i=0;i<results[from];i++)
    {
        uint slot=periodicSnapshotSlot(from,i);
        if(!periodicSnapshotGeneration(s,from,slot)||results[actorPoolAt(s,slot)+1]==0) continue;
        uint entry=at+8+count*4,b=actorBinding(s,slot);results[entry]=slot;results[entry+1]=results[actorPoolAt(s,slot)];results[entry+2]=commands[b];results[entry+3]=commands[b+1];
        results[at+1+slot/32]|=1U<<(slot%32);count++;
    }
    results[at]=count;results[at+5]=1;results[actorPoolHead(s)+7]++;
}
bool worldPeriodicNamedMember(inout Runtime s,uint resident,uint target)
{
    uint definition=s.carrierDefinition[resident];
    return worldPeriodicClock(s,readDefinition(s.inputBase,definition))&&periodicSnapshotMember(s,periodicDefinitionSnapshot(s,definition),target);
}
