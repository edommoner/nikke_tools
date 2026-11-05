"""Independent whole-squad parity for speed immunity and overflow conversion."""
import copy,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
audit=module('charge_immune_audit','scripts/audit-charge-immunity.py');c=audit.c;E=c.E
raw=module('charge_immune_raw','scripts/verify-cleanse-detail.py')
import detail_gpu
from calculator.buff_manager import BuffManager

def dynamic_cases():
    owner=c.NAMES[2]
    base=[E('skill speed','buff','charge_speed_pct',70,'all_allies'),E('skill slow','buff','charge_speed_pct',-20,'all_allies'),
          E('conversion','buff','charge_speed_overflow_conversion_pct',240,'all_allies')]
    yield 'timed-positive-immunity',{owner:base+[E('temporary immunity','buff','charge_speed_buff_immune',0,'all_allies',duration=1,event='every:2s')]},8
    yield 'fullburst-runtime-immunity',{owner:base+[E('full burst immune','buff','charge_speed_debuff_immune',0,'all_allies',event='passive',condition=['during_full_burst'])]},8
    yield 'charge-runtime-immunity',{owner:base+[E('charge immune','buff','charge_speed_buff_immune',0,'self',event='passive',condition=['during_charge'])]},8
    yield 'single-bullet-immunity',{owner:base+[E('one bullet immune','buff','charge_speed_buff_immune',0,'self',event='burst_cast',duration_bullets=1)]},8
    yield 'enemy-slow-and-ally-immunity',{owner:base+[E('enemy slow','buff','charge_speed_pct',-25,'target',polarity='harmful'),E('own negative immunity','buff','charge_speed_debuff_immune',0)]},8
    yield 'caster-based-speed-and-immunity',{owner:[E('caster speed','buff','charge_speed_caster_based_pct',75,'all_allies'),E('negative caster speed','buff','charge_speed_caster_based_pct',-25,'all_allies'),E('positive immunity','buff','charge_speed_buff_immune',0,'all_allies')]},8
    mode={'source':'스킬3','name':'authored SR mode','type':'weapon_change','target':'self','weapon_type':'SR','max_ammo':4,'damage_coeff':{'10':251},'charge_time':.3,'full_charge_mult':250,'duration':3,'trigger':{'timing':['burst_cast'],'condition':[]}}
    yield 'weapon-mode-speed-and-overflow',{owner:base+[mode]},8
    yield 'fractional-cancellation-and-group-order',{owner:[E('huge speed','buff','charge_speed_pct',1e16,'all_allies'),E('small speed','buff','charge_speed_pct',1,'all_allies'),E('huge slow','buff','charge_speed_pct',-1e16,'all_allies'),E('remove positive','buff','charge_speed_buff_immune',0,'all_allies')]},4
