"""Complete real base/favorite inputs with projectile modifiers;GPU0."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_projectile_roster_input import compile_projectile_battle
s=importlib.util.spec_from_file_location('projectile_roster_audit',ROOT/'research/audit-world-roster-input.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
if __name__=='__main__':audit.main(compiler=compile_projectile_battle,destination='portable-world-projectile-roster-readiness.json')
