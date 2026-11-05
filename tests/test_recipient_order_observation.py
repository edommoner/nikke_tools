"""The readback opt-in preserves inputs and cannot relax historical guards."""
import copy,hashlib,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_recipient_order_observation as observation

class RecipientOrderObservation(unittest.TestCase):

    def test_complete_wire_and_only_explicit_entry_are_admitted(self):
        from portable_backend import validate_composed_stride
        observation.check_layout(ROOT)
        validate_composed_stride(observation.SOURCE,observation.INPUT_WORDS,observation.OUTPUT_WORDS)
        for source,iw,ow in [(observation.SOURCE,observation.INPUT_WORDS-1,observation.OUTPUT_WORDS),
                             (observation.SOURCE,observation.INPUT_WORDS,observation.OUTPUT_WORDS+1),
                             ('gpu/world_coordinate_typed_ordered_unknown.slang',observation.INPUT_WORDS,observation.OUTPUT_WORDS)]:
            with self.subTest(source=source,iw=iw,ow=ow),self.assertRaises(ValueError):validate_composed_stride(source,iw,ow)


if __name__=='__main__':unittest.main()
