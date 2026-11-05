"""CPU-only receipt for a successful normal core and incomplete world run."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '6f54193636f2e44e59a588e208528f099419ac6e'
ARTIFACTS = {
    'windows-portable-cross-v79-summary.json': (1946, '3e2cbb4c5f5cfa9eb778ed82baaed5554584f87ef0c258695f9c71ef3316fb32'),
    'portable-cross-v79-execution.json': (3771, '9674201eba526349cce473da35e3d9ee164ba573af1e0ca2f03129b142f5551f'),
    'windows-portable-cross-v79-core-summary.json': (36136, 'cc0bd4903902959c898dafaa8bc7ef4849aac448472d46f7af1f484d7aac8caf'),
    'portable-cross-v79-phase-diagnostics.json': (5904, '7a2fbbfbb3f8cad253d6b452a439ca1f998f4c2b616347b7a87bbb3c6968d554'),
}

def load(name):
    return json.loads((ROOT/'research'/name).read_text())
