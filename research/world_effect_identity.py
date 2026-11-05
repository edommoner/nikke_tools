"""Bind observed original effects to registration rows, never display labels."""
def row(case,effect,owner=None):
    if case.get('source_effect_identity'):
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']):raise ValueError('Missing original effect registration identity')
        if effect.get('name')!=case['effects'][index].get('name'):raise ValueError('Original effect label/identity mismatch')
        if owner is not None and case['names'][case['owners'][index]]!=owner:raise ValueError('Original effect owner/identity mismatch')
        return index
    matches=[i for i,e in enumerate(case['effects']) if e.get('type')=='damage' and e.get('name')==effect.get('name')]
    if len(matches)!=1:raise ValueError('Ambiguous damage label requires original registration identity')
    return matches[0]

def event_row(case,event):
    matches=[i for i,e in enumerate(case['effects']) if e.get('type')=='damage' and e.get('name')==event.skill_name and case['names'][case['owners'][i]]==event.caster]
    if len(matches)!=1:raise ValueError('Ambiguous damage event requires its creation identity')
    return matches[0]
