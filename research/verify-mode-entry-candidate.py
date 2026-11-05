"""Common candidate kernel and packer,with full readback retained before native checks."""
import array,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
import engine_worker
import portable_runtime as runtime,portable_combat
from portable_specs import LIMITS as L
from mode_entry_native import data_context,observe

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
