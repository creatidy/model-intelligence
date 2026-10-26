"""Exact-source offline installed MI/Router acceptance, not live activation."""

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
import tomllib
import zipfile
from pathlib import Path

MI_PIN = "d65891668b7e79f7b666c021f02a1b4bf8c4ca9c"
ROUTER_PIN = "4162f6fa9f774beaf6e92d86b7ebc92f306da4bd"
ROUTER_URL = "https://forgejo.creatidy.com/BioMedical-IT/scarcity-router.git"
MI_REQUIREMENT = f"model-intelligence @ git+https://forgejo.creatidy.com/Creatidy/model-intelligence.git@{MI_PIN}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("staging", type=Path, help="new absolute outside-checkout directory")
    _ = parser.add_argument("--router-objects", type=Path, required=True)
    _ = parser.add_argument("--uv-cache", type=Path, required=True)
    arguments = parser.parse_args()
    stage = Path(arguments.staging).resolve()
    cache = Path(arguments.uv_cache).resolve()
    objects = Path(arguments.router_objects).resolve()
    checkout = Path(__file__).resolve().parents[1]
    if any(stage == path or stage in path.parents or path in stage.parents for path in (checkout, cache, objects)):
        raise ValueError("staging-must-be-separate")
    stage.mkdir(exist_ok=False)
    for name in ("home", "tmp", "cases"):
        (stage / name).mkdir()
    uv = shutil.which("uv")
    assert uv is not None
    environment = {
        "PATH": os.pathsep.join((str(Path(uv).parent), "/usr/local/bin", "/usr/bin", "/bin")),
        "HOME": str(stage / "home"),
        "TMPDIR": str(stage / "tmp"),
        "XDG_CACHE_HOME": str(stage / "home" / "cache"),
        "UV_CACHE_DIR": str(cache),
        "UV_OFFLINE": "1",
        "UV_PYTHON_DOWNLOADS": "never",
        "PYTHONDONTWRITEBYTECODE": "1",
        "SOURCE_DATE_EPOCH": "1792976400",
    }

    def run(*command: str, cwd: Path = stage) -> bytes:
        result = subprocess.run(command, cwd=cwd, env=environment, capture_output=True)
        with (stage / "commands.log").open("ab") as log:
            output = (
                ("archive-sha256:" + hashlib.sha256(result.stdout).hexdigest() + "\n").encode()
                if "archive" in command
                else result.stdout
            )
            _ = log.write((json.dumps(command) + "\n").encode() + output + result.stderr)
            _ = log.write(f"\nexit={result.returncode}\n".encode())
        result.check_returncode()
        return result.stdout

    assert run("git", "-C", str(objects), "remote", "get-url", "origin").decode().strip() == ROUTER_URL
    receipt: dict[str, object] = {
        "mi_revision": MI_PIN,
        "router_revision": ROUTER_PIN,
        "harness_revision": run("git", "-C", str(checkout), "rev-parse", "HEAD").decode().strip(),
        "harness_status": run("git", "-C", str(checkout), "status", "--porcelain=v1").decode(),
        "python": sys.version,
        "uv": run(uv, "--version").decode().strip(),
        "network": "offline builds/install/tests; canonical source objects prepared separately",
    }
    sources: dict[str, Path] = {}
    for label, repository, revision in (("mi", checkout, MI_PIN), ("router", objects, ROUTER_PIN)):
        assert run("git", "-C", str(repository), "rev-parse", f"{revision}^{{commit}}").decode().strip() == revision
        data = run("git", "-C", str(repository), "archive", revision)
        source = stage / label
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(source, filter="data")
        sources[label] = source
        receipt[f"{label}_source_archive_sha256"] = hashlib.sha256(data).hexdigest()
        receipt[f"{label}_tree"] = (
            run("git", "-C", str(repository), "rev-parse", f"{revision}^{{tree}}").decode().strip()
        )
    project = tomllib.loads((sources["router"] / "pyproject.toml").read_text())
    assert project["project"]["optional-dependencies"]["mi"] == [MI_REQUIREMENT]
    receipt["optional_mi_requirement"] = MI_REQUIREMENT
    build_constraints = stage / "build-constraints.txt"
    _ = build_constraints.write_text("hatchling==1.32.4\nuv_build==0.9.30\n")
    environment["UV_BUILD_CONSTRAINT"] = str(build_constraints)
    receipt["build_backend_versions"] = {"hatchling": "1.32.4", "uv_build": "0.9.30"}
    artifacts: dict[str, Path] = {}
    for label, source in sources.items():
        output = stage / f"{label}-dist"
        _ = run(uv, "build", "--offline", "--no-sources", "--out-dir", str(output), str(source))
        (wheel,) = output.glob("*.whl")
        (sdist,) = output.glob("*.tar.gz")
        extracted = stage / f"{label}-sdist"
        extracted.mkdir()
        with tarfile.open(sdist) as archive:
            archive.extractall(extracted, filter="data")
        (rebuilt_source,) = extracted.iterdir()
        rebuilt_dir = stage / f"{label}-rebuilt"
        _ = run(uv, "build", "--offline", "--no-sources", "--wheel", "--out-dir", str(rebuilt_dir), str(rebuilt_source))
        (rebuilt,) = rebuilt_dir.glob("*.whl")
        assert wheel.read_bytes() == rebuilt.read_bytes(), f"{label} sdist rebuild mismatch"
        artifacts[label] = wheel
        receipt[f"{label}_artifacts"] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (wheel, sdist)
        }
        with zipfile.ZipFile(wheel) as archive:
            package = "model_intelligence" if label == "mi" else "scarcity_router"
            # Every installed Python module must come from the frozen source export.
            prefix = source / "src" if label == "mi" else source
            for name in archive.namelist():
                if name.startswith(package + "/") and name.endswith(".py"):
                    assert archive.read(name) == (prefix / name).read_bytes()
    # Execute maintained fixtures outside both source exports; no package sources
    # or standalone consumer functions are copied onto the import path.
    cases = stage / "cases"
    for source in (checkout / "tests").glob("*.py"):
        _ = shutil.copyfile(source, cases / source.name)
    _ = shutil.copyfile(sources["router"] / "tests" / "test_mi_consumer.py", cases / "router_component_cases.py")
    (cases / "tests").mkdir()
    _ = (cases / "tests" / "__init__.py").write_text("")
    _ = shutil.copyfile(sources["router"] / "tests" / "observation.py", cases / "tests" / "observation.py")
    for name in ("model-catalog.json", "model-policy.json"):
        _ = shutil.copyfile(sources["router"] / name, stage / name)
    locked = run(uv, "export", "--offline", "--frozen", "--no-dev", "--no-emit-project", cwd=sources["router"])
    requirements = stage / "router-requirements.txt"
    _ = requirements.write_bytes(locked)
    virtual = stage / "installed"
    _ = run(uv, "venv", "--offline", "--python", sys.executable, str(virtual))
    python = virtual / "bin" / "python"
    _ = run(uv, "pip", "install", "--offline", "--python", str(python), "-r", str(requirements))
    _ = run(uv, "pip", "install", "--offline", "--no-deps", "--python", str(python), str(artifacts["router"]))
    bootstrap = run(str(python), "-I", "-B", str(cases / "installed_router_cases.py"), "bootstrap", str(stage))
    print(bootstrap.decode().strip())
    receipt["bootstrap"] = json.loads(bootstrap)
    # The optional VCS requirement is satisfied by the locally built wheel from
    # that exact Git object, not by version equality or a network VCS resolver.
    wheel_requirements = stage / "installed-wheels.txt"
    _ = wheel_requirements.write_text(
        "\n".join(
            f"{name} @ {artifacts[label].as_uri()} "
            f"--hash=sha256:{hashlib.sha256(artifacts[label].read_bytes()).hexdigest()}"
            for label, name in (("router", "scarcity-router[mi]"), ("mi", "model-intelligence"))
        )
        + "\n"
    )
    _ = run(
        uv,
        "pip",
        "install",
        "--offline",
        "--no-deps",
        "--require-hashes",
        "--python",
        str(python),
        "-r",
        str(wheel_requirements),
    )
    receipt["installed_dependency_check"] = run(uv, "pip", "check", "--python", str(python)).decode()
    result = run(str(python), "-I", "-B", str(cases / "installed_router_cases.py"), "acceptance", str(stage))
    print(result.decode().strip())
    receipt["integration"] = json.loads(result)
    expected_cut = json.loads((stage / "expected-cut.json").read_bytes())
    outputs = [
        run(
            str(virtual / "bin" / "mi-evidence"),
            operation,
            str(stage / "publication"),
            "--instance",
            "installed-synthetic",
            "--at",
            "2026-10-26T00:00:00.123456+00:00",
            "--max-bytes",
            "262144",
            "--checkpoint",
            expected_cut["sha256"],
            "--json",
        )
        for operation in ("status", "inspect", "export")
    ]
    assert outputs[0] == outputs[1] == outputs[2]
    assert json.loads(outputs[0]) == json.loads((stage / "operator-b.json").read_bytes())
    _ = (stage / "cli-snapshot.json").write_bytes(outputs[0])
    receipt["installed_cli_agreement"] = "PASS status=inspect=export=reader snapshot"
    for pattern in (
        "router_component_cases.py",
        "test_producer.py",
        "test_zai_source.py",
        "test_operator.py",
        "test_portable_operator.py",
    ):
        _ = run(str(python), "-I", "-B", "-m", "unittest", "discover", "-s", str(cases), "-p", pattern, "-v")
    receipt["component_suites"] = "PASS; exact commands, counts and individual cases in commands.log"
    receipt["backend_requirements"] = {
        label: tomllib.loads((source / "pyproject.toml").read_text())["build-system"]
        for label, source in sources.items()
    }
    receipt["result"] = "PASS"
    _ = (stage / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
