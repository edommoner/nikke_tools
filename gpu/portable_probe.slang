// Portability probe only: integer precision, state mutation, target generations,
// and clock epochs. The production damage formula and float64 policy are pending.
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;

struct ProbeState
{
    uint stacks;
    uint generation;
    uint epoch;
    uint due;
    uint expiry;
    uint coefficient;
    uint interval;
    uint active;
    uint64_t total;
};

void registerClock(inout ProbeState state, uint due, uint expiry, uint coefficient, uint interval)
{
    state.epoch += 1;
    state.due = due;
    state.expiry = expiry;
    state.coefficient = coefficient;
    state.interval = interval;
    state.active = 1;
}

void applyStep(inout ProbeState state, uint kind, uint time, uint a, uint b, uint c, uint d)
{
    if (kind == 1) state.stacks = min(state.stacks + a, b);
    else if (kind == 2 && state.generation != a)
    {
        state.generation = a;
        state.stacks = 0;
    }
    else if (kind == 3 && state.generation == a)
        state.total += uint64_t(state.stacks) * uint64_t(b);
    else if (kind == 4) registerClock(state, a, b, c, d);
    else if (kind == 5 && state.active != 0 && state.epoch == a)
    {
        if (time >= state.expiry) state.active = 0;
        else if (time >= state.due)
        {
            state.due += state.interval;
            state.total += uint64_t(state.stacks) * uint64_t(state.coefficient);
        }
    }
    else if (kind == 6) state.active = 0;
}

[shader("compute")]
[numthreads(1, 1, 1)]
void portableProbe(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= commands[0]) return;
    ProbeState state = {};
    state.generation = 1;
    uint base = 1 + id.x * 97;
    for (uint i = 0; i < commands[base]; i++)
    {
        uint at = base + 1 + i * 6;
        applyStep(state, commands[at], commands[at+1], commands[at+2], commands[at+3], commands[at+4], commands[at+5]);
    }
    uint output = id.x * 7;
    results[output] = uint(state.total);
    results[output+1] = uint(state.total >> 32);
    results[output+2] = state.stacks;
    results[output+3] = state.generation;
    results[output+4] = state.epoch;
    results[output+5] = state.due;
    results[output+6] = state.active;
}
