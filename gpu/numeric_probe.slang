#include "binary64.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;

[shader("compute")]
[numthreads(1, 1, 1)]
void numericProbe(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= commands[0]) return;
    uint at = 1 + id.x * 5;
    uint64_t a = uint64_t(commands[at+1]) | (uint64_t(commands[at+2]) << 32);
    uint64_t b = uint64_t(commands[at+3]) | (uint64_t(commands[at+4]) << 32);
    uint op = commands[at];
    uint64_t value = op == 1 ? f64Add(a, b) : op == 2 ? f64Add(a, b ^ F64_SIGN) : op == 3 ? f64Mul(a, b) : op == 4 ? f64Div(a, b) : op == 5 ? uint64_t(f64Less(a, b)) : uint64_t(f64Equal(a, b));
    results[id.x*2] = uint(value);
    results[id.x*2+1] = uint(value >> 32);
}
