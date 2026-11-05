"""Complete prepared five-member inputs for all real base/favorite profiles; GPU0."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts')]
import engine_worker as adapter
import portable_backend
from calculator import timeline
from detail_coverage import body_for
from portable_world_roster_input import compile_world_battle
from portable_readiness import inspect_effects,summarize,issue,diagnostic_sources
from portable_readiness_semantics import work_lanes

def roster_for(name):
 stage=str(adapter.META[name]['burst_stage'])
 fillers={'1':['도라','드레이크','N102','메어리','미란다'],'2':['미란다','드레이크','N102','메어리','도라'],'3':['미란다','도라','N102','메어리','드레이크'],'A':['미란다','도라','드레이크','메어리','N102']}
 if stage not in fillers:raise ValueError('No complete roster policy for stage '+stage)
 return [name]+[n for n in fillers[stage] if n!=name][:4]
