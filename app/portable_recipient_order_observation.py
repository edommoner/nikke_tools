"""Read the shared runtime's final recipient order; never select recipients."""
from pathlib import Path
from portable_coordinate_typed_specs import INPUT_WORDS,OUTPUT_WORDS
SOURCE='gpu/world_coordinate_typed_ordered_history_entry.slang'

def shader():
    return '''// Existing battle executor, followed only by final recipient-order readback.
#define PORTABLE_CUSTOM_COMPOSED_ENTRY
#include "world_coordinate_typed_history_entry.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    executeComposedCoordinateEvents(runtimeStates[id.x],id);
    uint output=id.x*P_OUTPUT_WORDS;
    if(results[output]!=0) return;
    for(uint i=0;i<runtimeStates[id.x].orderedCount;i++)
    {
        uint slot=runtimeStates[id.x].orderedRows[i];
        uint64_t order=carrierOrder(runtimeStates[id.x],slot);
        storeNumber(output+P_RECIPIENT_ORDER_BASE+slot*2,order);
    }
}
'''

def check_layout(root):
    from portable_skill_history import check_layout as history
    history(root)
    if (Path(root)/SOURCE).read_text(encoding='utf-8')!=shader():
        raise ValueError('Recipient-order observation entry changed')

def metadata(value):
    """Only the explicit observation entry may opt into these output words."""
    return dict(value,ordered_recipients=True)
