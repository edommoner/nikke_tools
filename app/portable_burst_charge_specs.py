"""Original caster gauge references, independent of recipient/active weapon."""
STAT = 'burst_charge_speed_pct'


def required(effects):
    return any(e.get('type') == 'buff' and e.get('stat') == STAT for e, _ in effects)


def from_roster(chars):
    from calculator.buff_manager import _NIKKE
    return [{k: _NIKKE[c['name']][k] for k in ('burst_energy', 'burst_energy_raw')
             if k in _NIKKE[c['name']]} for c in chars]


def pack(words, references, L, double_words):
    if references is None:
        return
    if not isinstance(references, list) or len(references) != 5:
        raise ValueError('Burst charge requires five original caster references')
    at = L['BURST_REFERENCE_BASE']
    words[at] = 1
    for who, reference in enumerate(references):
        if not isinstance(reference, dict) or set(reference) - {'burst_energy', 'burst_energy_raw'}:
            raise ValueError('Unsupported burst reference fields')
        energy = reference.get('burst_energy', 0)
        raw = reference.get('burst_energy_raw', 0)
        for value in (energy, raw):
            double_words(value)
            if not 0 <= value <= 1e6:
                raise ValueError('Burst reference out of range')
        words[at+1] |= int('burst_energy_raw' in reference) << who
        pos = at+8+who*4
        words[pos:pos+4] = double_words(energy)+double_words(raw)
