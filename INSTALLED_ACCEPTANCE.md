# Installed Explicit-Input Acceptance

Receipt for [MI #19](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/19),
2026-10-26. This is deterministic **installed MI -> installed Router library
interoperability**, not live/provider acceptance, default activation, D-082 active
admission, Kernel/Console adoption, a release or product GO. The owner continuation
explicitly permits original controlled public evidence for the positive case and
requires selected-source compatibility to be reported separately.

## Frozen Components

| Component | Canonical commit | Installed version / identity check |
| --- | --- | --- |
| MI producer | `d65891668b7e79f7b666c021f02a1b4bf8c4ca9c` | `model-intelligence==0.1.0`; all installed Python modules equal the exact source archive |
| Router consumer | `4162f6fa9f774beaf6e92d86b7ebc92f306da4bd` | `scarcity-router==0.1.0`; all installed Python modules equal the exact source archive |
| Router #176 | [PR #221](https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/pulls/221) | Merged at the Router commit above; approved HEAD `fdc85f17049d7b25d1f8a85f7ea98829a6595916` |
| Installation tools | CPython 3.12.0, uv 0.9.30 | Build constraints: `uv_build==0.9.30`, `hatchling==1.32.4` |
| Contracts | frame 1; public payload `/1`, `/2`; utilization `/1`; operator `/1` | No schema, temporal API or production package code changed by this harness |

Canonical Git refs were freshly resolved before implementation; MI was clean at
its stated revision and Router objects were fetched from its canonical Forgejo
remote into a temporary bare object repository. Each build uses `git archive` of
the exact commit, not a sibling working tree. The receipt records source tree and
archive digests. The harness itself records its distinct current HEAD/status;
the producer is deliberately frozen at Router's optional dependency pin, not
identified by the reused `0.1.0` version. Changes in this delivery are acceptance
tests, documentation and test-reuse attribution, not new producer semantics.

| Built artifact | SHA-256 |
| --- | --- |
| `model_intelligence-0.1.0-py3-none-any.whl` | `1ca0b6a0d0e99a5df4a75c66b625f9433553afda09f6b5928be574369a29d019` |
| `model_intelligence-0.1.0.tar.gz` | `0ee0bc06680c84dd963b48c5604bf2048dca8dcd17fd6ec1bd08f4f5cc67edc1` |
| `scarcity_router-0.1.0-py3-none-any.whl` | `1e3b5136d060ac34311321738a47abf916ec515f91a27592b5fd219d394bf456` |
| `scarcity_router-0.1.0.tar.gz` | `b785657fdcb2c66baf9e539f43f78ea3e10ca615079b0979e52a7bb98c771c5f` |

Both sdists rebuild byte-identical wheels with the declared tools/epoch. Every
wheel's Python module is compared to the exact export before installation; every
installed module is then compared to that export. Installed `direct_url.json`
must identify that local wheel; uv leaves its optional archive hash empty. The
installation uses `--require-hashes` with the independent wheel SHA-256, and all
installed wheel files except the installer-rewritten RECORD must match the wheel.
Imports and default
catalog/policy resources resolve under the isolated venv's `site-packages`, outside
both source exports and the MI checkout. Bootstrap selection succeeds **before MI
is installed**, with the original two-field machine envelope.

Router's `mi` extra declares exactly:

```text
model-intelligence @ git+https://forgejo.creatidy.com/Creatidy/model-intelligence.git@d65891668b7e79f7b666c021f02a1b4bf8c4ca9c
```

Offline installation explicitly supplies the two locally built wheels with
`router-wheel[mi]` and `--no-deps`. This is not a claim that an offline VCS resolver
retrieved the dependency. The runner verifies the source pin and installed wheel
identity itself; normal runtime dependencies are installed from Router's frozen
lock export, and `uv pip check` checks their availability. No registry package
named only `model-intelligence==0.1.0` is substituted.

## Reproduction

Prepare canonical objects and approved locked build/runtime wheels separately.
No provider authentication or inference is needed. Use a new staging directory
for every complete run; failures retain logs and artifacts rather than overwriting
the earlier receipt. Example from this checkout:

```sh
git clone --bare --single-branch --branch develop https://forgejo.creatidy.com/BioMedical-IT/scarcity-router.git /tmp/kilo/mi19-router-objects
uv run --no-sync python tests/verify_installed_router.py /tmp/kilo/mi19-installed-check --router-objects /tmp/kilo/mi19-router-objects --uv-cache /tmp/kilo/uv-cache
```

The runner builds and tests in an allowlisted child environment with synthetic
HOME/temp/cache paths, `UV_OFFLINE=1`, disabled Python downloads and bytecode, and
fixed `SOURCE_DATE_EPOCH=1792976400`. The custom selection process also refuses
socket creation/DNS/connections. Both collectors are deterministic synthetic
status/eligibility inputs; it never falls back to provider collection.

Outputs: `receipt.json`, `commands.log` with commands/exit codes/test names/counts,
`integration.json`, installed metadata, wheel/sdist files, complete publication
directories, expected reference, CLI/reader snapshots and per-decision immutable
`cut.json`, `context.json`, `decision.json`, `manifest.json`, `envelope.json`.
Retain that directory as one receipt. It contains original synthetic local context,
not owner credentials, private quota or an actual task.

## Positive Use

The maintained Router synthetic fixture declares an exact model subject, public
channel, native configuration, independently explicit effort, interface/version,
source observation/revision/freshness and advertised integral input allowance in
tokens with an explicit basis. Physical model identity remains unknown. Its
`example.invalid` source and `owned-synthetic` rights are controlled test evidence,
not assertions about a manufacturer's actual 4096-token limit.

The installed MI codec records the expected reference **before** `producer.publish`;
the publisher must return that exact reference and retain the exact bytes. Installed
`retained` and operator inspection validate the publication. Installed
`MIConsumer.load(path, expected_reference)` loads the digest-addressed artifact.
The installed default bootstrap catalog/policy and reviewed exact fixture binding
feed actual `selection_app.select_from_inputs` with a fixed microsecond clock.

A spy at the actual `select_model` boundary asserts that the incoming catalog
already contains `MI public input 4096 tokens`, then calls the original selector.
The actual selected explanation contains that fact. This is not a post-selection
annotation or a replacement selector. Removing only the display annotation makes
the complete decision equal to baseline; removing it from the evaluated catalog
makes the complete catalog equal to bootstrap. Ratings, hard properties, identity,
eligibility, private capacity and policy are unchanged.

Compatible B is published and loaded inside the OpenAI collector, after A was
captured but before actual evaluation. That decision still uses A; the next uses
`MI public input 8192 tokens`. Installed `decode_decision_utilization` verifies the
actual machine envelope, exact cut/evaluation time/decision/context/manifest and
emitted reference. Replay from retained A reproduces its original artifacts even
after B is active. Offline evaluation at the freshness boundary reports stale,
not positive availability. No running Attempt or live execution is claimed.

| Immutable artifact | A SHA-256 | B SHA-256 |
| --- | --- | --- |
| Cut | `7ddf4dcb1e33b8ec76e24677e31c69c1b8d56b3fc898bd7ec3853ad63c7b552f` | `3812a57a51ed5659270f07f3b02a83032ed2b10b1ac09adb42f2f6d6c2b40b22` |
| Context | `bbc7628a6ede74e0e2628d04edf8addf7f85815b923a711b72047fd5c3daea15` | `ebbec02f4627f64d957a917a3cb3d17285f74fac6b461096532037c3f743f0cc` |
| Decision | `a10f8f793bdf4c6d879dc735a6f8a36238fdbb391581db00ec7d8bf8e09da071` | `a78eda31c0a3139c0d160dc48cddadc6fa68c986c105289068ff0440ac4b7c11` |
| Utilization manifest | `40a1f06c29183c0b473289ff3152a6dd95f601ada1ed9b1a49f50de600eb2ad9` | `c20bb52ad9833c1cffef78106dcffa5e5c0e4dd4120431149173969a3f190158` |
| Machine envelope | `2d89ef788f74f59e7250a49e974f1e0b5da3640aa5a870b664089afdb5262609` | `741c86fd87d989e27cdee9c4f342b078d895b9e029e2dda20048617ecf69457e` |

## Coverage And Recovery

The installed runner executes **62 maintained tests**: Router's 16 consumer tests
and MI's 5 producer, 17 selected-source, 6 operator and 18 independent portable
operator tests. They import installed distributions, not source packages. The
unchanged Router test/helpers and bootstrap resources are staged from its exact
archive; test reuse and Apache-2.0 provenance are recorded in `NOTICE`.
The additional installed path checks include **9 explicit publication/consumer/
generation refusals**, **6 utilization-binding refusals**, **12 MI and 73 Router
source-module comparisons**, and **25 existing selected-source/bootstrap identity
pairings** that still cannot satisfy scope/configuration requirements. These are
checks, not additional unittest test-count claims. The full MI gate separately
passes 178 repository tests, Ruff, basedpyright (zero errors/warnings), locked sync
and Git whitespace checks.

| Case | Installed evidence |
| --- | --- |
| Digest/cut/version/malformed/oversize/member/source rejection | Router tests plus explicit expected-digest, truncation, unsupported format/schema and oversized update refusals; last consumer cut and publication unchanged |
| Scope/channel/configuration/model mismatch | Exact-binding Router tests; incompatible publication scope refuses; no wildcard/variant-to-effort/physical-identity inference |
| Missing/rewritten/truncated history and unsupported rollback | Router history/revision tests; original A cannot replace active B in either consumer or publisher |
| Known/unknown/fresh/stale/future/conflict | Router tests distinguish labels; future successors do not replace current facts early; no implicit authority or recency winner |
| Unsupported units/meaning/rights | Router native-limit/rights tests refuse positive facts; unknown never becomes unlimited, free or an entitlement |
| Withdrawal/revocation/retraction | Router ordinary/critical/future revocation and admissible/inadmissible restoration tests retain notice history and provenance |
| Expired promotions/future correction/withdrawal | Installed producer lifecycle test exercises existing effective-time projection and retained cuts; no invented active-admission policy |
| Interrupted/failed/incomplete update and offline | Installed publisher interruption/source-failure tests and custom retained-B checks; source failure cannot renew freshness or rewrite A |
| Decision/context/cut/time/manifest/reference tampering | Installed accepted MI verifier rejects six independently changed bindings; Router also rejects changed envelope/result/context/manifest |
| No MI / explicitly empty MI / valid MI | Base installation works without MI; empty consumer preserves baseline decision but emits an explicit unknown-cut utilization; valid consumer changes explanation only |
| Operator/reconnect/dedup/history gaps | Installed CLI status=inspect=export=reader snapshot; portable tests independently validate full snapshots, explicit gaps, resync and transport-only silence |

Supported recovery remains [the #18 procedure](src/model_intelligence/INSTALLATION.md):
preserve complete artifacts/references, retry only complete compatible generations,
resync full snapshots explicitly and use a separate preserved backup for older cuts.
Do not edit `current`, prune history, invent a migration or rehash corrupt inputs as
trusted. Publication and health are separate observations, not one transaction.

## Selected Source And Limits

Actual installed `zai.normalize` consumes all eight original MI upstream-shaped
captures and actual `producer.publish` publishes the result. The consumer loads
those exact bytes. **No positive selected-source adoption is established.**
`zai.SCOPE.channel` is null; per-model subjects have different public channels but
no native configuration or explicit subject effort; their observations have unknown
freshness. `ModelBinding.matches` requires a nonnull subject channel equal to scope
channel and exact scope/subject configuration with independently known effort.
Null is not a wildcard. Model alias/variant and a plan-managed lane cannot repair
those facts or establish physical execution. Native meanings also cannot be
converted to an input allowance merely because their numeric values look useful.

This is a selected-source adoption limitation, not a failure of the owner-authorized
controlled installed interoperability test. Positive adoption of those particular
source facts needs separately accepted curation and Router-owned exact associations;
it is not fixed by mutating Router, changing MI `/1` or `/2`, or enabling D-082.

Component implementation and deterministic installed integration are demonstrated
for these pins and this explicit library seam. Live/provider behavior, default MI
activation, active-admission/calibration, Kernel #55 utilized-reference adoption,
Console/browser integration, deployment, public release, full A/B/C value and final
project/product GO remain **unaccepted or unverified**, not silently skipped passes.
No foreign repository changed; no provider/model call or Daybreak audit ran.
