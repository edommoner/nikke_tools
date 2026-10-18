"""Small shared archive/receipt gate for new GPU mechanism checkpoints."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def checked_receipts(paths):
    receipts = {path: read(path) for path in paths}
    for path, receipt in receipts.items():
        assert receipt['passed'], path
        digests = receipt.get('source_sha256', {})
        assert isinstance(digests, dict), (path, 'expected a source inventory')
        for source, digest in digests.items():
            assert sha(source) == digest, (path, source)
    return receipts


def save_checkpoint(path, archive_path, checkpoint, selection):
    selection = sorted(set(selection))
    for name in selection + [path, archive_path]:
        resolved = (ROOT / name).resolve()
        assert resolved.is_relative_to(ROOT) and resolved != ROOT, name
    # Confirm every selected file before creating a partial archive.
    digests = {name: sha(name) for name in selection}
    archive = ROOT / archive_path
    assert not archive.exists(), archive
    checkpoint = dict(checkpoint, archive=archive_path, source_sha256=digests)
    (ROOT / path).write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    archive.mkdir()
    for name in selection + [path]:
        target = archive / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == sha(name), name
    return dict(passed=True, files=len(selection) + 1, archive=str(archive))
