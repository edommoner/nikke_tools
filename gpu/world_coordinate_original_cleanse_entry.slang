// Original sampled shots and random recipients consume one ordered MT stream.
#define PORTABLE_COORDINATE_ORIGINAL_CLEANSE
#define WORLD_ALLIED_RNG(s,legacy) csRng(s)
#define WORLD_ALLIED_RNG_FINISH(s) exportCoordinateAlliedRng(s);
#include "world_coordinate_original_stack_entry.slang"
void exportCoordinateAlliedRng(inout Runtime s)
{
    for(uint word=0;word<CS_RNG_WORDS;word++)
        results[s.resourceOutput+P_REVIVAL_RNG_BASE+word]=results[csRng(s)+word];
}
