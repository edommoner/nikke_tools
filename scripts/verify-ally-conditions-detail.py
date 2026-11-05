"""Ally HP gates use effect-owner activation and actual-recipient runtime HP."""
import argparse, hashlib, importlib.util, json, math, random, sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for, a
from calculator.buff_manager import BuffManager

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

oracle=load('ally_hp_oracle','scripts/verify-detail.py')
p=load('ally_hp_periodic','scripts/verify-periodic-detail.py')
raw_effects=load('ally_hp_injection','scripts/verify-cleanse-detail.py')
E=p.effect
NAMES=['리타','크라운','앨리스','모더니아','루주']


def cpu_oracle(program,script,enemy,stats):
    # The legacy event oracle predates HP instants; initialize the same HP
    # maps as timeline.simulate before registering the unmodified handlers.
    original=oracle.BuffManager.__init__
    def initialize(self,*args,**kwargs):
        original(self,*args,**kwargs)
        self.state['hp']={n:stats[n]['hp'] for n in self.squad_names}
        self.state['hp_pct']={n:100.0 for n in self.squad_names}
        for name in self.squad_names:self.sync_hp(name)
    with patch.object(oracle.BuffManager,'__init__',initialize):
        return oracle.oracle(program,script,enemy,stats,timeline_handlers=True)

def primitives():
    # Boundary, source/recipient distinction, all five query orders and healing.
    for threshold in (0,30,50,100):
        for hp in (max(0,threshold-.01),threshold,min(100,threshold+.01)):
            effects=[(E('gate','buff','atk_pct',23,'all_allies',event='passive',condition=[f'ally_hp_below:{threshold}']),NAMES[0]),
                     (E('drain','instant','current_hp_reduce',100-hp,NAMES[2],event='burst_cast'),NAMES[1]),
                     (E('heal','instant','heal_hp_pct',100,'all_allies',event='full_burst_start',scaling='max_hp'),NAMES[1])]
            for order in (list(range(5)),list(reversed(range(5)))):
                commands=[(0,0,i) for i in range(5)]+[(.1,3,1)]+[(.2,'query',i) for i in order]+[(.3,1,1)]+[(.4,'query',i) for i in order]
                yield f'hp-{threshold}-{hp}-order{order[0]}',NAMES,effects,commands,None
    # Finite buff: activation must fail while all allies are healthy, and the
    # persistent runtime test must later select the damaged recipient only.
    for timing in ('battle_start','passive','on_attack'):
        effects=[(E('gate','buff','atk_pct',23,'all_allies',event=timing,duration=3,condition=['ally_hp_below:50']),NAMES[0]),
                 (E('drain','instant','current_hp_reduce',50,NAMES[2],event='burst_cast'),NAMES[1])]
        commands=[(0,0,i) for i in range(5)]+[(.05,7,0)]+[(.06,'query',i) for i in range(5)]+[(.1,3,1),(.2,7,0)]+[(.3,'query',i) for i in range(5)]
        yield 'finite-'+timing,NAMES,effects,commands,None
    # Includes a defender who is the caster: "ally" excludes that caster.
    for names in (NAMES,['리타','도라','앨리스','모더니아','루주'],['크라운','리타','앨리스','모더니아','루주']):
        for condition in ('has_defender_ally','no_defender_ally'):
            from calculator.buff_manager import _NIKKE
            has=any(_NIKKE.get(n,{}).get('class')=='방어형' for n in names[1:])
            expected=[23 if has==(condition=='has_defender_ally') else 0]*5
            effects=[(E('defender gate','buff','atk_pct',23,'all_allies',condition=[condition]),names[0])]
            commands=[(0,0,i) for i in range(5)]+[(.1,'query',i) for i in range(5)]
            yield condition+'-'+names[0]+'-'+names[1],names,effects,commands,expected
