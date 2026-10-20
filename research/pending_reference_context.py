"""Authored innate stages are static fixture data,not CPU combat observations."""
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator import buff_manager,timeline
from timer_registry_cases import NAMES
@contextmanager
def data_context(case):
 stages=case['pending_reference_context']['stages'];tables=[]
 for t in (engine_worker.META,buff_manager._NIKKE,timeline._NIKKE):
  if not any(t is x for x in tables):tables.append(t)
 from contextlib import ExitStack
 with ExitStack() as stack:
  for t in tables:stack.enter_context(patch.dict(t,{n:dict(t[n],burst_stage=str(s)) for n,s in zip(NAMES,stages)}))
  yield
