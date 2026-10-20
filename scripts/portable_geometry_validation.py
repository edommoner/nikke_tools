"""Identical malformed raw geometry programs for both GPU backends."""
import copy
from portable_specs import LIMITS as L, FIELDS as F


def rejection_programs(cases, compile_case):
    base = next(c for c in cases if c.get('geometry_reference') and not c.get('geometry_physical_reference'))
    program, metadata = compile_case(base)
    at = L['GEOMETRY_BASE']
    rows = []
    mutations = [
        ('flags', {at:2}), ('flags-high', {at:5}), ('mask', {at+1:64}),
        ('core-negative', {at+2:0,at+3:0xbff00000}), ('core-nan', {at+3:0x7ff80000}),
        ('core-infinity', {at+3:0x7ff00000}), ('distance-nan', {at:3,at+5:0x7ff80000}),
        ('distance-absent-value', {at+5:0x3ff00000}), ('distance-and-list', {at:3,at+1:1}),
        ('header-reserved', {at+6:1}), ('owner-id-zero', {at+16:0}), ('owner-id-large', {at+16:7}),
        ('owner-reserved', {at+17:1}), ('owner-tail-reserved', {at+22:1}),
        ('lower-negative', {at+18:0,at+19:0xbff00000}),
        ('lower-nan', {at+19:0x7ff80000}), ('upper-infinity', {at+21:0x7ff00000}),
        ('bounds-reversed', {at+18:0,at+19:0x40590000,at+20:0,at+21:0}),
        ('inactive-mode', {at+56:1}), ('mode-tail', {at+56+255*6:1}),
        ('disabled-nonzero', {at:0}), ('core-name', {L['CONDITION_BASE']+1:1}),
        ('core-arg', {L['CONDITION_BASE']+3:0x3ff00000}),
        ('range-name', {L['CONDITION_BASE']:33,L['CONDITION_BASE']+1:1}),
        ('range-arg', {L['CONDITION_BASE']:33,L['CONDITION_BASE']+3:0x3ff00000}),
    ]
    def append(name, original, meta, changes):
        words=list(original)
        for pos, value in changes.items():words[pos]=value
        rows.append((dict(name='geometry-invalid-'+name,status=64), (words,copy.deepcopy(meta))))
    for name,changes in mutations:
        append(name,program,metadata,changes)
    for name,condition,stat in [('core-no-geometry',35,0),('range-no-geometry',33,0),
                               ('min-no-geometry',0,61),('max-no-geometry',0,62)]:
        words=list(program);words[at:at+L['GEOMETRY_WORDS']]=[0]*L['GEOMETRY_WORDS']
        changes={L['CONDITION_BASE']:condition} if condition else {L['DEFINITION_BASE']+F['STAT']:stat,L['DEFINITION_BASE']+F['CONDITION_COUNT']:0}
        append(name,words,metadata,changes)
    mode_case=next(c for c in cases if c.get('geometry_physical_reference') and c['effects'][0]['type']=='weapon_change')
    mode,meta=compile_case(mode_case)
    for name,changes in [('mode-id-zero',{at+56:0}),('mode-id-large',{at+56:7}),
                          ('mode-reserved',{at+57:1}),('mode-bounds-nan',{at+59:0x7ff80000})]:
        append(name,mode,meta,changes)
    return [r[1] for r in rows],[r[0] for r in rows]
