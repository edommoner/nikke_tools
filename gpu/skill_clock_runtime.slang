// One-shot adjustment of initialized every:Ns clocks. The next interval stays
// unchanged; the ordinary tick loop owns firing, conditions and rescheduling.
[noinline]
void reduceSkillCooldown(inout Runtime s,uint mask,uint64_t value,uint64_t when)
{
    if(mask==0 || f64Zero(value)) return;
    uint64_t factor=larger(0,f64Add(ONE,f64Div(value,HUNDRED)^F64_SIGN));
    for(uint row=0;row<s.count;row++)
    {
        if(s.periodInitialized[row]==0 || (mask&(1U<<definition_owner(s.inputBase,row)))==0) continue;
        uint64_t remaining=larger(0,f64Add(s.periodDue[row],when^F64_SIGN));
        uint64_t next=f64Add(when,f64Mul(remaining,factor));
        // Native remaining clocks retain IEEE overflow/unordered results. They
        // are scheduling state, never damage or integer-conversion quantities.
        // Ordered due checks suppress Inf/NaN; later reductions use max(0,...)
        // in this operand order, matching native recovery from an unordered due.
        s.periodDue[row]=next;
    }
}
