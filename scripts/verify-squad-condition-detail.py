"""Whole-squad composition predicates, with independent CPU simulation and RNG."""
import copy,hashlib,importlib.util,json,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
r=module('squad_random','scripts/verify-random-target-detail.py');a=r.v.v.c.a
from calculator.buff_manager import BuffManager

@contextmanager
def supporter_without_skills(name):
 original=BuffManager.char_effects
 def effects(self,who):return [] if who==name else original(self,who)
 with patch.object(BuffManager,'char_effects',effects):yield

def real_cases():
 for who,buddy,positive,supporter in [('누아르','루주',True,None),('누아르','리타',False,None),('람','렘',True,'렘'),('람','리타',False,None)]:
  names=[who,buddy]+[n for n in ['리타','크라운','앨리스','모더니아'] if n not in (who,buddy)][:3]
  if supporter:names=[who,buddy,'리타','크라운','모더니아']
  body=r.v.v.c.body_for(names,35,True);body['shooting_policy']='character';body['stat_deltas']={who:{'atk':1234}}
  yield who+('-with-buddy' if positive else '-without-buddy'),body,positive,supporter
