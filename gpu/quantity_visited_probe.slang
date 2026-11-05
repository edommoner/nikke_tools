static const uint P_DEFINITIONS = 256U;
#include "quantity_visited.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= commands[0]) return;
    uint input = 1U + id.x * 516U, output = id.x * 1056U;
    for (uint i = 0; i < 1056U; i++) results[output+i] = 0;
    uint steps = commands[input], groups = commands[input+1U], rounds = commands[input+2U];
    if (steps > 512U || groups > P_DEFINITIONS || rounds < 1U || rounds > 2U || commands[input+3U] != 0U)
    { results[output] = 64U; return; }
    for (uint i = 0; i < steps; i++) if (commands[input+4U+i] >= groups)
    { results[output] = 64U; return; }
    for (uint i = steps; i < 512U; i++) if (commands[input+4U+i] != 0U)
    { results[output] = 64U; return; }
    results[output+1U] = steps; results[output+2U] = groups; results[output+3U] = rounds;
    QuantityVisited seen;
    for (uint round = 0; round < rounds; round++)
    {
        seen.initialize(groups);
        uint count = 0;
        for (uint i = 0; i < steps; i++)
        {
            bool fresh = seen.insert(commands[input+4U+i]);
            results[output+16U+round*512U+i] = fresh ? 1U : 0U;
            if (fresh) count++;
        }
        results[output+4U+round] = count;
        for (uint i = 0; i < (groups+31U)/32U; i++) results[output+1040U+round*8U+i] = seen.words[i];
    }
}
