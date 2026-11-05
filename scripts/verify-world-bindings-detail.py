"""World identity queries plus reuse of the shared landing witnesses."""
import argparse,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from detail_boss import empty_world
from detail_world import packed_enemy
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('world_binding_impacts','scripts/verify-typed-impacts-detail.py')



if __name__=='__main__':main()
