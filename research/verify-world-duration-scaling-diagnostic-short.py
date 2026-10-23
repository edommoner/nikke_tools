import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('duration_diagnostic',Path(__file__).with_name('verify-world-duration-scaling-short.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross,prepare,native_reference,validate_rejection=base.suite,base.cross,base.prepare,base.native_reference,base.validate_rejection
compare=base.compare_diagnostic
