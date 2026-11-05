// The same numeric cartridge operator for allied and enemy resources.
// Recipient selection, capacities, reloads and completion events are callers.
bool prepareAmmoInstant(uint kind,uint64_t value,out int64_t flat,out uint64_t fraction)
{
    flat=0;fraction=0;uint status;
    if(kind==13)fraction=f64Div(value,HUNDRED);
    else
    {
        flat=int64_t(f64ToI64(value,1,status));
        if(status!=0)
        {
            if(!f64Less(0,value))return false;
            flat=int64_t(0x7fffffffffffffff);
        }
    }
    return true;
}

bool ammoInstantResult(uint kind,uint capacity,int current,int64_t flat,uint64_t fraction,out int result)
{
    result=0;int64_t change=flat;uint status;
    if(kind==13)
    {
        uint64_t amount=f64Mul(f64FromI64(capacity),fraction);
        if(!f64Finite(amount))return false;
        change=int64_t(f64ToI64(amount,0,status));
        if(status!=0)change=f64Less(amount,0)?int64_t(uint64_t(1)<<63):int64_t(0x7fffffffffffffff);
    }
    int64_t before=int64_t(current),after;
    if(change>=int64_t(capacity)-before)after=capacity;
    else if(kind==13&&change<=-before)after=0;
    else
    {
        if(change<int64_t(-2147483647)-1-before)return false;
        after=before+change;
    }
    result=int(after);return true;
}
