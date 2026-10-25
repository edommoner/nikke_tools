"""Reuse real packet/notification capture under the sampled common policy."""
from fractions import Fraction
def observe(case):
    from world_coordinate_sampling_native import observe as sampled
    from world_coordinate_packet_quantity_native import observe as quantities
    from portable_coordinate_sampling_contracts import verify
    from world_frame_native import roster_names
    n=quantities(case,observer=lambda c:sampled(c)[0]);verify(case,n);names=roster_names(case)
    for notice in n['full_charge_quantities']:
        muzzles=case['combat']['weapons'][notice['owner']]['muzzles']
        total=sum(p['damage'] for row in n['physical_pellets'] if row['owner']==names[notice['owner']] and row['time']==notice['time'] for p in row['packets'])
        assert notice['dealt']==float(Fraction(total,muzzles))==total/muzzles,'Native exact integer parent ratio'
    return n,n['skill_trace']
