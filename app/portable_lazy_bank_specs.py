"""A bounded temporary bank for the existing private projectile executor."""
FIELDS=(('cacheGroup','GROUP',1),('cacheMask','MASK',1),('cacheOrder','ORDER',1),
        ('cacheRefs','REFS',1),('cacheTime','TIME',2))
BANKED_FIELDS=frozenset(name for name,_,_ in FIELDS)
DECLARATIONS=(
    'uint cacheGroup[P_LAZY_CACHE], cacheMask[P_LAZY_CACHE], cacheOrder[P_LAZY_CACHE], cacheRefs[P_LAZY_CACHE];',
    'uint64_t cacheTime[P_LAZY_CACHE];',
)
PROJECTILE_OUTPUT_WORDS=786432
DIAGNOSTIC_WORDS=16


def allocate(limits):
    base=limits['SKILL_CRITICAL_STATE_BASE']+limits['SKILL_CRITICAL_STATE_WORDS'];cursor=base
    limits['LAZY_BANK_BASE']=base
    for _,key,width in FIELDS:
        limits['LAZY_BANK_'+key+'_BASE']=cursor;cursor+=limits['LAZY_CACHE']*width
    limits['LAZY_BANK_WORDS']=cursor-base
    if base%2 or cursor>PROJECTILE_OUTPUT_WORDS-DIAGNOSTIC_WORDS:raise ValueError('Lazy bank overlaps live output or diagnostic tail')


def validate_output_stride(output_words):
    if output_words!=PROJECTILE_OUTPUT_WORDS:
        raise ValueError('Lazy bank requires the projectile output stride')
