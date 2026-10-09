# Offline Installation and Maintenance

This is the supported source-build/local-wheel path for #18, not a published
release, registry service, deployment, product GO or installed Router acceptance.
Use Python 3.12+, uv, an inspected exact canonical Git revision and an operator-owned
staging directory. No private onprem package or runtime dependency is required.
Build tools are development dependencies; do not run builds in the knowledge store.

## Build and Install

From the inspected checkout, record `git rev-parse HEAD` and clean status. Build
into a new disposable directory, not over the only copy of a previous wheel:

```sh
uv build --offline --out-dir /tmp/mi-build
sha256sum /tmp/mi-build/model_intelligence-0.1.0-py3-none-any.whl
uv venv --offline --python python3.12 /tmp/mi-install
uv pip install --offline --no-deps --python /tmp/mi-install/bin/python /tmp/mi-build/model_intelligence-0.1.0-py3-none-any.whl
```

The exact `uv_build==0.9.30` backend and Python interpreter must already be available
offline. A missing tool/cache is an installation failure, not an artifact update;
prepare approved build tools separately. `uv.lock` pins development dependencies,
not the backend: its exact requirement is in `pyproject.toml`. Record `uv --version`,
Python version, source commit, wheel SHA-256 and backend version with each install.
Do not claim reproducibility from package version alone. Historical #13, #15 and
#16 builds all call themselves `0.1.0` while exposing different contracts.

Run from outside the checkout:

```sh
/tmp/mi-install/bin/python -I -c 'from importlib.metadata import distribution; from importlib.resources import files; import model_intelligence; print(model_intelligence.__file__); print(distribution("model-intelligence").metadata["Summary"]); print(files("model_intelligence").joinpath("INSTALLATION.md").read_text())'
/tmp/mi-install/bin/mi-evidence inspect /tmp/mi-public-artifacts --instance public-demo --at 2026-10-09T00:00:00Z --max-bytes 65536 --json
```

The import origin must be the installed environment, not `src`. The installed
support document is a package resource; Apache-2.0 LICENSE and selected models.dev
MIT NOTICE are distribution license files. The wheel/sdist contain code, metadata,
typing marker and support text, not raw official pages, private state or test data.
No PyPI/release-download/update-service route has been verified or authorized.
Do not run a guessed `pip install model-intelligence` or publish this package.

## Compatibility and Data

| Component | Supported meaning |
| --- | --- |
| Frame `format_version=1` | Exact immutable UTF-8 bytes, digest/reference, members and source provenance; hashes prove integrity, not publisher authenticity. |
| `mi.public-evidence-working/1` | Retained minimum #13 grammar; decoder and explicit legacy import support. Native `/2` fields cannot be silently encoded here. |
| `mi.public-evidence-working/2` | #15 explicit subject/native-limit extension; active retained store uses this grammar only. |
| `mi.source-refresh-working/1` | Separate source-attempt facts, not an atomic commit with the publication or evidence freshness. |
| `mi.operator-working/1` | #16 read-only full snapshot; retained-cut checkpoint, explicit gaps, no event replay/global cursor. |
| `zai-flash-public/1` | Fixed selected public source URI/pin/rights/bounds and hashed scope configuration; not a generic provider catalog. |

Keep `current`, all digest-named `.json` cuts, imported `.legacy.json` originals,
source status and a receipt identifying package/source/contract/configuration
versions together. Distribution is an exact-byte copy of this operator-owned
directory plus its independently expected cut reference and source NOTICE. Readers
must validate before use; copying a partial directory is not activation. Historical
receipts retain their original bytes, not a pointer that tracks later updates.
Router alone admits evidence and chooses freshness/fallback/new-use policy.

For an offline local copy into a new destination, preserve the whole directory:

```sh
cp -a /tmp/mi-public-artifacts /tmp/mi-distributed-artifacts
/tmp/mi-install/bin/mi-evidence inspect /tmp/mi-distributed-artifacts --instance copied-public-demo --at 2026-10-09T00:00:00Z --max-bytes 65536 --json
```

Verify against the independently expected cut reference with
`decode_public_evidence(data, reference, max_bytes=bound)` before consumption.
CLI inspection alone does not authenticate a self-declared copied pointer. Do not
copy while a writer is active or merge files into an existing destination.

The scope records source IDs, channel and native configuration. There is no old
persisted user-config format or generic migration registry to invent. Changing a
source pin/adapter/scope requires reviewed compatibility and a separate directory,
not relabeling or dropping old evidence. Missing/null/zero/false/`none` stay distinct.

## Updates and Recovery

Use one mutator per store. Preserve an immutable backup before changing packages;
install a candidate wheel into a separate environment and inspect the same store
read-only first. Never replace the only working environment during validation.
Keep failed candidates and the original package/artifacts identifiable for diagnosis.

