"""Run only with an installed wheel from isolated outside-checkout validation."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from importlib.metadata import distribution
from importlib.resources import files
from pathlib import Path

import model_intelligence
from model_intelligence.contract import decode_public_evidence, encode_public_evidence
from model_intelligence.publication import CutReference


def main() -> None:
    mode, name = sys.argv[1:]
    root = Path(name)
    origin = Path(model_intelligence.__file__ or "").resolve()
    assert "site-packages" in origin.parts and Path(sys.prefix).resolve() in origin.parents
    metadata = distribution("model-intelligence").metadata
    assert metadata["Name"] == "model-intelligence"
    assert metadata["Version"] == "0.1.0"
    assert metadata["License-Expression"] == "Apache-2.0"
    assert metadata.get_all("Requires-Dist", []) == []
    assert files("model_intelligence").joinpath("py.typed").is_file()
    # Only owned staged test fixtures are added; installed MI is already resolved.
    sys.path.insert(0, str(Path(__file__).parent))
    from test_router_conformance import T, base

    if mode == "legacy":
        data, reference = encode_public_evidence(base(), produced_at=T)
        _ = (root / "legacy.json").write_bytes(data)
        _ = (root / "legacy.sha256").write_text(reference.sha256, encoding="ascii")
    elif mode == "current":
        from model_intelligence.producer import import_legacy, retained

        assert metadata["Summary"] == "Public AI ecosystem evidence, provenance and immutable publication"
        assert files("model_intelligence").joinpath("INSTALLATION.md").is_file()
        info = distribution("model-intelligence")
        notices = [path for path in info.files or () if path.name == "NOTICE"]
        assert len(notices) == 1 and "Copyright (c) 2025 models.dev" in info.locate_file(notices[0]).read_text()
        original = (root / "legacy.json").read_bytes()
        reference = CutReference(1, "mi.public-evidence-working/1", (root / "legacy.sha256").read_text())
        store = root / "store"
        store.mkdir()
        changed = import_legacy(
            store, original, reference, expected=base().applicability, produced_at=T, max_bytes=65536
        )
        assert (
            import_legacy(store, original, reference, expected=base().applicability, produced_at=T, max_bytes=65536)
            == changed
        )
        assert (store / f"{reference.sha256}.legacy.json").read_bytes() == original
        current = retained(store, max_bytes=65536)
        assert current is not None and current[2] == base()
        distributed = root / "distributed"
        _ = shutil.copytree(store, distributed)
        copied = retained(distributed, max_bytes=65536)
        assert copied is not None and copied == current
        assert decode_public_evidence(copied[0], current[1], max_bytes=65536) == base()
        before = {path.name: path.read_bytes() for path in distributed.iterdir()}
        damaged = copied[0][:-1]
        try:
            _ = decode_public_evidence(damaged, current[1], max_bytes=65536)
        except ValueError as error:
            assert error.args == ("digest-mismatch",)
        else:
            raise AssertionError("partial distribution accepted")
        assert before == {path.name: path.read_bytes() for path in distributed.iterdir()}
        _ = (root / "native.json").write_bytes(current[0])
        _ = (root / "native.sha256").write_text(changed.sha256, encoding="ascii")
        assert hashlib.sha256(current[0]).hexdigest() == changed.sha256
        at = datetime(2026, 10, 9, tzinfo=UTC)
        from model_intelligence.operator import snapshot

        assert snapshot(store, instance="owned-install", at=at, max_bytes=65536)["publication"] is not None
    elif mode == "producer":
        from model_intelligence.producer import retained

        before = {path.name: path.read_bytes() for path in (root / "store").iterdir()}
        current = retained(root / "store", max_bytes=65536)
        assert current is not None and current[2] == base()
        assert before == {path.name: path.read_bytes() for path in (root / "store").iterdir()}
    elif mode == "downgrade":
        before = {path.name: path.read_bytes() for path in (root / "store").iterdir()}
        native = (root / "native.json").read_bytes()
        reference = CutReference(1, "mi.public-evidence-working/2", (root / "native.sha256").read_text())
        try:
            _ = decode_public_evidence(native, reference, max_bytes=65536)
        except ValueError as error:
            assert error.args == ("unsupported-version",)
        else:
            raise AssertionError("old package accepted new grammar")
        legacy = (root / "legacy.json").read_bytes()
        saved = CutReference(1, "mi.public-evidence-working/1", (root / "legacy.sha256").read_text())
        assert decode_public_evidence(legacy, saved, max_bytes=65536) == base()
        assert before == {path.name: path.read_bytes() for path in (root / "store").iterdir()}
    else:
        raise ValueError("unsupported-validation-mode")
    print(json.dumps({"mode": mode, "installed": str(origin), "result": "PASS"}))


if __name__ == "__main__":
    main()
