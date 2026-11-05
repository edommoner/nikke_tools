import importlib.util,array,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('duration_legacy',Path(__file__).with_name('verify-world-duration-scaling-short.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
def prepare():
    rows,data=base.prepare();w=rows[0][1];packed=array.array('I',[1,*w])
    if sys.byteorder!='little':packed.byteswap()
    return [('reject/duration-scaling-old-entry',w,None)],packed.tobytes()
validate_rejection=base.validate_rejection
