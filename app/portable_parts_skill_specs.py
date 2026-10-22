"""Private non-coordinate part-skill scope and full-world receipt allocation."""
BASE=781328
CAPACITY=2048
WORDS=CAPACITY*2
END=BASE+WORDS
def verify_layout(limits):
    from portable_heal_share_trace import BASE as trace_base,COUNT,WORDS as trace_words
    assert trace_base+8+COUNT*trace_words+8==BASE # Retain eight guard words.
    assert limits['LANDINGS']==CAPACITY and limits['LANDING_WORDS']==8
    assert limits['REVIVAL_BASE']+limits['REVIVAL_WORDS']<=trace_base
    assert limits['WORLD_PERIODIC_HEAD_BASE']+16<=trace_base
    assert END+10<=786416<limits['WORLD_RELOAD_OUTPUT_WORDS']
    return dict(base=BASE,end=END,capacity=CAPACITY,words=WORDS)

def validate(effect,*,combat,world_frame):
    if 'hits_parts' not in effect:return False
    if effect.get('type')!='damage' or type(effect['hits_parts']) is not bool:
        raise ValueError('Part skill marker requires a damage effect and boolean')
    if combat is None or not world_frame:raise ValueError('Part skills require the private combat world')
    # Deferred acceptance depends on the compiled owner's burst stage, not a
    # guessed timing string. The shared GPU descriptor validator rejects it.
    return True
