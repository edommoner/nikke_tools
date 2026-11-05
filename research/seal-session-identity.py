"""Attest current native/GPU session boundaries without widening certification."""
import copy,hashlib,importlib.util,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
SOURCE='2e1a265a58622cde3bdeef9c4bd9c9e3ad0d4e9c'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,v):(P/(n+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(raw):
    text=raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n')
    text='\n'.join(line for line in text.split('\n') if not re.match(r'^\s*#line\b',line))
    text=re.sub(r'"([^"\n]+)"',lambda m:'"'+m[1].replace('\\','/').split('/')[-1]+'"' if '/' in m[1] or '\\' in m[1] or m[1]=='slang-cuda-prelude.h' else m[0],text)
    return hashlib.sha256(text.encode()).hexdigest()
