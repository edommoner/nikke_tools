"""Reproduce/verify the isolated correctness candidate without changing live GPU source."""
import argparse
import hashlib
import io
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE='85b8b190ec9d9fa8ebd66058947bccfcda72e489'


def expected_sources():
    files={}
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=ROOT))) as archive:
        for member in archive:
            if member.isfile():files[member.name]=archive.extractfile(member).read()
    text=files['gpu/event_runtime.slang'].decode()
    text=text.replace('gaugeCharging, normalLandedMask;','gaugeCharging, normalLandedMask, physicalGaugeOwner;')
    text=text.replace('uint64_t cooldownApplied[5];','uint64_t cooldownApplied[5], physicalGaugeGain;')
    old='uint64_t gain = f64Less(damage.damageGauge,0) ? s.gain[damage.owner] : damage.damageGauge;'
    assert text.count(old)==1
    text=text.replace(old,'uint64_t gain = f64Less(damage.damageGauge,0) ? (s.physicalGaugeOwner==damage.owner+1 ? s.physicalGaugeGain : s.gain[damage.owner]) : damage.damageGauge;')
    files['gpu/event_runtime.slang']=text.encode()
    text=files['gpu/combat_runtime.slang'].decode()
    text=text.replace('    s.frameAmmoActive[who] = 1;','    s.frameAmmoActive[who] = 1;\n    s.physicalGaugeOwner=who+1;s.physicalGaugeGain=w.gain;')
    text=text.replace('s.frameAmmoActive[who] = 0; clearMode(s,who,when);','s.frameAmmoActive[who] = 0;s.physicalGaugeOwner=0; clearMode(s,who,when);')
    text=text.replace('    s.frameAmmoActive[who] = 0;','    s.frameAmmoActive[who] = 0;s.physicalGaugeOwner=0;')
    files['gpu/combat_runtime.slang']=text.encode()
    text=files['gpu/runtime_init.slang'].decode().replace('    s.normalLandedMask = 0;','    s.normalLandedMask = 0;\n    s.physicalGaugeOwner = 0;\n    s.physicalGaugeGain = 0;')
    files['gpu/runtime_init.slang']=text.encode()
    files['burst_charge_mode_fix_runtime.slang']=b'#include "gpu/event_runtime.slang"\n'
    return files


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    folder=ROOT/'research/portable-build/burst-charge-mode-fix-candidate'
    expected=expected_sources()
    if not args.verify:
        folder.mkdir()
        for name,data in expected.items():
            path=folder/name;path.parent.mkdir(exist_ok=True,parents=True);path.write_bytes(data)
    for name,data in expected.items():
        assert (folder/name).read_bytes()==data,name
    print(len(expected),'candidate sources byte-exact to archived baseline plus explicit patch')
    for name in ('gpu/event_runtime.slang','gpu/combat_runtime.slang','gpu/runtime_init.slang'):
        print(name,hashlib.sha256(expected[name]).hexdigest())


if __name__=='__main__':main()
