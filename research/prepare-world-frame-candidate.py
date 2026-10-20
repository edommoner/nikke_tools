"""Prepare evidence storage for the direct shared world entry; no source copies."""
import datetime,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import source_hashes
from portable_specs import LIMITS,check_schema
def prepare():
 check_schema();source='gpu/world_frame_entry.slang'
 folder=ROOT/'research/portable-build'/('world-frame-common-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 record=dict(base_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),created=str(folder),source=source,patches=[],runtime_copies=False,canonical_source_shared=True,preparation_mutates_canonical=False,input_words=LIMITS['WORLD_FRAME_INPUT_WORDS'],output_words=LIMITS['WORLD_FRAME_OUTPUT_WORDS'],abi=hex(LIMITS['WORLD_FRAME_ABI']),source_sha256=source_hashes(source),scope='One canonical event/combat/protection/target executor. Descriptor providers and layout selected at compile time;no rewritten runtime copy.')
 (folder/'candidate-preparation.json').write_text(json.dumps(record,indent=2)+'\n')
 assert json.loads((folder/'candidate-preparation.json').read_text())==record
 return record
if __name__=='__main__':print(json.dumps(prepare(),indent=2))
