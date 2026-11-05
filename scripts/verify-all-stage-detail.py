"""Exercise Red Hood's A-stage selection, including default B3-only buttons."""
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('all_stage_base',ROOT/'scripts/verify-burst-stage-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
WHO='레드 후드';NAMES=[WHO]+v.NAMES[:4];E=v.E

def scenarios():
 yield 'default-A-is-B3-only',[],{}
 yield 'explicit-A-all-stages',[],{WHO:'A'}
 yield 'explicit-A-zero-cooldown',[E('no cooldown','buff','burst_cooldown',100)],{WHO:'A'}
 yield 'explicit-B2-zero-cooldown',[E('no cooldown','buff','burst_cooldown',100)],{WHO:'2'}
 yield 'override-A-opens-all-buttons',[E('all buttons','buff','burst_stage_override:A',0),E('no cooldown','buff','burst_cooldown',100)],{}
 yield 'override-B1-expires-back-to-A',[E('temporary B1','buff','burst_stage_override:1',0,duration=4)],{}
 yield 'override-B3-is-explicitly-active',[E('B3','buff','burst_stage_override:3',0)],{}
 yield 'A-reentry-each-stage-once',[E('all buttons','buff','burst_stage_override:A',0),E('no cooldown','buff','burst_cooldown',100),E('request','instant','burst_reentry',1,event='burst_cast')],{}