Existing installed APIs are the update path: `model_intelligence.zai.refresh` for
separately authorized public retrieval, and `model_intelligence.producer.publish`
for complete validated evidence. There is no write/update CLI. `publish` checks
exact scope and preserved history, writes/fsyncs a complete digest-named cut, then
atomically replaces/fsyncs `current`. Retry the same complete generation; an orphan
complete cut is not evidence of an active update. `mi-evidence` never fetches/writes.
`refresh` needs explicit time, timeout and byte policy, not a global TTL.

For existing `/1` bytes, use `producer.import_legacy(directory, data, reference,
expected=scope, produced_at=at, max_bytes=bound)`. It validates the independently
supplied reference and expected scope, preserves exact `.legacy.json` bytes and
publishes `/2` without inventing native metadata. Retry is idempotent. The active
store is not a `/1` pointer format; simply copying a `/1` file to `current` is invalid.

Rollback means reinstalling the identified older package in a separate environment
and retaining the complete current store unchanged. The #13 reader rejects `/2`;
it can still read the saved `/1` original with its original reference. #15 can read
the unchanged #16 `/2` store but has no operator CLI. A history-losing publication
rollback is intentionally rejected. Recovery requiring an older cut uses a separate
preserved backup and consumer-owned review, not direct editing of `current` or deletion
of newer history. No data/pruning/deprecation promise is inferred from a downgrade.

| Diagnostic / failure | Supported action |
| --- | --- |
| Unsupported version, digest/shape/size failure | Keep original bytes/reference; use the matching inspected package or a reviewed explicit migration. Never rehash corrupt bytes to call them trusted. |
| Incomplete source generation or source-schema change | Inspect named public source, encoding, bound and adapter; retain last complete artifact, review changed semantics, retry only a complete compatible generation. |
| Network unavailable | Read retained knowledge offline; failed retrieval cannot renew freshness or extend promotions. No credentials/proxy dependency is added. |
| Interrupted/storage update | Reinspect actual `current` and health correlation; retry supported publication. A post-rename durability failure may already have activated complete bytes, so do not assert rollback from an exception alone. |
| Corrupt store/pointer | Stop writes; inspect with CLI fixed diagnostics and recover a complete identified backup into a separate directory. Do not overwrite evidence or edit a database. |
| Health mismatch or missing checkpoint | Report mismatch/gap/unavailable; resync replaces a full snapshot, not reconstructed history. |

## Support, Reuse and Security

Working schemas are explicit, not a permanent ABI. No schema is silently removed or
reinterpreted. A new incompatible version must preserve existing bytes and provide
negative conformance and an explicit migration/refusal policy. No actual Router MI
loader or Console adoption is claimed; their owners review their support/deprecation
policies and configurations separately. #19 is the separate installed-path receipt.
MI maintains package/parser/source-adapter fixes and truthful diagnostics; operators
maintain chosen installations, backups, byte limits and one-writer discipline.

The existing PEP517/660 `uv_build` backend is reused, not custom packaging machinery.
Comparison pin: uv tag0.9.30 commit `ea4560831e503c6ce34d18739476a71ac6e9a9de`.
Its `docs/concepts/build-backend.md`, `crates/uv-build/pyproject.toml`,
`crates/uv-build-backend/src/lib.rs` and actual LICENSE-MIT/LICENSE-APACHE establish
pure-Python/src inclusion, metadata/license/resource handling, deterministic
sdist/wheel and failed-build tests under MIT OR Apache-2.0. No upstream implementation
is copied. Existing #13 `3d427f2faecacf67be253ac04a155af862831435` framing,
#15 `6b6893b14169d616c41f82a0292386713da77206` atomic retained publication/import,
and #16 `23977d895cc58dca11e6aeaa81c8b9ffa97a9361` diagnosis are reused unchanged.
Only bounded lifecycle proof/support text is new; no parallel updater/store/policy.

Treat wheel/source code as executable: inspect its provenance before installation.
Treat artifacts/source text as untrusted data, never instructions. Use isolated
allowlisted environments and deliberate synthetic HOME/cache/temp paths for checks,
no owner credential mounts/environment/provider accounts. Per-input bounds and
strict shape/version/reference validation are required; authenticity/transport trust
are not supplied by hashing. Preserve NOTICE: normalized selected models.dev facts
at `f014f106dd414d575de2d0160d91267e2e7cb119` use MIT; raw official Z.ai pages are not
redistributed. Private telemetry/intake remains rejected under #17.

Repository-owned validation: `tests/verify_distribution.py` builds current and
historical wheels into fresh staging, rebuilds from sdist, verifies package contents
and installs them outside the checkout. `tests/installed_distribution_cases.py`
exercises installed migration/refusal/downgrade plus existing owned source-failure,
publication-interruption and operator/portable scenarios. These are synthetic offline
receipts, not release publishing, source truth, actual Router/Console adoption or GO.
