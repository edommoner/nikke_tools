"""Ordered definition candidates; descriptor counts still belong to the executor."""
EVENT_COUNT=128
MAX_DEFINITIONS=256
MAX_TRIGGERS=8
TRIGGER_BASE=145
TRIGGER_WIDTH=7
DIRECT_EVENTS=frozenset((28,47,57,61))

def build_index(rows):
    if len(rows)>MAX_DEFINITIONS:raise ValueError('Too many event definitions')
    buckets=[[] for _ in range(EVENT_COUNT)]
    for index,row in enumerate(rows):
        count=row[144]
        if int(count)!=count or not 0<=count<=MAX_TRIGGERS:raise ValueError('Invalid trigger count')
        seen=set()
        for at in range(int(count)):
            event=row[TRIGGER_BASE+at*TRIGGER_WIDTH]
            if int(event)!=event or not 0<=event<EVENT_COUNT:raise ValueError('Invalid trigger event')
            event=int(event)
            if event not in seen:buckets[event].append(index);seen.add(event)
    offsets=[0];definitions=[]
    for bucket in buckets:definitions.extend(bucket);offsets.append(len(definitions))
    return dict(offsets=tuple(offsets),definitions=tuple(definitions),definition_count=len(rows))

def candidates(index,event,argument=-1):
    if event in DIRECT_EVENTS:return (argument,) if 0<=argument<index['definition_count'] else ()
    if not 0<=event<EVENT_COUNT:return ()
    return index['definitions'][index['offsets'][event]:index['offsets'][event+1]]
