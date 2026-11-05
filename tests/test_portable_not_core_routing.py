"""Native context prerequisites never imply portable admission or GPU coverage."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))


class NotCoreRoutingTests(unittest.TestCase):
    pass


    def test_host_not_core_requires_a_physical_world(self):
        from portable_trigger_specs import validate_input
        effect=dict(trigger=dict(timing=['hit_count'],condition=['not_core']))
        with self.assertRaises(ValueError):validate_input(effect,world_frame=False)
        validate_input(effect,world_frame=True)



if __name__=='__main__':unittest.main()
