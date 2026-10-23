// Static union with weapon capacity references; no Runtime or wire growth.
bool durationReference(inout Runtime s,uint row)
{ return (commands[s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4+3]&0x80000000U)!=0; }
void initializeDurationTrace(inout Runtime s)
{
#ifdef PORTABLE_DURATION_SCALING_TRACE
    bool enabled=false;for(uint row=0;row<s.count;row++) enabled|=durationReference(s,row);
    if(enabled) { for(uint i=0;i<P_NATIVE_DIAG_WORDS;i++) results[s.resourceOutput+P_NATIVE_DIAG_BASE+i]=0;results[s.resourceOutput+P_NATIVE_DIAG_BASE]=0x44555331U; }
#endif
}
void traceDurationExpiry(inout Runtime s,uint row,uint64_t when,uint64_t base,bool read,bool present,uint64_t count,uint64_t expires)
{
#ifdef PORTABLE_DURATION_SCALING_TRACE
    uint head=s.resourceOutput+P_NATIVE_DIAG_BASE,index=results[head+1];
    if(index>=256) { results[head+2]++;return; }results[head+1]++;
    uint at=head+16+index*16;results[at]=row;results[at+1]=definition_owner(s.inputBase,row);results[at+2]=uint(read);results[at+3]=uint(present);
    storeNumber(at+4,when);storeNumber(at+6,base);storeNumber(at+8,count);storeNumber(at+10,expires);results[at+12]=commands[s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4+3];
#endif
}
[noinline]
uint64_t definitionExpiry(inout Runtime s,uint row,uint64_t when)
{
    uint64_t base=definition_duration(s.inputBase,row);
#ifdef PORTABLE_DURATION_SCALING
    if(durationReference(s,row))
    {
        uint descriptor=commands[s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4+3],key=descriptor&511U,name=(descriptor>>9)&255U;
        bool read=base!=0xbff0000000000000UL,present=false;uint64_t count=0,expires=F64_INF;
        if(read)
        {
            s.sourceTime=when;
            if(key!=0) count=referenceCount(s,definition_owner(s.inputBase,row),key-1,name,false,present);
            expires=f64Add(when,f64Mul(base,present?count:uint64_t(0)));
        }
        traceDurationExpiry(s,row,when,base,read,present,count,expires);return expires;
    }
#endif
    return f64Less(base,0)?F64_INF:f64Add(when,base);
}
uint64_t passiveDefinitionExpiry(inout Runtime s,uint row,uint64_t when)
{
#ifdef PORTABLE_DURATION_SCALING
    if(durationReference(s,row)) return definitionExpiry(s,row,when);
#endif
    return f64Add(when,definition_duration(s.inputBase,row));
}
