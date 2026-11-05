"""All old1393 inputs plus12 aimed area inputs."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('aimed-factor-retention','aimed-area')


def module(name):
    s=importlib.util.spec_from_file_location('aimed_area_retention_'+name,ROOT/('research/verify-world-'+name+'-short.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


adapters={name:module(name) for name in FAMILIES}
prior=adapters[FAMILIES[0]];suite,cross,combine=prior.suite,prior.cross,prior.combine
def prepare():return combine(adapters)
def native_reference(domain):
    family,inner=domain;m=adapters[family]
    if hasattr(m,'native_reference'):return m.native_reference(inner)
    return dict(zip(('battle','skill_trace'),m.suite.inspect_native(inner[0])))
def compare(block,domain):return adapters[domain[0]].compare(block,domain[1])
def validate_rejection(block,name):
    family,label=name.split('/',1);adapters[family].validate_rejection(block,label)
