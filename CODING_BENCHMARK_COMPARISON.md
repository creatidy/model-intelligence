# Coding Benchmark Evidence Comparison

This read-only comparison combines the separate M1-01
`models-dev.coding-benchmarks/1` publication with M1-02's official
`terminal-bench-4.0.0-submissions` scope. Values remain source-attributed
observations, not normalized ratings.

## Source and Rights

The source is the four selected TOML model records at
[models.dev commit `3fb4bb98e633ff1af1b94f84ba07c8549e859aa8`](https://github.com/anomalyco/models.dev/tree/3fb4bb98e633ff1af1b94f84ba07c8549e859aa8).
Its exact-revision [MIT license](https://github.com/anomalyco/models.dev/blob/3fb4bb98e633ff1af1b94f84ba07c8549e859aa8/LICENSE)
covers the repository's model TOMLs. The upstream README documents benchmark
records as part of its TOML model-data format. The selected records point to
first-party OpenAI or Z.ai model reports. MI retains those citations and the
source content hashes, not copies of those reports.

For GLM configuration only, the provider-reported setup was independently
checked against the pinned Z.ai model-card README revisions
[`GLM-5.3` `ba32f8c19c8738e2c57c71798c601d477a7bf844`](https://huggingface.co/zai-org/GLM-5.3/tree/ba32f8c19c8738e2c57c71798c601d477a7bf844)
and
[`GLM-5.3-Flash` `46a050bec13002ad29ee795c16e61cf4fa3c4a9c`](https://huggingface.co/zai-org/GLM-5.3-Flash/tree/46a050bec13002ad29ee795c16e61cf4fa3c4a9c).
Those reports say Z.ai ran DeepSWE with mini-swe-agent, temperature 0.95,
top-p 1.0, a six-hour timeout and 400K context for both models. The adapter
records these provider facts with the pinned card references; it does not copy
the cards' tables or images.

The official SWE-Marathon v1.1 webpage publishes rows for the candidates, but
its separately hosted leaderboard data has no verified data-use license. MI
does not copy its scores. The GLM-5.3 SWE-Marathon row below comes from the
MIT-licensed models.dev TOML, cites Z.ai's model card, and explicitly records
its modified anti-cheat checks; it must not be treated as the official
leaderboard row or as directly comparable to other candidates.

Artificial Analysis API values are not part of this publication. The bounded
Free-endpoint test exposed the headline Intelligence, Coding and Agentic
indices, six capability indices, Intelligence Index cost (including its
cost-per-task field), token prices and median performance, but not individual
benchmark scores. Its terms restrict use in third-party model selection
products absent prior written consent (`AA_PRODUCT_USE_RIGHTS` is `UNVERIFIED`).

## Candidate Evidence

| Candidate | Available selected evidence | Tested configuration and provenance | Comparison status |
| --- | --- | --- | --- |
| GPT-6.1 Sol High | **UNKNOWN**: no benchmark row in the selected model record. The GPT-6.1 Sol product report provides no DeepSWE numeric score or exact agent configuration. | Exact identity is distinct from GPT-6 Sol. Do not substitute GPT-6 Sol's earlier score. High-effort benchmark evidence is unavailable in this source slice. | No measured comparison. |
| GPT-6 Luna Max | DeepSWE v1.1: `66.6`, metric `score`, native unit **UNKNOWN**. | `max effort`; source-reported date `2026-09-22` (not established as evaluation date); harness and task/evaluator details **UNKNOWN**. models.dev cites OpenAI's GPT-6 Sol/Luna report. | Not directly comparable: GLM sources use a different provider report/configuration; Luna harness and native unit are missing. |
| GLM-5.3-Flash | DeepSWE v1.1: `63.4`, metric `resolved`, native unit **UNKNOWN**. | `max effort`; Z.ai provider-run, mini-swe-agent, temperature 0.95, top-p 1.0, six-hour timeout, 400K context. Evaluation date **UNKNOWN**. | Same named DeepSWE harness and reported settings as GLM-5.3, but units/task-level uncertainty remain; not a model-only controlled result. |
| GLM-5.3 | DeepSWE v1.1: `66.9`, metric `resolved`, native unit **UNKNOWN**. SWE-Marathon v1.1: `42.5`, metric `score`, native unit **UNKNOWN**. | DeepSWE: `max effort`, Z.ai provider-run mini-swe-agent, temperature 0.95, top-p 1.0, six-hour timeout, 400K context. SWE-Marathon: `max effort`, Z.ai provider-run, Claude Code 2.1.207, temperature 1.0, top-p 0.95, 128K output, 1M context, modified anti-cheat checks. Evaluation dates are **UNKNOWN**. | Different benchmarks and metrics; the SWE-Marathon setup is explicitly modified. No cross-benchmark comparison. |

The numeric values above are the original source values and metric labels. MI
does not convert them to percentages, assume the meaning of `resolved` or
`score`, infer missing reasoning settings, or derive a winner. The two GLM
DeepSWE entries share a named harness, provider evaluator, version, reasoning
setting and reported runtime parameters, but native units, exact task sampling
and repeated-run uncertainty are not established; they remain model-plus-harness
observations, not a controlled model-only result.

## Relevance to the Kilo Task

DeepSWE and SWE-Marathon concern software-engineering agents working in real
repositories, so they are more relevant than general knowledge or static code
generation tests to diagnosing a defect and making a repository change. They
are still not exact proxies for the stated Kilo task (diagnose a repository
defect, implement a fix, run tests and prepare a PR): the selected records do
not establish matching task sets, scoring units, harnesses and evaluators across
the candidates. The excluded SWE-Marathon leaderboard cannot fill those gaps
without verified data rights.

## Reproducible Publication Receipt

The adapter fetches only the four HTTPS raw TOML paths pinned to the commit
above, with an 8,192-byte per-source ceiling, identity encoding, no redirects,
and complete-generation validation. It retains only DeepSWE and SWE-Marathon
benchmark claims in MI's existing immutable `/2` publication contract. The
source row's original metric, score, reported variant, harness, date, and
citation are preserved; unreported units remain `UNKNOWN`. Refreshing a source
does not retract absent rows or rewrite prior observations.

The generated receipt records the actual retrieval timestamp, exact source byte
counts/content SHA-256 values, publication digest, and normalized comparison in
the issue delivery evidence. It is reproducible from the pinned source URLs and
`model_intelligence.benchmarks.refresh`; no source response fixture substitutes
for this receipt.

To refresh the pinned source set and print the comparison from the retained cut:

```python
import json
from datetime import UTC, datetime
from pathlib import Path

from model_intelligence.benchmarks import compare, refresh
from model_intelligence.producer import retained

directory = Path("public-artifacts")
directory.mkdir(exist_ok=True)
_reference, result = refresh(directory, at=datetime.now(UTC), max_artifact_bytes=65536, timeout=20)
if not result.succeeded:
    raise RuntimeError("benchmark source refresh failed")
publication = retained(directory, max_bytes=65536)
if publication is None:
    raise RuntimeError("benchmark publication unavailable")
print(json.dumps(compare(publication[2]), indent=2, sort_keys=True))
```

**Observed receipt:** retrieval `2026-10-27T22:32:05.083650+00:00`, publication
SHA-256 `09868c7c7b867e9585b9a652c678995809d60b674e2de906598708a2964304aa`.

| Source record | Bytes | Content SHA-256 |
| --- | ---: | --- |
| `models/openai/gpt-6.1-sol.toml` | 547 | `b180d58dd12d19d8277fa6bd7aff847941c314f9bd03c70c765ba3c253b4e081` |
| `models/openai/gpt-6-luna.toml` | 702 | `d80644fc4d2ebc811be3a361a5654637c8f677e4bed1d42e0a8ee8e03a14d3b3` |
| `models/zhipuai/glm-5.3.toml` | 3,684 | `7f119f1e905d0187a505ab1af04ef123a02bf23c3a3e2ae6eb44630334e5106d` |
| `models/zhipuai/glm-5.3-flash.toml` | 2,329 | `7c2ce22a6ecd64a1d8b33ef60382c276973ce11098bed89ef2fa0199b5fdafde` |

Provider configuration sources (configuration facts only, not table data):

| Provider card | Revision |
| --- | --- |
| `zai-org/GLM-5.3/README.md` | `ba32f8c19c8738e2c57c71798c601d477a7bf844` |
| `zai-org/GLM-5.3-Flash/README.md` | `46a050bec13002ad29ee795c16e61cf4fa3c4a9c` |

## Terminal-Bench 4.0 Evidence (M1-02)

### Source and Rights

The source is the official `harbor-framework/terminal-bench` repository at
commit [`6964e9252c90227fc1cfa26cbc59aee4134792e4`](https://github.com/harbor-framework/terminal-bench/tree/6964e9252c90227fc1cfa26cbc59aee4134792e4).
`leaderboard/leaderboard.yaml` identifies Terminal-Bench 4.0.0; the official
evaluator pins `terminal-bench/terminal-bench` to dataset content
`sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732`.
The benchmark release commit is
[`452bf305c6daa62fc59061d22133a7cbc7c1572e`](https://github.com/harbor-framework/terminal-bench/tree/452bf305c6daa62fc59061d22133a7cbc7c1572e).

MI reads only four result JSON files under `leaderboard/submissions/` in this
pinned repository. The root Apache-2.0 license's Sections 2 and 5 grant
redistribution of the Work and intentionally submitted contributions;
`leaderboard/SUBMIT.md` documents the per-submission PR/maintainer-promotion
path. The selected files are part of that licensed repository and have no
submission-directory or per-file license override. This is a source-level
rights basis for these records, not an assumption that software licensing
automatically covers unrelated leaderboard databases. The compatible
Apache-2.0 license is included in this MI repository's `LICENSE`.
The live official board at [tbench.ai, version 4.0](https://www.tbench.ai/?version=4.0)
was checked against these records as a display cross-check; reuse is based on
the pinned repository contributions, not an assumption that the rendered site
table itself carries that repository license.

The Hub Terms assign raw execution content to customers. MI does not copy the
task dataset, trial-ID lists, logs, outputs or raw Harbor Hub execution records.
The `source_jobs` identifiers carried in the licensed submission records are
retained only as provenance links. MI relies on the Apache-licensed summary
records, not on redistribution of Hub job payloads.

The upstream guide states that community Terminal-Bench 4.0 submissions are
closed and only maintainer-run submissions are accepted now. M1-02 uses the
existing official entries and makes no upstream submission or mutation.

### Measurements

The source `accuracy` field is a resolution rate: a selected trial succeeds iff
verifier reward is greater than zero, and higher is better. The official
submission validator requires all 66 canonical tasks and at least five trials
per task. Each selected record contains 330 trial IDs. The reported 95%
confidence-interval half-width uses the official task-level standard error and
normal `z=1.96` calculation:

```text
variance = sum(p_i * (1 - p_i) / (k_i - 1)) / n_tasks^2
ci95_half_width = 1.96 * sqrt(variance) * 100 percentage points
```

This is per-configuration uncertainty, not a pairwise model-significance test.
`metadata.date` is a model release date, not an evaluation date. The separate
Hub source-job pages show run start times, but do not report a common timezone
or final evaluation timestamp; the typed MI claims therefore preserve
evaluation date as **UNKNOWN** and treat job start as contextual provenance.
Every model revision is also **UNKNOWN**.

| Candidate | Submitted model ID and effort | Agent/harness and evaluator | Terminal-Bench 4.0.0 resolution rate | Model release date | Source job start (displayed time, timezone unknown) |
| --- | --- | --- | --- | --- | --- |
| GPT-6.1 Sol | `openai/gpt-6.1-sol`, max | Codex 0.159.0; official Terminal-Bench verifier/maintainer pipeline | `58.18% ± 3.11 pp`, 192/330 successes | 2026-09-29 | 2026-09-30 02:43, [job](https://hub.harborframework.com/jobs/3837153f-6673-539d-b3e2-99a6edd3c5db) |
| GPT-6 Luna | `openai/gpt-6-luna`, max | Codex 0.159.0; official Terminal-Bench verifier/maintainer pipeline | `16.36% ± 2.72 pp`, 54/330 successes | 2026-09-22 | 2026-09-29 19:34, [job](https://hub.harborframework.com/jobs/38bcca13-9ed9-5cf2-a864-d777ae4c76d1) |
| GLM-5.3 | Displayed model/org `GLM-5.3` / Z.ai; raw source ID `anthropic/glm-5.3`; max | Claude Code 2.1.207; official Terminal-Bench verifier/maintainer pipeline | `41.82% ± 3.23 pp`, 138/330 successes | 2026-08-14 | 2026-08-26 17:16, [job](https://hub.harborframework.com/jobs/18e4ee29-d8b4-516b-b79d-b8bad5bcd5be) |
| GLM-5.3-Flash | `z-ai/glm-5.3-flash`, none | Claude Code 2.1.285; official Terminal-Bench verifier/maintainer pipeline | `35.76% ± 3.54 pp`, 118/330 successes | 2026-08-26 | 2026-09-30 01:14, [job](https://hub.harborframework.com/jobs/e498ef42-3647-58ea-8790-b18f53c18d89) |

The Sol and Luna source job pages showed extra pending attempts (22 and 70
respectively); each versioned submission lists the 330 selected trials used by
its reported metric. The official CI checks the 66-task/minimum-five-trial
requirement. These pending extras are not silently counted in the published
`n=330`. The GLM-5.3 raw route alias `anthropic/glm-5.3` is preserved alongside
the official model display and Z.ai organization; MI does not silently rewrite
the submitted identifier.

### Comparability to Kilo

Sol and Luna use the same benchmark/task version, Codex version and max-effort
setting. Their submitted rates differ by 41.82 percentage points and their
published per-task intervals do not overlap. This supports a narrow
configuration-level observation for those Codex/max submissions, not a
pairwise test or a guarantee for Kilo Sol High. The Kilo harness and its
configuration-specific quality mapping remain unmeasured.

GLM-5.3 and GLM-5.3-Flash differ in effort and Claude Code version; their rates
are not a controlled GLM comparison. Cross-comparisons between Codex and Claude
Code are likewise not model-only comparisons. Terminal-Bench is relevant
repository-agent evidence, but no global winner, Router 1-5 rating, or
automatic admission decision follows from these observations. M1-01 DeepSWE
evidence remains present as a separate benchmark, with its own metric and
limitations.

### Terminal-Bench Resource Context

The selected records report total tokens as uncached input plus output, with
cached input separately. `total_cost_usd` is the official submission metric
code's sum of per-trial Harbor `cost_usd` telemetry. It is not an invoice,
verified subscription price, quota consumption or Kilo-session cost.

| Candidate | Source token total (uncached input + output) | Cached input separately | Source-reported selected-run cost |
| --- | ---: | ---: | ---: |
| GPT-6.1 Sol | 1,459,936,514 | 1,354,187,811 | USD 634.24 |
| GPT-6 Luna | 3,909,124,893 | 3,778,954,219 | USD 72.14 |
| GLM-5.3 | 8,677,039,373 | 8,444,041,600 | USD 2,727.63 |
| GLM-5.3-Flash | 2,916,503,275 | 2,786,100,736 | USD 118.73752448 |

These resource fields are provenance context only; MI does not use them to rank
models or infer a model-quality score.

### Reproducible Terminal-Bench Receipt

The adapter fetches only these four HTTPS raw JSON paths pinned to repository
commit `6964e9252c90227fc1cfa26cbc59aee4134792e4`, with a 65,536-byte per-file
ceiling, identity encoding and no redirects. It validates the complete
generation, exact candidate/agent/effort, release-date metadata, success count,
unit/accuracy, confidence bounds, source-job references and 330 unique selected
trial IDs. It validates but neither writes nor outputs those raw trial IDs.
The four Terminal-Bench claims publish to a separate immutable `/2` scope; M1-01
history and Z.ai scope remain unchanged. Token/cost information is confined to
the source-linked read-only comparison receipt, not typed quality claims.

**Actual source-to-publication run:** capture `2026-10-28T12:15:21.131014+00:00`;
the M1-01 cut SHA-256 was
`5a9e78c6135e254a525c5be3cf48e83dd01fd5eb922a85532b8c18013a25ec8e`, and the
Terminal-Bench `/2` publication SHA-256 was
`f6f64fdbc8e2b2dd8431d705ece6c224bc4203dad56626078abe13f22e3f5550`. All four
pinned GitHub raw-source fetches returned HTTP 200 and passed complete-generation
validation.

| Official submission file at the pinned commit | HTTP | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `2026-09-30-openai-gpt-6-1-sol-max-codex.json` | 200 | 15,889 | `2bb4407be33d9ea12c9d1173ee749b1296bba0b5fb8442c87c9cc7be3c2d8bf7` |
| `2026-09-30-openai-gpt-6-luna-max-codex.json` | 200 | 15,881 | `f063aee31d6599b95ebe37341071bc625bf042362b45590db4cc50efbb5cb8a8` |
| `2026-08-26-anthropic-glm-5-3-max-claude-code.json` | 200 | 15,927 | `f8c5a8ef9dab054e78444f6e2e4b756dda2cf193839a3a357ce2a4d32a0c24c9` |
| `2026-10-06-z-ai-glm-5-3-flash-none-claude-code.json` | 200 | 15,898 | `93d786abffa53c6618b7fe781bb022dfedbbb3ea79786c035ed64ca8d529de6b` |

To refresh the separate scopes and regenerate the combined read-only comparison:

```python
import json
from datetime import UTC, datetime
from pathlib import Path

from model_intelligence.benchmarks import refresh as refresh_coding
from model_intelligence.producer import retained
from model_intelligence.terminal_bench import compare, refresh as refresh_terminal

at = datetime.now(UTC)
coding_dir = Path("public-artifacts/coding")
terminal_dir = Path("public-artifacts/terminal-bench")
_coding_ref, coding_result = refresh_coding(coding_dir, at=at, max_artifact_bytes=262144, timeout=30)
_terminal_ref, terminal_result = refresh_terminal(terminal_dir, at=at, max_artifact_bytes=262144, timeout=30)
if not coding_result.succeeded or not terminal_result.succeeded:
    raise RuntimeError("one or more pinned source generations failed")
coding = retained(coding_dir, max_bytes=262144)
terminal = retained(terminal_dir, max_bytes=262144)
if coding is None or terminal is None:
    raise RuntimeError("one or more immutable publications are unavailable")
print(json.dumps(compare(coding[2], terminal[2], terminal_result.submissions), indent=2, sort_keys=True))
```

## Combined Coding-Agent Comparison

DeepSWE and Terminal-Bench both concern repository problem-solving, so they add
evidence relevant to the stated Kilo defect/fix/tests/PR task. Terminal-Bench 4.0
supports a narrow same-Codex-version/max-effort Sol-versus-Luna observation; the
submitted Sol rate is higher and the published per-task intervals do not
overlap. That is a result for those model-agent configurations on that benchmark,
not a pairwise test or a guarantee for Kilo Sol High. GLM has source-backed
Claude Code observations, but effort and agent-version differences preclude a
controlled comparison with each other or with Codex. DeepSWE, Terminal-Bench,
their distinct metrics and remaining unknowns stay separate. No winner, Router
1–5 rating or automatic admission decision is generated.
