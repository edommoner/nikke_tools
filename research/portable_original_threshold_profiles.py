"""Original Biscuit effects with literal injuries; no computed activation times."""
import copy

def profiles():
    from detail_coverage import body_for
    from portable_original_incoming_profiles import attack
    body=dict(copy.deepcopy(body_for(['비스킷','미란다','노아','센티','드레이크'],30)),burst_gauge_mode='accumulate')
    attacks=[attack('first-defender',1.,1800000,target='slot:3',ignore=True),
             attack('first-protected',2.,100000,target='slot:3',ignore=True),
             attack('second-defender',7.,1800000,target='slot:4',ignore=True),
             attack('second-protected',8.,100000,target='slot:4',ignore=True),
             attack('third-crossing',14.,1500000,target='slot:3',ignore=True),
             attack('exhausted',14.1,100000,target='slot:3',ignore=True)]
    return {'original-catalogue/threshold/Biscuit-'+label+'/30s':
            dict(character='비스킷',favorite_stage=0,kind=3,duration=30,body=copy.deepcopy(body),
                 patterns=[dict(id='world',kind='idle',until=dict(time=30)),*copy.deepcopy(attacks[:count])],
                 scene_witness=dict(family='Original-threshold',scenario=label))
            for label,count in [('control',0),('first',2),('two',4),('exhausted',6)]}
