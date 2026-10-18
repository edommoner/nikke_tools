"""Give lost-HP value queries the existing requested revival percentage.

The pinned CPU clears hp_pct to None while restoring passives. The v34 bridge
already supplies the requested percentage to condition queries; _get_value's
lost_hp_pct branch has the same None arithmetic failure (actual Moran revival).
Keep the transition sentinel and change only this query inside that context.
"""
from functools import wraps
def install():
    from calculator.buff_manager import BuffManager
    original=BuffManager._get_value
    if getattr(original,'_nikke_lost_hp_revive_query',False):return
    @wraps(original)
    def get_value(self,eff,ab,*args,**kwargs):
        name=ab.caster;percentages=self.state.get('hp_pct',{});context=getattr(self,'_nikke_revive_percentages',{})
        if eff.get('scaling')!='lost_hp_pct' or percentages.get(name) is not None or name not in context:
            return original(self,eff,ab,*args,**kwargs)
        percentages[name]=context[name]
        try:return original(self,eff,ab,*args,**kwargs)
        finally:percentages[name]=None
    get_value._nikke_lost_hp_revive_query=True
    BuffManager._get_value=get_value
