// Legacy scalar helpers retain GPU-owned input reads. The old array integrator
// is unreachable in this opt-in profile; the same generated arc bodies are used.
#define coordinateLandingV1 legacyArrayCoordinateLandingV1
#include "coordinate_landing_resident_v1.slang"
#undef coordinateLandingV1
#include "coordinate_resident_arc_layout.slang"
#include "coordinate_arc_arena_view.slang"
#include "coordinate_arc_arena_ops.slang"
#include "coordinate_landing_resident_arena_ops.slang"
[noinline]
bool coordinateLandingV1(uint input,uint output)
{
    uint scratch=output+CRA_SCRATCH_OFFSET;
    for(uint i=0;i<CRA_WORDS;i++)results[scratch+i]=0;
    bool valid=arena_coordinateLandingV1(input,output);
    valid=valid&&results[scratch]==0;
    for(uint i=0;i<CRA_WORDS;i++)results[scratch+i]=0;
    return valid;
}
