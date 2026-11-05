"""Exact shared pending-reference packets and malformed entry-delay admission."""
import array,copy,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
import engine_worker
import portable_runtime as runtime,portable_combat
from portable_specs import LIMITS as L,FIELDS as F
from pending_reference_context import data_context
from pending_reference_native import observe
from mode_entry_native import data_context as entry_context

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
