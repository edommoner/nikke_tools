"""Metadata-only real parties and explicit operations for unobserved roles."""
import copy,importlib.util
from pathlib import Path

def profiles():
    spec=importlib.util.spec_from_file_location('original_role_defaults',Path(__file__).resolve().parents[1]/'scripts/detail_coverage.py')
    defaults=importlib.util.module_from_spec(spec);spec.loader.exec_module(defaults)
    rapi='라피 : 레드 후드';hood='레드 후드';rows={}
    parties=[('Rapi-no-B1',[rapi,'도라','드레이크','프리바티','센티'],None),
             ('Rapi-with-B1',[rapi,'도라','드레이크','프리바티','미란다'],None),
             ('Red-Hood-123',[hood,'미란다','도라','드레이크','메어리'],[{'1':[hood],'2':[hood],'3':[hood]}]),
             ('Red-Hood-12',[hood,'미란다','도라','드레이크','메어리'],[{'1':[hood],'2':[hood],'3':['드레이크']}])]
    for label,roster,sequence in parties:
        body=dict(copy.deepcopy(defaults.body_for(roster,30)),burst_gauge_mode='accumulate')
        row=dict(character=roster[0],favorite_stage=0,kind=3,duration=30,body=body,variant=label)
        if sequence is not None:row['declared_burst_sequence']=copy.deepcopy(sequence)
        rows['original-catalogue/role/'+label+'/30s']=row
    return rows
