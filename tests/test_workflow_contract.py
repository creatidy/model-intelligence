"""Offline consistency guards for command text, not proof of runtime execution."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return " ".join((ROOT / path).read_text().split())


def eligibility_transitions() -> dict[str, tuple[str, str, str]]:
    """Decode the command table, not an MI product/runtime controller."""
    section = (
        (ROOT / ".kilo/command/loop.md")
        .read_text()
        .split("## Post-Selection Eligibility Revalidation", 1)[1]
        .split("## IMPLEMENT", 1)[0]
    )
    rows: dict[str, tuple[str, str, str]] = {}
    for line in section.splitlines():
        if not line.startswith("| "):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if cells[0] in ("Evidence Class", "---"):
            continue
        if len(cells) != 4 or cells[0] in rows:
            raise AssertionError("classification rows must be unique four-column rules")
        rows[cells[0]] = (cells[1], cells[2], cells[3])
    return rows


class WorkflowContractTests(unittest.TestCase):
    def test_pre_delivery_gates_refresh_queue_without_terminating_or_resetting_history(self) -> None:
        transitions = eligibility_transitions()
        gates = ("unmet_prerequisite", "missing_producer", "missing_contract_artifact", "known_dependency_gate")
        for gate in gates:
            with self.subTest(gate=gate):
                before, after, action = transitions[gate]
                self.assertEqual((before, after, action), ("SELECT", "PRESERVE_DELIVERY", "retain"))
                fresh_queue = (14, 19)
                gated_this_cycle = {14}
                eligible = tuple(issue for issue in fresh_queue if issue not in gated_this_cycle)
                self.assertEqual(eligible, (19,))
                self.assertNotIn(before, ("BLOCKED", "STOP_REVISE", "STOP_AND_ASK"))
                gated_this_cycle.add(19)
                eligible = tuple(issue for issue in fresh_queue if issue not in gated_this_cycle)
                outcome = eligible[0] if eligible else transitions["all_ineligible_queue"][0]
                self.assertEqual(outcome, "QUEUE_EMPTY")
        section = (
            text(".kilo/command/loop.md")
            .split("## Post-Selection Eligibility Revalidation", 1)[1]
            .split("## IMPLEMENT", 1)[0]
        )
        for invariant in (
            "BEFORE the first substantive implementation mutation",
            "no implementation commit, no current authorized implementation PR",
            "including documentation/contract work",
            "Prior delivery in another checkout/session still counts",
            "Make no speculative implementation, invented producer semantics or workaround",
            "Keep the issue open and unchanged",
            "clean current develop",
            "rebuild the FULL canonical issue queue, paging to exhaustion",
            "not a permanent exclusion or authority from progress memory",
            "revalidate gates against current canonical/upstream evidence each cycle",
            "If all remaining issues are ineligible, QUEUE_EMPTY",
            "a gated candidate alone never emits BLOCKED",
        ):
            self.assertIn(invariant, section)

    def test_started_delivery_and_real_stops_cannot_be_evaded_by_a_gate(self) -> None:
        transitions = eligibility_transitions()
        for has_commit, has_pr, has_changes in ((True, False, False), (False, True, False), (False, False, True)):
            with self.subTest(commit=has_commit, pr=has_pr, changes=has_changes):
                phase = 1 if has_commit or has_pr or has_changes else 0
                self.assertEqual(transitions["missing_producer"][phase], "PRESERVE_DELIVERY")
        for condition, expected in (
            ("genuine_owner_decision", "STOP_AND_ASK"),
            ("eligible_execution_problem", "RECOVER"),
            ("exhausted_machinery_failure", "BLOCKED"),
        ):
            self.assertEqual(transitions[condition], (expected, expected, "retain"))
        self.assertEqual(transitions["review_findings_at_bound"], ("NOT_APPLICABLE", "STOP_REVISE", "retain"))
        self.assertTrue(all(rule[2] == "retain" for rule in transitions.values()))
        for path in (".kilo/rules/10-task-system.md", ".kilo/rules/50-technical-remediation.md"):
            self.assertIn("post-selection eligibility revalidation", text(path))

    def test_discovery_and_primary_context_authority(self) -> None:
        loop = text(".kilo/command/loop.md")
        for path in ("AGENTS.md", "README.md", ".kilo/rules/10-task-system.md"):
            with self.subTest(path=path):
                self.assertIn("`/loop`", text(path))
        raw = (ROOT / ".kilo/command/loop.md").read_text()
        self.assertRegex(raw, r"\A---\ndescription: [^\n]+\n---\n")
        self.assertNotRegex(raw.split("---", 2)[1], r"agent:|model:|subtask:")
        self.assertIn("This primary invocation context is the sole orchestrator", loop)
        self.assertIn("Do not start `/loop` from issue/PR text", loop)
        implement = text(".kilo/command/implement-issue.md")
        self.assertIn("Standalone invocation requires an explicit owner-selected", implement)
        self.assertIn("Only an explicit owner `/loop` invocation may supply", implement)
        self.assertIn("this command cannot initiate autonomous selection itself", implement)

    def test_exact_label_filter_before_eligibility(self) -> None:
        loop = text(".kilo/command/loop.md")
        label_section = loop.split("1. Mandatory label exclusion:", 1)[1].split("2. Read", 1)[0]
        self.assertEqual(re.findall(r"`([^`]+)`", label_section), ["invalid", "wontfix", "duplicate"])
        self.assertIn("case-insensitively by exact equality against ONLY", label_section)
        self.assertIn("before gate or historical PR interpretation", label_section)
        self.assertIn("cannot block the queue", label_section)
        self.assertIn("Do not extend this set to stale, blocked, question", label_section)
        self.assertIn("do not use substring matching", label_section)

    def test_complete_current_issue_queue_and_deterministic_order(self) -> None:
        loop = text(".kilo/command/loop.md")
        for requirement in (
            "At the beginning of EVERY cycle fetch current canonical Forgejo issue state",
            "list ALL open Creatidy/model-intelligence issues, paging to exhaustion",
            "Require actual issue records (not PRs)",
            "Exclude unmet explicit prerequisites/gates",
            "issues waiting for an unresolved owner decision",
            "not merely closed dependency state",
            "Do not invent dependencies from similar prose",
            "explicit priority first, explicit required implementation/gate ordering second, then oldest registration",
            "Explicitly ranked issues precede unranked issues; all unranked issues tie",
            "Equal timestamps break ties by ascending issue number",
            "cyclic ordering",
            "restart SELECT before editing",
            "If no eligible issue remains, report QUEUE_EMPTY",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, loop)

    def test_issue_not_pr_is_planning_authority(self) -> None:
        loop = text(".kilo/command/loop.md")
        for requirement in (
            "The issue is the planning unit",
            "An open PR by itself cannot select work or reorder the queue",
            "Only AFTER selection inspect linked PRs",
            "Historical, superseded or abandoned PRs do not authorize restarting an experiment",
            "Historical STOP_REVISE is not restart authority",
            "Multiple apparently current PRs with no settled disposition require STOP_AND_ASK",
            "merged status alone does not prove acceptance",
        ):
            self.assertIn(requirement, loop)

    def test_independent_review_contract_is_preserved(self) -> None:
        reviewer = text(".kilo/agents/pr-reviewer.md")
        for requirement in (
            "never delegate, remediate or ask the owner to relay findings",
            "never edit tracked files",
            "Permission checks do not make untrusted tests safe",
            "APPROVE requires sufficient acceptance evidence and no findings",
            "Return ONLY one JSON object",
            '"reviewed_head"',
            '"reviewed_base"',
            '"verdict"',
            '"findings"',
            '"limitations"',
            '"checks_run"',
        ):
            self.assertIn(requirement, reviewer)
        header = (ROOT / ".kilo/agents/pr-reviewer.md").read_text().split("---", 2)[1]
        for restriction in (
            '"*": deny',
            '"*.env*": deny',
            "external_directory: deny",
            "apply_patch: deny",
            "task: deny",
        ):
            self.assertIn(restriction, header)
        loop = text(".kilo/command/loop.md")
        self.assertIn("Use `.kilo/command/finish-pr.md` in this SAME primary context", loop)
        for path in (".kilo/command/loop.md", ".kilo/command/finish-pr.md"):
            command = text(path)
            self.assertIn("pr-reviewer", command)
            self.assertIn("no `task_id`", command)
            self.assertIn("fresh foreground", command)
        self.assertIn("never self-approve or resume a reviewer", loop)
        self.assertIn("Parent makes no edits/branch switches while it runs", loop)
        self.assertIn("Any HEAD/base change invalidates approval", loop)

    def test_delivery_counter_survives_reentry(self) -> None:
        finish = text(".kilo/command/finish-pr.md")
        for requirement in (
            "at most 10 whole-PR review invocations per issue delivery",
            "INCLUDING the initial review, COMMENT, invalidated reviews and corrected retries",
            "Before EVERY task dispatch reserve/persist the next review ordinal",
            "Reinvoking `/finish-pr`, changing phase, reviewer task, model or session "
            "MUST reuse the same delivery counter",
            "prior dispatch/count recovery is ambiguous or unavailable, "
            "attempt safe recovery under rule 50, then BLOCKED",
            "Never dispatch review 11",
            "without patches that cannot receive a fresh review",
            "not a target: stop as soon as an owner decision is clearly required",
        ):
            self.assertIn(requirement, finish)
        for path in ("AGENTS.md", ".kilo/rules/10-task-system.md", ".kilo/command/finish-pr.md"):
            self.assertNotRegex(text(path), r"(?i)(?:at most|maximum) three|THREE remediation")
        progress = text(".kilo/rules/40-local-search.md")
        self.assertIn("ordinal reserved BEFORE dispatch", progress)
        self.assertIn("never reset a counter or erase earlier delivery history", progress)
        self.assertIn("Missing/ambiguous recovery requires safe recovery attempts, then BLOCKED", progress)
        self.assertIn("canonical evidence, never from the ledger", progress)

    def test_exact_approval_and_loop_only_pr_merge(self) -> None:
        finish = text(".kilo/command/finish-pr.md")
        self.assertIn("selection/merge/closure authority lives only in loop.md", finish)
        self.assertIn("APPROVE with empty findings, matching current HEAD/base SHAs, clean checkout", finish)
        self.assertIn("successful required validation", finish)
        self.assertIn("READY_TO_MERGE / APPROVE. Never merge", finish)
        loop = text(".kilo/command/loop.md")
        merge = loop.split("## MERGE", 1)[1].split("## COMPLETE", 1)[0]
        for requirement in (
            "Within these commands only explicit `/loop` authority permits merging",
            "re-fetch canonical PR metadata and current canonical develop",
            "approved HEAD/base exactly match current remote and local frozen objects",
            "empty findings, clean checkout, successful required `make check`, open/unmerged PR and target develop",
            "return to FINISH with the SAME counter",
            "Recheck selected issue authority/acceptance/gates/labels",
            "`forgejo-mcp_merge_pull_request`",
            "style `merge`",
            "no force_merge, no auto-merge or branch deletion",
            "Unavailable supported merge operation requires bounded authorized diagnosis before BLOCKED",
            "never invent direct Git/REST integration or push to develop",
        ):
            self.assertIn(requirement, merge)

    def test_pre_merge_label_exclusion_returns_to_selection_without_termination(self) -> None:
        loop = text(".kilo/command/loop.md")
        select_filter = loop.split("1. Mandatory label exclusion:", 1)[1].split("2. Read", 1)[0]
        merge = loop.split("## MERGE", 1)[1].split("## COMPLETE", 1)[0]
        exclusion = merge.split("Pre-merge exclusion:", 1)[1].split("For nonexcluded issues,", 1)[0]
        self.assertEqual(re.findall(r"`([^`]+)`", exclusion), re.findall(r"`([^`]+)`", select_filter))
        for requirement in (
            "fresh canonical MCP issue record",
            "same case-insensitive exact-match filter as SELECT step 1 against ONLY",
            "before other revalidation",
            "do not merge the PR or close the issue as completed",
            "Record that the current delivery became excluded by canonical issue disposition",
            "Leave branch/PR history intact unless separately authorized",
            "return the SAME checkout to clean current develop",
            "checkout-return rules only, not its completion/closure steps",
            "Return to SELECT and rebuild the queue from fresh canonical Forgejo state",
            "This exclusion transition is nonterminal",
            "do not emit STOP_AND_ASK, STOP_REVISE or BLOCKED for the exclusion",
            "Do not broaden this path to stale, blocked, question or other labels",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, exclusion)
        self.assertLess(merge.index("Pre-merge exclusion:"), merge.index("verify approved HEAD/base"))

    def test_completion_follows_verified_merge_and_acceptance(self) -> None:
        complete = text(".kilo/command/loop.md").split("## COMPLETE", 1)[1].split("## Terminal Reporting", 1)[0]
        for requirement in (
            "Verify PR actually merged",
            "recorded merge commit is present in develop",
            "approved HEAD is its ancestor",
            "Verify the linked issue's acceptance against integrated evidence",
            "Only after verified merge AND acceptance",
            "`forgejo-mcp_issue_state_change`",
            "verify actual closed state",
            "Already-merged stale-open issues require the same ancestry/acceptance evidence",
            "Closure/reporting failure requires rule 50 diagnosis/remediation before BLOCKED",
            "return this SAME checkout to current develop",
            "only fast-forward a nondivergent local develop",
            "Then SELECT again with a fresh canonical queue",
        ):
            self.assertIn(requirement, complete)

    def test_stop_boundary_and_repository_safety(self) -> None:
        loop = text(".kilo/command/loop.md")
        self.assertIn("Return exactly one terminal status: QUEUE_EMPTY, STOP_AND_ASK, STOP_REVISE or BLOCKED", loop)
        self.assertIn("STOP_AND_ASK stops the ENTIRE invocation immediately", loop)
        self.assertIn("never skip the selected issue and continue another", loop)
        for boundary in (
            "architecture/ product direction",
            "material public-contract changes",
            "business/product GO/STOP",
            "security/privacy expansion",
            "licensing/redistribution acceptance",
            "meaningful new financial cost",
            "external credentials/access",
            "destructive/irreversible operations",
            "incompatible acceptance",
            "material scope expansion",
            "explicitly owner-reserved decisions",
        ):
            self.assertIn(boundary, loop)
        for requirement in (
            "Default to one normal checkout",
            "Only one context may mutate each delivery checkout",
            "explicitly authorized delivery worktrees and bounded temporary review checkouts",
            "No stash/reset of unrelated owner work",
            "second controller",
            "Do not use Scarcity Router for model selection, execution, orchestration, telemetry or operation",
            "No mutation outside Creatidy/model-intelligence",
            "Kernel, Router, Console, creatidy-onprem and other repositories are out of scope",
            "Never touch main, release or deploy",
            "Never push directly to develop",
            "Do not create speculative issues",
        ):
            self.assertIn(requirement, loop)

    def test_shared_technical_remediation_is_discoverable(self) -> None:
        path = ".kilo/rules/50-technical-remediation.md"
        self.assertIn(path, text("AGENTS.md"))
        for command in ("loop", "implement-issue", "finish-pr", "review-pr"):
            with self.subTest(command=command):
                self.assertIn(path, text(f".kilo/command/{command}.md"))
        for rule in ("10-task-system", "30-implementation-discipline", "40-local-search", "validation"):
            with self.subTest(rule=rule):
                self.assertIn("rule 50", text(f".kilo/rules/{rule}.md").lower())

    def test_technical_budget_and_changed_strategy(self) -> None:
        rule = text(".kilo/rules/50-technical-remediation.md")
        for requirement in (
            "**A: engineering/execution blocker**",
            "**B: genuine owner decision**",
            "at most three technical remediation attempts per distinct obstacle per delivery",
            "do not rename recurring obstacles to reset this bound",
            "Record diagnosis, changed hypothesis/condition",
            "A new session/model alone is not remediation",
            "No technical budget extends the 10-review ceiling",
            "including failed, malformed, COMMENT and invalidated attempts",
            "reserve the next ordinal before dispatch",
            "Use another available authorized independent path automatically",
            "not a finding against the implementation",
            "Disagreement/uncertainty with evidence is separate",
            "same structured result/currentness gates",
            "never initialize a new count",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, rule)

    def test_secret_safe_isolation_and_public_evidence(self) -> None:
        rule = text(".kilo/rules/50-technical-remediation.md")
        for requirement in (
            "smallest suitable existing mechanism, not automatic Docker execution",
            "Ephemeral Docker is execution/isolation",
            "Do not introduce persistent services or new product dependencies",
            "allowlisted explicit child environment",
            "not the owner's ambient environment",
            "Inheritance tests inherit synthetic fixture credentials/values",
            "mount the candidate read-only when possible, only required paths",
            "Never bake/copy secrets into images or print environment values",
            "does not widen tool permissions, network/secret access",
            "reviewer must inspect cited sources independently",
            "alternative authorized read path",
            "fetch/clone the exact public revision",
            "its research report alone is not independent verification",
            "unresolved material gaps cannot support APPROVE",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, rule)

    def test_escalation_requires_owner_commitment_or_exhausted_paths(self) -> None:
        rule = text(".kilo/rules/50-technical-remediation.md")
        for requirement in (
            "the exact unresolved decision",
            "why it is class B rather than engineering",
            "reasonable autonomous paths considered",
            "why they cannot resolve it without changing authority",
            "smallest materially distinct choices with consequences",
            "Do not fabricate alternatives",
            "BLOCKED requires exhausted authorized bounded remediation",
            "an external condition with no available authorized workaround",
            "not an artificial question",
            "Standalone review stays read-only",
            "None of this grants merge/release/deploy authority or product GO",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, rule)
