// Existing complete coordinate executor and disjoint cover landing bank.
#define PORTABLE_CUSTOM_COMPOSED_ENTRY
#define PORTABLE_COVER_DEFENSE
#define PORTABLE_PRODUCT_UNSPECIFIED_COVER
#define PORTABLE_COORDINATE_MANUAL_ACTIONS
#define PORTABLE_PRODUCT_MANUAL_COVER_LOG
#include "cover_defense_layout.slang"
#include "product_coordinate_battle_entry.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    executeComposedCoordinateEvents(runtimeStates[id.x],id);
    // Only finished packet snapshot scratch is caller-owned and cleared.
    uint output=id.x*CDF_OUTPUT_WORDS;
    for(uint i=0;i<CDF_DEPTH*CDF_SNAPSHOT_WORDS;i++)results[output+CDF_OUTPUT_BASE+CDF_SNAPSHOT_BASE+i]=0;
}
