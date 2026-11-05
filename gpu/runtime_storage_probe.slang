// Compiler-only experiment. No battle math or canonical runtime is changed.
struct ProbeState
{
    uint alive[512];
    uint64_t value[512];
};
RWStructuredBuffer<ProbeState> resident;
RWStructuredBuffer<uint> control;

[noinline]
void updateReference(inout ProbeState state,uint index)
{
    state.alive[index] += 1;
    state.value[index] += uint64_t(state.alive[index]);
}
[noinline]
void updateIndirect(uint lane,uint index)
{
    resident[lane].alive[index] += 1;
    resident[lane].value[index] += uint64_t(resident[lane].alive[index]);
}

[shader("compute")]
[numthreads(1,1,1)]
void storageReference(uint3 id:SV_DispatchThreadID)
{
    uint index=control[id.x*2]&511;
    updateReference(resident[id.x],index);
    control[id.x*2+1]=resident[id.x].alive[index];
}
[shader("compute")]
[numthreads(1,1,1)]
void storageIndirect(uint3 id:SV_DispatchThreadID)
{
    uint index=control[id.x*2]&511;
    updateIndirect(id.x,index);
    control[id.x*2+1]=resident[id.x].alive[index];
}
