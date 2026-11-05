"""Original Bay favorite2 positive broken-cover healing, no effects overrides."""
import copy
from portable_weighted_battle_cases import fixtures as original
from portable_original_incoming_profiles import attack
def fixtures():
    c=copy.deepcopy(original()[2]);c['name']='weighted-incoming/Bay/favorite-2/broken-cover-condition/65s'
    c['body']['duration']=65;c['patterns'][0]['until']['time']=65
    next(p for p in c['patterns'] if p['id']=='incoming-10.0')['spec']['atk']=5000000.
    c['patterns'] += [attack('condition-prime',23.3,400000.,target='slot:1',ignore=True,pierce=True),*[attack('late-'+str(t),t,100000.,target='slot:5',ignore=True,pierce=True) for t in (35.,45.,50.,60.)]]
    c['body']['enemy']['patterns']=copy.deepcopy(c['patterns']);c['contract']['scenario']='break-no-revive-reburst'
    return [c]
