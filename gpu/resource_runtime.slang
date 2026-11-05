struct ResourceDefinition { uint op, key, flags; uint64_t cap, literal, minimum; };
[ForceInline]
ResourceDefinition resourceDefinition(inout Runtime s, uint row)
{
    uint at=s.inputBase+P_RESOURCE_DEFINITION_BASE+row*10; ResourceDefinition r;
    r.op=commands[at]; r.key=commands[at+1]; r.flags=commands[at+2];
    r.cap=loadNumber(at+4); r.literal=loadNumber(at+6); r.minimum=loadNumber(at+8); return r;
}
// Each GPU invocation owns one disjoint output slice. Resource quantities
// live there throughout execution, avoiding redundant large private arrays.
uint resourceAddress(inout Runtime s, uint pos) { return s.resourceOutput+P_RESOURCE_STATE_BASE+pos*5; }
uint resourceFlags(inout Runtime s, uint pos) { return results[resourceAddress(s,pos)]; }
uint64_t resourceValue(inout Runtime s, uint pos) { uint at=resourceAddress(s,pos)+1; return uint64_t(results[at]) | (uint64_t(results[at+1])<<32); }
uint64_t resourceCap(inout Runtime s, uint pos) { uint at=resourceAddress(s,pos)+3; return uint64_t(results[at]) | (uint64_t(results[at+1])<<32); }
void setResourceValue(inout Runtime s, uint pos, uint64_t value) { storeNumber(resourceAddress(s,pos)+1,value); }
void setResourceCap(inout Runtime s, uint pos, uint64_t value) { uint at=resourceAddress(s,pos); results[at] |= 2; storeNumber(at+3,value); }
// Named effect resources use software binary64. Actual spend is independent
// of subtracting a rounded remainder; modulo truncates the binary64 value
// exactly without a signed-int64 narrowing conversion.
[noinline]
uint resourceModulo(uint64_t value, uint modulus)
{
    if (modulus == 0) return 0xffffffff;
    int exponent = int((value >> 52) & 2047)-1023;
    if (exponent < 0 || f64Zero(value)) return 0;
    uint64_t significand = (value & F64_FRAC) | (uint64_t(1)<<52), rem;
    if (exponent < 52) rem = (significand >> uint(52-exponent)) % uint64_t(modulus);
    else
    {
        rem = significand % uint64_t(modulus);
        [loop] for (int bit = 0; bit < exponent-52; bit++) rem = (rem*2) % uint64_t(modulus);
    }
    return (value & F64_SIGN) != 0 && rem != 0 ? modulus-uint(rem) : uint(rem);
}
uint f64ToPositiveStep(uint64_t value)
{
    uint status; uint64_t n = f64ToI64(value,1,status);
    return status == 0 && n <= 0x7fffffff ? uint(n) : 0;
}
[noinline]
bool resourceCondition(inout Runtime s, uint who, uint kind, uint key, uint64_t arg, int remainder)
{
    uint64_t value = resourceValue(s,who*P_RESOURCE_KEYS+key);
    if (kind == C_GAUGE_ABOVE) return !f64Less(value,arg);
    if (kind == C_GAUGE_BELOW) return f64Less(value,arg);
    if (kind == C_GAUGE_EQ) return f64Equal(value,arg);
    return remainder >= 0 && resourceModulo(value,f64ToPositiveStep(arg)) == uint(remainder);
}
[noinline]
uint64_t effectiveResourceCap(inout Runtime s, uint who, uint key)
{
    uint64_t cap = resourceCap(s,who*P_RESOURCE_KEYS+key); Sum add; add.total = 0; add.correction = 0;
    // Native dispatch scans the active list in insertion order; it does not
    // multiply cap literals by stacks or resolve their recipient predicates.
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint slot = s.orderedRows[pass]; Definition d = residentDefinition(s,slot); ResourceDefinition r = resourceDefinition(s,s.carrierDefinition[slot]);
        if (s.alive[slot] != 0 && d.owner == who && r.op == 4 && r.key == key+1) addSum(add,r.literal);
    }
    cap = f64Add(cap,f64Add(add.total,add.correction));
    if (!f64Finite(cap)) s.error = 16;
    return cap;
}
[noinline]
bool resourceStepBoundary(uint64_t cursor, uint64_t end, uint64_t stepBits, out uint64_t boundary, inout uint error)
{
    boundary = 0;
    uint status; uint64_t q = f64ToI64(f64Div(cursor,stepBits),2,status);
    if (status != 0 || q == F64_SIGN-1) { error = 2; return false; }
    q++;
    uint64_t top = f64ToI64(f64Div(end,stepBits),2,status);
    if (status != 0) { error = 2; return false; }
    // Compare two signed integer bit patterns without implementation-defined casts.
    if ((q ^ F64_SIGN) > (top ^ F64_SIGN)) return false;
    uint64_t step = f64ToI64(stepBits,1,status), sign = q & F64_SIGN, magnitude = sign != 0 ? ~q+1 : q;
    uint64_t limit = sign != 0 ? F64_SIGN : F64_SIGN-1;
    if (status != 0 || step == 0 || magnitude > limit/step) { error = 2; return false; }
    uint64_t product = magnitude*step; if (sign != 0) product = ~product+1;
    boundary = f64FromI64(product);
    uint64_t check = f64ToI64(boundary,1,status);
    if (status != 0 || check != product) { error = 2; return false; }
    return true;
}
[noinline]
bool nextResourceBoundary(inout Runtime s, uint who, uint key, uint64_t cursor, uint64_t end, out uint64_t selected)
{
    bool found = false; selected = 0;
#ifdef PORTABLE_RESOURCE_SCAN_REFERENCE
    for (uint row = 0; row < s.count; row++) for (uint slot = 0; slot < definition_triggerCount(s.inputBase,row); slot++)
    {
        uint at = s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;
        if (definition_owner(s.inputBase,row) != who || commands[at] != 30 || commands[at+4] != key) continue;
#else
    uint encoded = results[s.resourceOutput+P_RESOURCE_STEP_HEAD_BASE+who*P_RESOURCE_KEYS+key];
    while (encoded != 0)
    {
        uint index = encoded-1, row = index/P_TRIGGERS, slot = index%P_TRIGGERS;
        uint at = s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;
        encoded = results[s.resourceOutput+P_RESOURCE_STEP_NEXT_BASE+index];
#endif
        uint64_t boundary;
        if (resourceStepBoundary(cursor,end,loadNumber(at+1),boundary,s.error) && (!found || f64Less(boundary,selected))) { found = true; selected = boundary; }
        if (s.error != 0) return false;
    }
    return found;
}
#ifndef RESOURCE_TRACE_CAPACITY
#define RESOURCE_TRACE_CAPACITY P_TRACE
#define RESOURCE_TRACE_AT(output,index) ((output)+P_RESOURCE_TRACE_BASE+(index)*8)
#endif
#ifndef RESOURCE_TRACE_ENABLED
#define RESOURCE_TRACE_ENABLED(s) ((s).traceMode==1)
#endif
void logResourceNotification(inout Runtime s, uint event, uint who, uint key, uint64_t when, uint64_t boundary, uint output)
{
    if (s.resourceTraceTotal == 0x7fffffff) { s.error = 2; return; }
    s.resourceTraceTotal++;
    if (!RESOURCE_TRACE_ENABLED(s)) return;
    if (s.resourceTraceCount == RESOURCE_TRACE_CAPACITY) { s.error = 8; return; }
    uint index=s.resourceTraceCount++, at = RESOURCE_TRACE_AT(output,index);
    results[at] = event; results[at+1] = who; results[at+2] = key; results[at+3] = 0;
    storeNumber(at+4,when); storeNumber(at+6,boundary);
}
[noinline]
bool initializeResources(inout Runtime s)
{
    for (uint who=0; who<5; who++) for (uint key=0; key<s.resourceCount; key++)
    { uint at=resourceAddress(s,who*P_RESOURCE_KEYS+key); for (uint word=0; word<5; word++) results[at+word]=0; }
    for (uint word=0; word<5*P_RESOURCE_KEYS; word++) results[s.resourceOutput+P_RESOURCE_STEP_HEAD_BASE+word]=0;
    for (uint word=0; word<P_DEFINITIONS*P_TRIGGERS; word++) results[s.resourceOutput+P_RESOURCE_STEP_NEXT_BASE+word]=0;
    for (uint word = 1; word < 8; word++) if (commands[s.inputBase+P_RESOURCE_META_BASE+word] != 0) return false;
    for (uint row = 0; row < s.count; row++)
    {
        Definition d = readDefinition(s.inputBase,row); ResourceDefinition r = resourceDefinition(s,row); uint at = s.inputBase+P_RESOURCE_DEFINITION_BASE+row*10;
        if (commands[at+3] != 0 || r.op > 5 || r.flags > 3) return false;
        if (r.op == 0)
        { for (uint k = 1; k < 10; k++) if (commands[at+k] != 0) return false; if (d.kind >= 9 && d.kind <= 11) return false; }
        else
        {
            if (r.key == 0 || r.key > s.resourceCount) return false;
            if (r.op <= 3 ? d.kind != r.op+8 : d.kind != 4) return false;
            if (!f64Finite(r.cap) || f64Less(r.cap,0) || !f64Finite(r.minimum) || f64Less(r.minimum,0) || f64Less(FOREVER,r.minimum) || !f64Finite(r.literal)) return false;
            if ((r.flags & 1) == 0 && !f64Zero(r.cap)) return false;
            if (r.op != 4 && !f64Zero(r.literal)) return false;
            if (r.op != 2 && r.op != 3 && !f64Zero(r.minimum)) return false;
            if (r.op <= 3 && !f64Finite(d.value)) return false;
        }
        for (uint slot = 0; slot < d.triggerCount; slot++)
        {
            uint event = s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;
            if (commands[event] == 26) s.resourceAmmoObserved = 1;
            if (commands[event] != 30) continue;
            uint key = commands[event+4], step = f64ToPositiveStep(loadNumber(event+1));
            if (key >= s.resourceCount || step == 0 || !f64Equal(f64FromI64(step),loadNumber(event+1)) || commands[event+3] != 0) return false;
            uint index = row*P_TRIGGERS+slot, head = d.owner*P_RESOURCE_KEYS+key;
            results[s.resourceOutput+P_RESOURCE_STEP_NEXT_BASE+index] = results[s.resourceOutput+P_RESOURCE_STEP_HEAD_BASE+head]; results[s.resourceOutput+P_RESOURCE_STEP_HEAD_BASE+head] = index+1;
        }
        for (uint slot = 0; slot < d.conditionCount; slot++)
        {
            uint cond = s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS+slot*4, kind = commands[cond];
            if (kind < C_GAUGE_ABOVE || kind > C_GAUGE_MOD) continue;
            if (commands[cond+1] >= s.resourceCount || !f64Finite(loadNumber(cond+2))) return false;
            if (kind == C_GAUGE_MOD)
            { uint step = f64ToPositiveStep(loadNumber(cond+2)); if (step == 0 || !f64Equal(f64FromI64(step),loadNumber(cond+2))) return false; }
        }
    }
    return true;
}
