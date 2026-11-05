"""One batch: original6 real rosters plus direct-reader contracts and raw negatives."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def module(label,file):
    spec=importlib.util.spec_from_file_location(label,ROOT/'research'/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


adapters={'late-attack-random':module('history_late','verify-world-late-attack-random-short.py'),
          'state-focus-rosters':module('history_real','verify-world-state-focus-rosters-short.py')}
suite,cross=adapters['late-attack-random'].suite,adapters['late-attack-random'].cross


def prepare():
    entries=[]
    for family,adapter in adapters.items():
        rows,_=adapter.prepare()
        entries.extend((family+'/'+name,words,None if domain is None else (family,domain)) for name,words,domain in rows)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):return adapters[domain[0]].native_reference(domain[1])
def compare(block,domain):return adapters[domain[0]].compare(block,domain[1])
def validate_rejection(block,name):
    family,label=name.split('/',1);adapters[family].validate_rejection(block,label)
