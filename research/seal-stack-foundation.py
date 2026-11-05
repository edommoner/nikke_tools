"""Seal the foundation, preserving explicit incomplete all-character status."""
import copy,hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
SOURCE='851625603c9079008bedfb892b80ba36575daeeb'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(raw):
 text=raw.decode().replace('\r\n','\n').replace('\r','\n')
 text='\n'.join(x for x in text.split('\n') if not re.match(r'^\s*#line\b',x))
 text=re.sub(r'"([^"\n]+)"',lambda m:'"'+m[1].replace('\\','/').split('/')[-1]+'"' if '/' in m[1] or '\\' in m[1] or m[1]=='slang-cuda-prelude.h' else m[0],text)
 return hashlib.sha256(text.encode()).hexdigest()
