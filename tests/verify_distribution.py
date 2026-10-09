"""Offline build/install proof, not a product updater or release publisher."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

LEGACY = "3d427f2faecacf67be253ac04a155af862831435"
PRODUCER = "6b6893b14169d616c41f82a0292386713da77206"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("staging", type=Path, help="new disposable absolute directory")
    _ = parser.add_argument("--uv-cache", type=Path, required=True, help="prepared approved offline build cache")
    arguments = parser.parse_args()
    stage = Path(arguments.staging).resolve()
    cache = Path(arguments.uv_cache).resolve()
    checkout = Path(__file__).resolve().parents[1]
    if stage == checkout or checkout in stage.parents or stage in checkout.parents or cache == stage:
        raise ValueError("staging-must-be-separate-from-checkout-and-cache")
    stage.mkdir(parents=False, exist_ok=False)
    uv = shutil.which("uv")
    assert uv is not None
    for name in ("home", "tmp"):
        (stage / name).mkdir()
    environment = {
        "PATH": os.pathsep.join((str(Path(uv).parent), "/usr/local/bin", "/usr/bin", "/bin")),
        "HOME": str(stage / "home"),
        "TMPDIR": str(stage / "tmp"),
        "XDG_CACHE_HOME": str(stage / "home" / "cache"),
        "UV_CACHE_DIR": str(cache),
        "UV_OFFLINE": "1",
        "UV_PYTHON_DOWNLOADS": "never",
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    def run(*command: str) -> bytes:
        return subprocess.run(command, cwd=stage, env=environment, check=True, stdout=subprocess.PIPE).stdout

    def build(source: Path, target: str, *, wheel_only: bool = False) -> Path:
        output = stage / target
        flags = ("--wheel",) if wheel_only else ()
        _ = run(uv, "build", "--offline", "--no-sources", *flags, "--out-dir", str(output), str(source))
        wheels = tuple(output.glob("*.whl"))
        assert len(wheels) == 1
        return wheels[0]

    tested = stage / "cases"
    tested.mkdir()
    for source in (checkout / "tests").glob("*.py"):
        _ = shutil.copyfile(source, tested / source.name)
    current = build(checkout, "current")
    direct = build(checkout, "direct", wheel_only=True)
    assert current.read_bytes() == direct.read_bytes(), "sdist/direct wheel contents differ"
    with zipfile.ZipFile(current) as wheel:
        names = wheel.namelist()
        assert len(names) == len(set(names))
        assert all(name.startswith(("model_intelligence/", "model_intelligence-0.1.0.dist-info/")) for name in names)
        assert "model_intelligence/INSTALLATION.md" in names and "model_intelligence/py.typed" in names
        assert not any(name.endswith((".pyc", ".pyo")) for name in names)
    archives = tuple(current.parent.glob("*.tar.gz"))
    assert len(archives) == 1
    extracted = stage / "sdist"
    extracted.mkdir()
    with tarfile.open(archives[0]) as archive:
        archive.extractall(extracted, filter="data")
    sources = tuple(extracted.iterdir())
    assert len(sources) == 1
    rebuilt = build(sources[0], "rebuilt", wheel_only=True)
    assert current.read_bytes() == rebuilt.read_bytes(), "rebuilt sdist wheel differs"
    historical: dict[str, Path] = {}
    for label, revision in (("legacy", LEGACY), ("producer", PRODUCER)):
        source = stage / label
        source.mkdir()
        data = run("git", "-C", str(checkout), "archive", revision)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(source, filter="data")
        historical[label] = build(source, f"{label}-wheel", wheel_only=True)
    virtual = stage / "installed"
    _ = run(uv, "venv", "--offline", "--python", sys.executable, str(virtual))
    python = virtual / "bin" / "python"
    receipt: dict[str, object] = {"legacy_revision": LEGACY, "producer_revision": PRODUCER}
    receipt["source_head"] = run("git", "-C", str(checkout), "rev-parse", "HEAD").decode().strip()
    receipt["source_status"] = run("git", "-C", str(checkout), "status", "--porcelain=v1").decode()
    receipt["uv"] = run(uv, "--version").decode().strip()
    receipt["python"] = sys.version
    receipt["backend"] = "uv_build==0.9.30"
    receipt["wheel_sha256"] = hashlib.sha256(current.read_bytes()).hexdigest()
    for mode in ("legacy", "current", "producer", "downgrade"):
        wheel = historical["legacy" if mode == "downgrade" else mode] if mode != "current" else current
        _ = run(uv, "pip", "install", "--offline", "--no-deps", "--reinstall", "--python", str(python), str(wheel))
        result = run(str(python), "-I", "-B", str(tested / "installed_distribution_cases.py"), mode, str(stage))
        print(result.decode().strip())
        if mode == "current":
            incomplete = stage / "incomplete-0.1.0-py3-none-any.whl"
            _ = incomplete.write_bytes(b"owned incomplete wheel")
            failed = subprocess.run(
                (uv, "pip", "install", "--offline", "--no-deps", "--python", str(python), str(incomplete)),
                cwd=stage,
                env=environment,
                capture_output=True,
            )
            assert failed.returncode != 0
            _ = run(
                str(python),
                "-I",
                "-c",
                "from importlib.resources import files; "
                'assert files("model_intelligence").joinpath("INSTALLATION.md").is_file()',
            )
            for pattern in ("test_producer.py", "test_zai_source.py", "test_operator.py", "test_portable_operator.py"):
                _ = run(str(python), "-I", "-B", "-m", "unittest", "discover", "-s", str(tested), "-p", pattern, "-v")
            outputs = [
                run(
                    str(virtual / "bin" / "mi-evidence"),
                    operation,
                    str(stage / "store"),
                    "--instance",
                    "owned-install",
                    "--at",
                    "2026-10-09T00:00:00Z",
                    "--max-bytes",
                    "65536",
                    "--json",
                )
                for operation in ("status", "inspect", "export")
            ]
            assert outputs[0] == outputs[1] == outputs[2]
    receipt["result"] = "PASS"
    receipt["historical_wheel_sha256"] = {
        label: hashlib.sha256(wheel.read_bytes()).hexdigest() for label, wheel in historical.items()
    }
    _ = (stage / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
