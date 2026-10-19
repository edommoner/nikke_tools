// Only representation transport, no battle simulation or host-generated traces.
#include "event_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void landingCodecProbe(uint3 thread : SV_DispatchThreadID)
{
    uint id=thread.x;if(id>=commands[0]) return;
    uint input=1+id*12,output=id*21;
    LandingReceipt r;
    r.row=commands[input];r.target=commands[input+1];r.mask=commands[input+2];r.order=commands[input+3];
    r.amount=loadNumber(input+4);r.when=loadNumber(input+6);
    r.hit=commands[input+8];r.hits=commands[input+9];r.depth=commands[input+10];r.epoch=commands[input+11];
    results[output+20]=validLandingReceipt(r) ? 1 : 0;
    if(!validLandingReceipt(r)) return;
    storeLandingReceipt(output,r);r=loadLandingReceipt(output);
    results[output+8]=r.row;results[output+9]=r.target;results[output+10]=r.mask;results[output+11]=r.order;
    storeNumber(output+12,r.amount);storeNumber(output+14,r.when);
    results[output+16]=r.hit;results[output+17]=r.hits;results[output+18]=r.depth;results[output+19]=r.epoch;
}
