"""Shared portable admission and metadata; battle/GPU work forbidden during packing."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend
from calculator import timeline
from portable_runtime import validate_effect,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F
from portable_revival_specs import MAGIC,PERSIST
from portable_revive_cases import fixtures

class RevivalTests(unittest.TestCase):
    def test_static_programs_and_positive_admission(self):
        s=importlib.util.spec_from_file_location('revival_test',ROOT/'research/verify-world-revive-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        def forbidden(*a,**kw):raise AssertionError('Native/GPU execution forbidden during packing')
        with patch.object(timeline,'simulate',forbidden),patch.object(timeline.CharState,'tick',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):entries,data=m.prepare()
        from world_frame_native import authored_metadata,roster_names
        charge=next(c for c in fixtures() if c['name']=='revive-charge-reset');names=roster_names(charge)
        with patch.dict(timeline._NIKKE,authored_metadata(charge)):
            actor=timeline.CharState(dict(name=names[0],skill_levels={'1':10,'2':10,'3':10}),charge['base_atk'][0],None)
        self.assertEqual(charge['combat']['weapons'][0]['min_cycle'],actor._min_fire_cycle)
        self.assertEqual(charge['post_fire_delays'][0],actor.post_fire_delay)
        self.assertEqual(len(entries),35);self.assertEqual(sum(d is not None for _,_,d in entries),26)
        for _,words,domain in entries:
            if domain is None:continue
            c,_,_=domain
            for i,e in enumerate(c['effects']):
                at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']
                self.assertEqual(bool(words[at+F['FLAGS']]&PERSIST),bool(e.get('persist_on_revive')))
                if e.get('stat')=='revive':
                    self.assertEqual(words[at+F['KIND']],29)
                    selector=words[L['RECIPIENT_BASE']+i*8]
                    if e['target'].startswith('allies_down_top_atk_excl:'):self.assertEqual(selector,22)
                    elif e['target'].startswith('allies_down_class_random:'):self.assertEqual(selector,23)
                    p=L['MODE_BASE']+i*L['MODE_WORDS'];self.assertEqual(words[p:p+4],[MAGIC,c.get('seed',19),0,0])
    def test_invalid_authored_shapes_stay_rejected(self):
        effect=fixtures()[1]['effects'][-1]
        for change,combat,world in [({},None,True),({}, {},False),({'type':'buff'}, {},True),({'fixed_value':0},{},True),({'fixed_value':-1},{},True),({'fixed_value':float('nan')},{},True),({'tick_interval':.1},{},True),({'scaling':'max_hp'},{},True),({'persist_on_revive':True},{},True)]:
            with self.subTest(change=change,combat=combat,world=world),self.assertRaises((UnsupportedPortable,ValueError)):
                validate_effect(dict(effect,**change),combat=combat,world_frame=world)
        buff=fixtures()[2]['effects'][-1]
        for value in (1,'yes',None):
            with self.assertRaises(UnsupportedPortable):validate_effect(dict(buff,persist_on_revive=value),combat={},world_frame=True)

if __name__=='__main__':unittest.main()
