// Shared producer cursor. The caller supplies the real actor generation,
// liveness and birth time; this function neither owns nor predicts that state.
// stateAt owns exactly two words, with the same lifetime as its configured slot.
bool nextWorldAddAttack(uint stateAt,uint generation,bool alive,uint64_t born,
                       uint hits,uint64_t interval,uint64_t when,out uint index)
{
    index=0;
    if(generation==0)return false;
    if(results[stateAt]!=generation){results[stateAt]=generation;results[stateAt+1]=0;}
    uint fired=results[stateAt+1];
    if(!alive || fired>=hits)return false;
    // Original pending is born+i*interval. Never accumulate interval on due.
    uint64_t due=f64Add(born,f64Mul(f64FromI64(fired),interval));
    if(!wsReached(when,due))return false;
    index=fired;results[stateAt+1]=fired+1;return true;
}
