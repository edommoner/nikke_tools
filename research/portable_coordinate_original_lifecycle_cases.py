"""Original DoT alternate sources under declared enemy birth/death worlds."""
import copy
from portable_coordinate_original_periodic_cases import fixtures as periodic

def fixtures():
    rows=[]
    for delay in (0.,10.):
        row=copy.deepcopy(periodic()[0])
        row.update(name=f'coordinate-original-lifecycle/Harran/death-{delay}',lifecycle_witness='death-before-dot' if delay==0 else 'death-refresh')
        row['body']['duration']=12
        row['patterns'].append(dict(id='victim',kind='summon',delay=delay,spec=dict(count=2,hp=1)))
        rows.append(row)
    row=copy.deepcopy(periodic()[2]);row.update(name='coordinate-original-lifecycle/Kurumi/burst-refresh',lifecycle_witness='burst-refresh');row['body']['duration']=6;rows.append(row)
    return rows
