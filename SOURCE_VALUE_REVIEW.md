# Model Intelligence Product Value

## Question and Decision Basis

Does MI provide material value beyond upstream, and what should it own? The
[owner's revised mandate][mandate] for [issue #12][issue] replaces the earlier
fixture/limitations-led packet. This analysis compares source coverage with actual
Router needs, not with a checklist of R2 types. The conclusion is a recommendation,
not an owner product GO, implementation authorization or full A/B/C proof receipt.
Keep issue #12 open and PR #23 unmerged. No #13-#19 implementation is selected.

A same-context benchmark/price conflict is not a viability prerequisite. Unknown
campaign boundaries and conflicting claims are normal domain states, not research
failures. They can matter operationally even without a synthetic fixture. R2 and
historical STOP_REVISE decisions are unchanged; this document does not restart
either stopped experiment or silently extend R2's representation.

Read-only source inspection was performed on 2026-10-05. Observations below mean
the named document/file represents a fact that way, not that its claim is true of
every deployment. Pinned files permit source-level checking; mutable pages have
no retained durable capture. Retrieval date, publication label, revision time,
business-effective time and installed behavior are distinct. No provider runtime,
paid API, private account or installed consumer path was exercised. Source claims
and test results are not interchangeable; offline guards only check this document.

## What Upstream Already Solves

These are bounded findings at the [inspection pins](#inspection-references), not
global absence claims or an audit of every record. Use upstream's complete view
before attributing a consumer's wrong endpoint or lost fields to missing data.

| Source | Useful coverage actually inspected | Residual limitation and appropriate use |
| --- | --- | --- |
| [models.dev][models] | `schema.ts`: canonical models/provider offerings, `canonical_model_id`, native reasoning toggle/effort/budget, numeric context/input/output limits, modalities, tools/structured output, tiered/cache/reasoning/audio prices, lifecycle status and contextual `BenchmarkResult`. `generate.ts`: inheritance, provider overrides and explicit omission. Git pins/history already supply source snapshots. | Adopt the catalog, not a replacement MI inventory. Per-field cost/capability provenance, alias transition intervals and assertion strength are not general structured fields in the inspected schema. Optional benchmark context is not guaranteed populated. A published resolved value is not an unresolved competing-claim set or deployment attestation. |
| [genai-prices][genai] | `types.py`, `data_snapshot.py`, `prices/README.md`: model matching/fallback, usage extraction, tiers, historical/date/daily-window conditions, bundled/custom snapshots and API valuation. `zai.yml` and `deepseek.yml` document specific approximation/condition limits. | Use suitable valuation in Router, not a new MI calculator. Matching is not physical identity. Last-active price precedence is not conflict preservation. An upstream enhancement or qualified consumer adapter can solve a narrow precision gap. |
| [AI Model Watch][watch] | `models.json`: exact API names, nullable limits/prices, status, `deprecated_on`, `retires_on`, `replacement`, source URLs and explanatory notes. [API docs][watch-api]: lifecycle feeds, explicit null semantics, ETags and schema versioning. | Reuse lifecycle discovery. Channel exceptions and inferred-versus-direct claims can be prose, requiring interpretation. The pinned September 6 dataset envelope differs from the later live v2 documentation; do not combine them into a fictional version. |
| [Model Price Watch][prices] | `models.json`, `price-history.json`, `CHANGELOG.md`: current/native pricing context, selected promotions and future-effective changes, daily history, source/receipt/confidence metadata, corrections and supersession. [API docs][prices-api] expose history and as-published archives. | Do not build another generic price tracker. Some complex applicability remains narrative. An upstream `verified` label is its assertion, not MI verification. A selected GLM receipt's referenced capture returned 404 at this public pin; that limits replay there, not proof that no capture exists elsewhere. |
| [codingplan][plans] | `plans.json`, `models.json`, `plan-models.json`, `entity-data.js`: separate plans/model relations, generated/schema versions, workload assumptions, measured/calculated/derived/unknown methods, time/context/service tiers, benchmark versions/configurations/confidence intervals. | Reuse secondary plan/configuration discovery. Derived token equivalents and four-week monthly assumptions are not official quota or private entitlement. Explain derivations instead of promoting a field named `measured*` into a provider promise. |
| Producer/client references | [Z.ai model/plan docs][model-doc], [campaign][campaign], [ZCode source][zcode] and its versioned NOTICE/CLI code explain channel/build-specific rules; contextual benchmarks can retain original [Artificial Analysis references][aa-api]. | Prefer direct citations for exceptions. Public source/documentation supports advertised or source-supported assertions, not actual account availability, physical-model enforcement or task-specific quality ratings. No new benchmark score is justified. |

Models.dev deserves particular attention. Its `BenchmarkResult` includes metric,
harness, variant, dataset, version, source and date; the Flash record supplies
Terminal-Bench version, Claude Code harness and max-effort context. Claims that
upstream lacks contextual benchmarks are incorrect. The generator deliberately
does not inherit benchmarks/license/links/weights into provider records: use
`catalog.json`, or join `models.json` through `canonical_model_id`, rather than
expecting `api.json` alone to contain all canonical evidence. Specialized types
are filtered by default; `type=all` omission checks are not retirement signals.
The hosted `model-schema.json` enumerates provider/model strings, not a full
knowledge-artifact provenance contract. These are upstream use details, not MI
product features.

Nor is history unique to MI. Models.dev's [GLM file history][model-history] and
[September 19 price patch][price-patch] are immutable alternatives to a custom
tracker. Model Price Watch already represents `scheduled_price_change` with
`effective_at`/`announced_on`/source and correction events with supersession and
`corrected_from` references. Git and price histories can be reused; source commit
time still does not necessarily equal business-effective time.

## Router Need, Not Another Catalog

Read-only inspection used committed Router HEAD
`6c337a400b4cdc28ded543d2ae8ccf3749d79cb7`, a local issue branch, not canonical
develop. Four unrelated modified files were preserved; routing findings use the
committed blob, not working-tree changes. No Router tests, fetch, mutation or
runtime calls were performed. Exact paths are in [the reference table](#inspection-references).
These are inspection observations, not independently reproduced consumer receipts.

The existing composition loads local catalog/profile artifacts and projects runtime
inventory through reviewed tracks. It does not establish an MI/upstream consumer.
Calibration already requires dated evidence/confidence/rationale for known 1-5
ratings; unknown required dimensions fail. Public benchmarks cannot supply these
workflow judgments automatically. Runtime discovery/adoption and exact requested
model/effort checks are already Router responsibilities. Its promotion policy
already evaluates bounded recurring windows; MI must not duplicate that evaluator.

Three concrete public inputs are not reliably supplied in a directly usable form
by the inspected upstream views: changing alias/channel/configuration applicability
(E1/E4/E5), economic basis and conditional plan/cohort/client rules (E2/E3), and a
cross-source reference tying those interpretations to the facts actually adopted
(E6 and history examples). This is not evidence that no upstream could add them.
An upstream fix or Router adapter is a viable solution for each individual gap.

Router also needs information no public MI or catalog can supply: authenticated
available models/efforts, actual subscription generation/balance, shared quota
pools, installed compatibility/enforcement, private preferences, reservations and
task-specific calibration. Those are local facts, not MI coverage deficiencies.
For example, committed `gateway_coordinator.py` still conflates
variant with effort in some paths despite explicit catalog effort; more public
data alone cannot fix a consumer translation defect. Router-owned [#179][router-identity]
and [#184][router-economics] address local identity/economics. [#176][router-mi]
plans admitted/offline snapshots, but an open issue does not prove integration or
require a synchronous MI lookup on each inference call.

## Real Cases and Decision Consequences

### E1: Moving Aliases and Stale Guidance

The current [Coding Plan overview][plan-overview] says GLM-5.2/5.1 requests route
to GLM-5.3 and GLM-4.7 requests to Flash. The [current Claude guide][claude-current]
defaults the three Claude roles to Flash; an [older scenario guide][claude-old]
still describes GLM-4.7/4.5-Air. Defaults, manual overrides and cohorts are different
subjects, not automatically contradictions. The old page's pre-2025-09-30 user
cohort date is not an alias-upgrade instant. No exact rollout time was established.

Models.dev already separates canonical and provider identity, but a record for a
requested name is not an effective alias-history or physical deployment guarantee.
Router cannot transfer GLM-4.7 calibration or infer an Anthropic model from a role
label. Thin MI can preserve the public mapping claim, channel/cohort and change
uncertainty; Router retains requested/resolved/dispatched/observed identity and
decides whether a moving alias is admissible. A local pinned notice plus adapter
could do the same if no public interpretation is reused elsewhere.

### E2: Price Basis and Plan Generation

The [models.dev Coding Plan offering][plan-offering] has zero per-token cost and
explains consumption of plan credits. [genai-prices' Z.ai file][genai-zai] values
ordinary and Coding Plan usage at API rates. These are incremental token charge
versus indicative API-equivalent valuation, not a same-basis price contradiction.
Neither implies unlimited capacity or actual subscription marginal billing.

The [July 30 plan notice][plan-notice] adds credits-based plans while retaining
existing active accounting until billing expiry, with different V1/team and V2
upgrade transitions. Its publication label cannot date later material now present
on that mutable page. Router needs the unit/basis/cohort distinction to avoid
counting zero token charges as free quota. MI can normalize the public distinctions;
Router owns actual account generation, migration choice, remaining credits and
realized cost. Genai remains a suitable indicative calculator where its basis fits.

### E3: Promotion With Conditions and an Unknown End

The [campaign notice][campaign] states September 3-October 7, extended from
September 20, with a 23:00-09:00 next-day UTC+8 window. Paid plans, Flash rather
than GLM-5.3, supported client/channel and ZCode >=3.10 matter. ZCode/AutoClaw zero
consumption differs from other supported agents' doubled quota; exhausted private
five-hour/weekly quota can block participation. The overview separately advertises
all-day off-peak rules; do not invent stacking.

The inspected models.dev/genai entries do not encode this complete condition set,
though other upstreams already have promotions/history. MI's useful residual is
the public applicability interpretation, not rate arithmetic or quota policy.
Router evaluates it against account/client/channel/clock and its existing policy.
The exact terminal instant and final overnight inclusivity are unknown. Preserve
that uncertain bound; Router may decline to rely on the benefit near it. Do not
fabricate an expiry, renew a benefit on refresh failure, or reject the observation
as a research failure. An extension claim is known now without reconstructed
announcement/acquisition chronology. [Genai's Z.ai approximation][genai-zai] is
a separate API-price example, not this campaign: its date-only start constraint
acknowledges an eight-hour boundary approximation.

### E4: Capability and Availability Depend on Surface

The [model guide][model-doc] distinguishes multimodal Flash from FlashX, whose API
is live but Coding Plan availability is explicitly absent. The [switching guide][switching]
contrasts text-only GLM-5.3 and describes client configuration needed for 1M context.
Models.dev already has modalities, numeric limits and contextual benchmarks. Reuse
them; MI's residual is preserving provider/channel/configuration qualifications,
not another copy of every capability field. Router must verify its installed
interface before admitting an image or long-context task. A release-note date
cannot establish every capability's deployment instant on every channel.

Dataset removal also differs from unavailability: Model Price Watch's Rerank 3.5
history explains removal of an unsuitable per-token row while the model remains
live. AI Model Watch uses per-search pricing for that kind of product. Preserve
billing unit, source coverage removal and actual retirement separately. A missing
row must not cause Router to retire a source or price it at zero.

### E5: A Real Disagreement Without a Forced Winner

The [pinned Z.ai offering][api-offering] has a source comment saying thinking can
be disabled. The current [official model guide][model-doc] permits only enabled;
the [Coding Plan guide][switching] instead translates disabled/off into low effort,
still thinking. This is a source-comment discrepancy plus a channel distinction,
not proof that models.dev's structured API advertises a toggle: its actual
`reasoning_options` lists effort levels only. Genai already describes always-on
reasoning. No runtime change or rollout instant is inferred.

A no-thinking hard requirement or budget estimate cannot rely on those phrases
being equivalent. MI could retain attributed claims, scope and uncertainty, or
submit a small upstream correction. Router owns request translation, evidence
adoption and separately authorized runtime tests. It must not equate plan `disabled`
with native effort `none` or choose a conflicting fact solely by source recency.
No artificial same-context benchmark/price conflict is needed for this use case.

### E6: Versioned Client Is Not Physical Execution

The [ZCode pin][zcode] is package 3.14.3; its CLI has prompt dispatch, structured
harness output and catalog-conditioned model/effort choices. The [website changelog][zcode-changelog]
describes 3.14.4. `NOTICE.md` distinguishes public builds from official features/
promotions and the gateway's unaudited internal processing; the Computer Use entry
is an unavailable placeholder. Source-supported selection does not establish
physical enforcement, official-build campaign eligibility or observed workspace
behavior. README-update and release dates are different metadata, not a fabricated
deployment conflict. Thin MI could publish build-qualified public assertions;
Router owns actual inventory/identity, Kernel owns harness authority and adapter
tests. Pinned client code is already reproducible upstream evidence, not a reason
for a new MI runtime controller.

## Four Information Responsibilities

| Category | Exact responsibility and boundary |
| --- | --- |
| Reference/fetch upstream | Canonical models/provider offerings, native controls/limits, benchmark context, token rates/tiers, lifecycle feeds, upstream history and indicative genai valuation. Use correct endpoints and preserve references. Do not replace catalogs, calculators or established trackers. |
| Normalize in thin MI | Shared public identity/channel/configuration relationships; economic unit/basis; cohort/client/window/uncertain-boundary conditions; attributed disagreements and assertion strength. Preserve source-native meaning and unknowns, never infer private entitlement or calibrated ratings. Missing optional annotations must not block ordinary upstream use. |
| Preserve public history in MI | Only selected public interpretation/revision/correction/withdrawal history not recoverable from reused source pins/archives, plus the mapping/annotation version and cross-source evidence cut. Do not archive everything twice. Retain uncertain times rather than invent lineage, validity or acquisition history. |
| Own locally in Router | Authenticated inventory, accounts/balances/pools, reservations/admission, local alias/config translation, observed compatibility/enforcement, calibrated suitability, billing/valuation application, freshness/offline policy and the exact adopted public reference. Kernel retains Attempt/outcome authority and utilized-reference linkage. |

## Are Provenance and Snapshots Operationally Useful?

| Mechanism | Concrete operational problem solved | Thin/Router-only challenge |
| --- | --- | --- |
| Provenance and basis | E2 needs to explain why a zero token rate and API-equivalent cost differ; E4 needs to distinguish coverage removal from retirement. Source/method/units prevent false cheapness and unsafe fallback. | Existing references/notes solve much of this. MI earns value only when it preserves meaning across the join, not by attaching another URL. |
| Temporal history | E1's current alias must not silently rewrite a past decision; E3's extension/unknown bound and changed conditions must not become unconditional permanent discounts. Reproduce the public evidence known/adopted for a decision separately from later effective claims. | Git pins and MPW histories already cover much. A local adopted-source log suffices for one consumer; commit time is not business time. R2 alone is not a historical knowledge-at-T query. |
| Conflict handling | E5 needs to retain a disputed assertion without hiding channel differences or pretending a winner was runtime-tested. E2 should first be recognized as different economic bases, not put in a conflict bucket. | Correct upstream prose where possible. Do not build a generic conflict engine for every unequal field; Router decides use/abstention policy, MI does not rank authorities. |
| Versioned evidence cut | E2/E3 joins should not mix new plan terms with old economic mappings; E6 needs the exact client/assertion context used when a decision is explained later. Shared mapping version and source pins make that cut recognizable. | A Router-local lockfile/adoption record can provide this. Producer snapshots are files/library artifacts, not necessarily a service. Router must bind inventory/calibration/admission context as well; an MI cut cannot explain the whole decision. |

Router currently records catalog version/date, policy and registry/target evidence;
derived inventory projections can retain the same base catalog version even after
entries change. Therefore catalog version alone is not the entire utilized view.
An MI manifest would identify public inputs only; Router must still record its
derived state. Cross-source snapshot consistency is useful, but not uniquely MI.

## Alternatives, Costs and Copying Boundary

| Alternative | Benefit and concrete cost | Assessment |
| --- | --- | --- |
| Direct upstream + Router adapters (STOP separate MI) | Fewest components; models.dev full catalog, genai valuation, AMW lifecycle, MPW history, codingplan discovery and selected official notices. Router keeps reviewed annotations/pins. Costs local joins, notice upkeep and no shared public interpretation owner. | Credible baseline, especially for one Router. Most ordinary routing data does not require MI. |
| Thin reusable MI layer (ADAPT) | Shared public meaning/applicability and selected annotation history, independent of private runtime. Costs provider-specific curation, mapping review and compatibility/update discipline; upstream facts remain upstream's work. | Defensible residual scope for the concrete cases above. Prefer a library/artifact module over an always-on service. |
| Broad separate MI service (GO) | Central catalog, independent price/history collection, scoring and acquisition platform. Adds duplicated maintenance, outages, parsing/security and stale-data risk without creating truth. | Not justified by inspected needs or source coverage. No GO recommendation. |

Upstream contributions are a fourth delivery route, not a reason to fork broadly:
fix a misleading thinking comment or improve a date/condition model before adding
permanent MI logic. Separate MI ownership is worthwhile only for interpretation
used across public integrations or repeated Router onboarding, not private policy.
Kernel's reference retention alone is not an independent public-data consumer.

This analysis observes/cites public facts and adds original comparisons; that
route has no generalized dataset-redistribution gate. No upstream dataset/code,
raw price/benchmark table or external fixture is copied. If a future implementation
vendors or redistributes datasets, check rights for that actual material: AMW's
license expressly covers Data/docs with notices; MPW's `LICENSE-DATA.md` covers
listed datasets under CC-BY-4.0 attribution/change obligations. Software licenses
do not automatically cover every imported source. Neither that future copying
choice nor paid Artificial Analysis data is necessary for this recommendation.
Unknown copying rights block that copying route, not the public product question.

## Inspection References

All Git pins identify source inspected, not hosted-model deployment. API/docs URLs
are mutable, read 2026-10-05, with no retained durable capture or invented precise
acquisition timestamp. Findings use targeted records, not exhaustive data audits.
Independent documentation review may not retrieve these external objects under
its unchanged allowlist; citations and source-analysis attribution do not claim
independent external verification by that reviewer or passing offline tests.

| Reference | Pin and reproducible file/symbol scope |
| --- | --- |
| [models.dev][models] | `f014f106dd414d575de2d0160d91267e2e7cb119`: `packages/core/src/schema.ts` (`ReasoningOption`, `BenchmarkResult`, `ModelMetadata`, `ModelShape`), `generate.ts` (`inheritableModelMetadata`, `mergeBaseModel`, `applyOmit`), `filter.ts`, worker `catalogResponse`, canonical GLM/provider/plan records linked above. |
| [genai-prices][genai] | `36d4e77cc4e8a447f13d63d79326425493268d45`: `packages/python/genai_prices/types.py` (`ConditionalPrice`, date/time constraints), `data_snapshot.py`, `prices/README.md`, `prices/providers/zai.yml` / `deepseek.yml`. |
| [AI Model Watch][watch] | `d3441ada9b032c141778bde1aeb740b1f4cd2dff`: `models.json`, `README.md`, `LICENSE`; lifecycle/status/null/source fields and selected channel-exception notes. Mutable API documentation kept separate. |
| [Model Price Watch][prices] | `3bdbb63401153462baf330460165f92b256e4a1e`: `models.json` scheduled changes, `price-history.json` GLM/Cohere/Groq/Rerank events, `CHANGELOG.md`, `LICENSE-DATA.md`. Referenced GLM `data/evidence/.../2026-09-09.txt` was not replayable at this public pin. |
| [codingplan][plans] | `7a7e43268c8b56f0b0c4ccf2fd5d1581cf2a9c2a`: `plans.json`, `models.json`, `plan-models.json`, `scripts/entity-data.js`; method/workload/time/context and original benchmark configuration/version metadata. |
| [ZCode][zcode] | `29628c9acdb81b703bbd4080c207a0e7ce5e276e`: `package.json`, `NOTICE.md`, `README.en.md`, CLI `run.ts` / `prompt-command.ts` / `command-center/handlers/model.ts` / `effort.ts`, `packages/zcode-cua/index.js`. |
| [Router committed inspection][router-source] | `6c337a400b4cdc28ded543d2ae8ccf3749d79cb7`: `selection_app.py` load/catalog, `control_api.py` composition, `selection_types.py` rating evidence, `execution_sources.py` derived catalog/floors, `gateway_coordinator.py` resolution, `resource_state.py` costs/identities/freshness, `policy.py` promotion preferences, committed `routing_core.py` binding/spend/promotion methods. Local issue-branch snapshot, not canonical develop; dirty files excluded. |
| Router artifact/decision context | Same committed pin: catalog version 5, policy version 9 and tracks; `selector.SelectionDecision`, `gateway_audit.py`, `gateway_continuation.py`. Existing tests inspected, not executed: calibration, inventory adoption, exact model/effort validation and effective-limit enforcement. Planned [#176][router-mi] remains distinct from source implementation. |

## Recommendation

**ADAPT**: narrow MI to a reusable upstream-backed **public evidence normalization
and selected-history layer**, not a separate comprehensive intelligence service.
Material value is preserving economic basis, alias/channel/configuration scope and
conditional public rules that ordinary catalog/rate views do not reliably join;
the real cases show wrong-admission, misaccounting and irreproducible-decision risks.
The benefits exist without a fabricated benchmark conflict or exact campaign end.

Exact retained scope: references to upstream catalogs/history/calculators;
reviewed public mapping/applicability annotations and attributed uncertainty;
selected annotation/revision history; a recognizable versioned cross-source cut.
No replacement catalog, benchmark ranking/calibration, duplicate price tracker,
quota engine, account inventory, final router, mandatory feedback, generic scheduler
or per-inference resident MI service. Router-local policy/runtime remains local.
An uncertain campaign end is useful evidence, not a demand to enlarge R2 here.

Reject broad-product GO on present evidence. Keep STOP/direct-upstream viable:
if Router adapters or upstream contributions maintain E1-E6 without repeated public
curation, move the thin work there and do not maintain a separate MI product.
Conversely, repeated independently consumed interpretations or onboarding decisions
that share these annotations justify the small public module, not automatically
a service. Maintenance savings, additional consumer demand and installed benefit
have not been measured; they are explicit limits on scale, not invented numeric
thresholds or a reason to avoid making this recommendation.

This is the revised issue #12 product recommendation, not authorization for GO,
new schema/acquisition/distribution or migration of Router contracts. Keep issue
#12 open and PR #23 unmerged pending independent review and subsequent owner action.
Original synthetic/full-proof receipts remain unclaimed; unknown dates, source
conflicts and absent benchmark pairs no longer serve as product-viability gates.

[issue]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/12
[mandate]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/12#issuecomment-14721
[models]: https://github.com/anomalyco/models.dev/tree/f014f106dd414d575de2d0160d91267e2e7cb119
[model-history]: https://github.com/anomalyco/models.dev/commits/f014f106dd414d575de2d0160d91267e2e7cb119/providers/zai/models/glm-5.3-flash.toml
[price-patch]: https://github.com/anomalyco/models.dev/commit/ebfeed5f5eb53e48f6fdf659cf9907ee0172ec03
[api-offering]: https://github.com/anomalyco/models.dev/blob/f014f106dd414d575de2d0160d91267e2e7cb119/providers/zai/models/glm-5.3-flash.toml
[plan-offering]: https://github.com/anomalyco/models.dev/blob/f014f106dd414d575de2d0160d91267e2e7cb119/providers/zai-coding-plan/models/glm-5.3-flash.toml
[genai]: https://github.com/pydantic/genai-prices/tree/36d4e77cc4e8a447f13d63d79326425493268d45
[genai-zai]: https://github.com/pydantic/genai-prices/blob/36d4e77cc4e8a447f13d63d79326425493268d45/prices/providers/zai.yml
[watch]: https://github.com/Khavel/ai-model-watch-data/tree/d3441ada9b032c141778bde1aeb740b1f4cd2dff
[watch-api]: https://aimodelwatch.dev/api
[prices]: https://github.com/romanshumy/llm-prices-data/tree/3bdbb63401153462baf330460165f92b256e4a1e
[prices-api]: https://modelpricewatch.com/api/
[plans]: https://github.com/wmpeng/codingplan/tree/7a7e43268c8b56f0b0c4ccf2fd5d1581cf2a9c2a
[model-doc]: https://docs.z.ai/guides/vlm/glm-5.3-flash.md
[switching]: https://docs.z.ai/devpack/latest-model.md
[plan-overview]: https://docs.z.ai/devpack/overview.md
[plan-notice]: https://docs.z.ai/devpack/notice/usage-revision.md
[campaign]: https://docs.z.ai/devpack/notice/event-glm-5.3-flash.md
[claude-current]: https://docs.z.ai/devpack/tool/claude.md
[claude-old]: https://docs.z.ai/scenario-example/develop-tools/claude.md
[zcode]: https://github.com/zai-org/ZCode/tree/29628c9acdb81b703bbd4080c207a0e7ce5e276e
[zcode-changelog]: https://zcode.z.ai/en/changelog
[aa-api]: https://artificialanalysis.ai/data-api/docs
[router-source]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/src/commit/6c337a400b4cdc28ded543d2ae8ccf3749d79cb7
[router-identity]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/179
[router-economics]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/184
[router-mi]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/176
