"""Compare dispatch sizes only after all correctness/transfer gates terminate."""
import argparse,hashlib,importlib.util,json,statistics,struct,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ff9a10d175f266708e2d572132b045f1c04083bb'
sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import dispatch_programs
from portable_specs import LIMITS as L
class Collected(BaseException):pass

def load(n):return json.loads((P/(n+'.json')).read_text())
