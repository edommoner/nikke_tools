// New final-selection consumer; all event phases/state/serialization stay shared.
#define PORTABLE_RESIDENT_RUNTIME
#define portableEvents legacyRangeRuntimeEvents
#include "event_runtime.slang"
#undef portableEvents
#include "coordinate_math.slang"
#include "coordinate_shape_math.slang"
#include "coordinate_arc_scalar.slang"
#include "coordinate_numeric_v1.slang"
#include "effect_range_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    executeNamedRange(runtimeStates[id.x],id.x);
}
