"""Quantity sources: independent stimuli, then existing whole-squad comparator."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
import detail_gpu as g
spec=importlib.util.spec_from_file_location('quantity_oracles',ROOT/'scripts/verify-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.effect;N=['앨리스','리타','크라운','모더니아','N102']

def characters(charge=False):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(a.META[n])) for n in N]
    if charge:
        chars[0]['charge_time_frames']=0
        chars[0]['_weapon'].update(damage_coeff=100,max_ammo=6,full_charge_mult=100,charge_time=0)
    return chars




if __name__=='__main__':main()
