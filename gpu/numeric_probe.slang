#include "binary64.slang"
#include "core_probability.slang"
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
    uint status = 0; uint64_t value = 0;
    if (op == 1) value = f64Add(a, b);
    else if (op == 2) value = f64Add(a, b ^ F64_SIGN);
    else if (op == 3) value = f64Mul(a, b);
    else if (op == 4) value = f64Div(a, b);
    else if (op == 5) value = uint64_t(f64Less(a, b));
    else if (op == 6) value = uint64_t(f64Equal(a, b));
    else if (op == 7 || op == 8 || op == 12) value = f64ToI64(a, op == 7 ? 0 : op == 8 ? 1 : 2, status);
    else if (op == 9) value = f64Integral(a, 2);
    else if (op == 10) value = f64FromI64(a);
    else if (op == 11) value = coreProbability(a, status);
    else if (op == 13) value = f64Abs(a);
    else if (op == 14) value = uint64_t(f64Finite(a));
    else status = 5;
    results[id.x*3] = uint(value);
    results[id.x*3+1] = uint(value >> 32);
    results[id.x*3+2] = status;
}
