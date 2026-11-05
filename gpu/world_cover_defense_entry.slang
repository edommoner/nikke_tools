// Opt-in independent cover DEF in the existing full original battle executor.
#define PORTABLE_COVER_DEFENSE
#define PORTABLE_CUSTOM_COMPOSED_ENTRY
#include "cover_defense_layout.slang"
#include "world_coordinate_typed_history_entry.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    executeComposedCoordinateEvents(runtimeStates[id.x],id);
    uint output=id.x*P_OUTPUT_WORDS;
    if(results[output]!=0)return;
    // Same final recipient-order observation; no second battle execution.
    for(uint i=0;i<runtimeStates[id.x].orderedCount;i++)
    {
        uint slot=runtimeStates[id.x].orderedRows[i];
        storeNumber(output+P_RECIPIENT_ORDER_BASE+slot*2,carrierOrder(runtimeStates[id.x],slot));
    }
    for(uint i=0;i<CDF_DEPTH*CDF_SNAPSHOT_WORDS;i++)results[output+CDF_OUTPUT_BASE+CDF_SNAPSHOT_BASE+i]=0;
}
