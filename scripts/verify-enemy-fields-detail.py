"""Sparse GPU recipient storage; authored inputs, not CPU buff-state replay."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_recipient_cases import prepare,actions,expected_values,exercise,world_patterns,NAMES
from detail_coverage import a
from detail_boss import compile_world
from impact_specs import ActorHandle,Impact,impact_command
import detail_gpu as g








if __name__=='__main__':main()
