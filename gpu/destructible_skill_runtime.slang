// Definition and all scalar arithmetic come from the existing common runtime.
// A private descriptor owns the extra typed target routing, never an alias to
// enemy body damage. Caller selects an explicit shared scalar context.
void dwExecuteProjectileSkill(inout Runtime s,inout WorldSchedule w,uint bindings,uint count,uint base,uint header,uint descriptor,uint frozen,uint packet,uint64_t when,uint output,uint answer,uint sampled)
{
    uint row=commands[descriptor],attackId=commands[descriptor+1],fullBurst=commands[descriptor+2];
    if(commands[descriptor+3]!=0x44534b31U||row>=s.count||attackId>=0x1000000U||fullBurst>1) { w.error=64;return; }
    for(uint i=4;i<16;i++) if(commands[descriptor+i]!=0) { w.error=64;return; }
    Definition d=readDefinition(s.inputBase,row);
    if(d.kind!=3||d.stat!=0||d.damageRoute!=1||d.damageCount!=1||d.damageHits!=1||d.damagePending!=0||d.damageNormal!=0||d.damageFlags!=0||d.healthScaling!=0||d.quantityFlags!=0||d.owner>=5||!dtQuantity(d.value)) { w.error=64;return; }
    uint64_t coefficient=namedDamageCoefficient(s,row,d.value,when);dtStore(sampled,coefficient);
    if(s.error!=0||f64Zero(coefficient)) { dtStore(sampled+2,0);return; }
    // The enclosing event frame owns target/phase. Do not temporarily rewrite
    // resident fields around an inout query; keep the actual context explicit.
    if(s.target!=0||s.phase!=(fullBurst!=0?5U:0U)) { w.error=64;return; }
    uint64_t amount=damageValue(s,d.owner,coefficient,when,false,s.coreBonus,d.damageFlags,ONE,false,false,row);
    dtStore(sampled+2,amount);
    if(s.error==0) dwAttackProjectiles(s,w,bindings,count,base,header,frozen,packet,d.owner,1,2,attackId,amount,ONE,when,output,answer);
}
