// Notification observations only. Event selection, activation, timers, resource
// and numeric effects use the same common dispatch on CUDA and Metal.
void initializeWorldSpawn(inout Runtime s)
{
    if(!worldInitialSpawnEnabled(s)) return;
    for(uint i=P_WORLD_SPAWN_HEAD_BASE;i<P_WORLD_SPAWN_TRACE_BASE+P_WORLD_SPAWN_TRACE_COUNT*4;i++) results[s.resourceOutput+i]=0;
    results[s.resourceOutput+P_WORLD_SPAWN_HEAD_BASE]=0x57534e31;
}
void recordWorldSpawn(inout Runtime s,uint owner,uint64_t when)
{
    uint head=s.resourceOutput+P_WORLD_SPAWN_HEAD_BASE,count=results[head+1];
    if(count>=P_WORLD_SPAWN_TRACE_COUNT) { s.error=64;return; }
    uint at=s.resourceOutput+P_WORLD_SPAWN_TRACE_BASE+count*4;results[head+1]=count+1;
    results[at]=owner;storeNumber(at+1,when);results[at+3]=0;
}
