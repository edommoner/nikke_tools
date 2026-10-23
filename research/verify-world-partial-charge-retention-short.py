"""All1442 previous inputs plus45 partial,14 dynamic,4 complete Crust and11 signed-base cases."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('squad-stage-retention','partial-charge','partial-charge-extended','partial-charge-rosters','partial-charge-reduction')


def module(name):
    s=importlib.util.spec_from_file_location('partial_retention_'+name,ROOT/('research/verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


adapters={name:module(name) for name in FAMILIES}
prior=adapters[FAMILIES[0]];suite,cross,combine=prior.suite,prior.cross,prior.combine

def prepare():return combine(adapters)
def native_reference(domain):return adapters[domain[0]].native_reference(domain[1])
def compare(block,domain):return adapters[domain[0]].compare(block,domain[1])
def validate_rejection(block,name):
    family,label=name.split('/',1);adapters[family].validate_rejection(block,label)
