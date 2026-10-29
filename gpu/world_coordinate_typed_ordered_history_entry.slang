// Existing battle executor, followed only by final recipient-order readback.
#define PORTABLE_RESIDENT_APPEND_PROBE
#include "world_coordinate_typed_history_entry.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    executePortableEvents(runtimeStates[id.x],id);
    uint output=id.x*P_OUTPUT_WORDS;
    if(results[output]!=0) return;
    for(uint i=0;i<runtimeStates[id.x].orderedCount;i++)
    {
        uint slot=runtimeStates[id.x].orderedRows[i];
        uint64_t order=carrierOrder(runtimeStates[id.x],slot);
        storeNumber(output+P_RECIPIENT_ORDER_BASE+slot*2,order);
    }
}
