# Coding Benchmark Evidence Comparison

This read-only comparison is generated from the `models-dev.coding-benchmarks/1`
publication. Values are attributed observations, not normalized ratings.

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
