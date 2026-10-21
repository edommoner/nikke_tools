// The algorithm and capacity stay shared. Only storage changes for the private
// projectile executor; older entry points preserve their Runtime arrays.
#ifdef PORTABLE_WORLD_PROJECTILE
#define LAZY_CACHE_GROUP(s,index) results[(s).resourceOutput+P_LAZY_BANK_GROUP_BASE+(index)]
#define LAZY_CACHE_MASK(s,index) results[(s).resourceOutput+P_LAZY_BANK_MASK_BASE+(index)]
#define LAZY_CACHE_ORDER(s,index) results[(s).resourceOutput+P_LAZY_BANK_ORDER_BASE+(index)]
#define LAZY_CACHE_REFS(s,index) results[(s).resourceOutput+P_LAZY_BANK_REFS_BASE+(index)]
#define LAZY_CACHE_TIME(s,index) (uint64_t(results[(s).resourceOutput+P_LAZY_BANK_TIME_BASE+2*(index)])|(uint64_t(results[(s).resourceOutput+P_LAZY_BANK_TIME_BASE+2*(index)+1])<<32))
#define LAZY_CACHE_STORE_TIME(s,index,value) storeNumber((s).resourceOutput+P_LAZY_BANK_TIME_BASE+2*(index),value)
[noinline]
void clearLazyCacheBank(uint output)
{
    [loop] for(uint word=0;word<P_LAZY_BANK_WORDS;word++) results[output+P_LAZY_BANK_BASE+word]=0;
}
#define LAZY_BANK_INIT(output) clearLazyCacheBank(output);
#define LAZY_BANK_FINISH(output) clearLazyCacheBank(output);
#else
#define LAZY_CACHE_GROUP(s,index) ((s).cacheGroup[index])
#define LAZY_CACHE_MASK(s,index) ((s).cacheMask[index])
#define LAZY_CACHE_ORDER(s,index) ((s).cacheOrder[index])
#define LAZY_CACHE_REFS(s,index) ((s).cacheRefs[index])
#define LAZY_CACHE_TIME(s,index) ((s).cacheTime[index])
#define LAZY_CACHE_STORE_TIME(s,index,value) (s).cacheTime[index]=value
#define LAZY_BANK_INIT(output)
#define LAZY_BANK_FINISH(output)
#endif
