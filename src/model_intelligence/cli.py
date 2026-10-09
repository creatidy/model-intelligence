"""Local read-only operator views; never fetches, publishes or delegates commands."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import cast

from model_intelligence.operator import canonical, snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mi-evidence", description="Offline read-only MI operator snapshots")
    parser.add_argument("operation", choices=("status", "inspect", "export"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--instance", required=True)
    parser.add_argument("--at", required=True, help="Explicit aware ISO evaluation time, not an acquisition cutoff")
    parser.add_argument("--max-bytes", type=int, required=True, help="Operator input-byte policy, not a global limit")
    parser.add_argument("--checkpoint", help="Previous retained cut digest; not an event offset")
    parser.add_argument("--json", action="store_true", help="Exact canonical full snapshot for every operation")
    args = parser.parse_args(argv)
    try:
        directory = cast(Path, args.directory)
        view = snapshot(
            directory,
            instance=cast(str, args.instance),
            at=datetime.fromisoformat(cast(str, args.at)),
            max_bytes=cast(int, args.max_bytes),
            checkpoint=cast(str | None, args.checkpoint),
        )
    except (ValueError, OSError, UnicodeError):
        print("operator-input-or-read-policy-rejected", file=sys.stderr)
        return 2
    if args.operation == "export" or args.json:
        print(canonical(view).decode())
    else:
        publication = cast(dict[str, object], view["publication"])
        health = cast(dict[str, object], view["health"])
        facts = cast(dict[str, object], view["facts"])
        history = cast(dict[str, object], view["history"])
        print(f"MI instance: {view['instance']}")
        print(f"Publication: {publication['state']}")
        print(f"Health: {health['state']} / correlation: {health['correlation']}")
        for key in ("latest", "future", "stale", "unknown_freshness", "notices", "uncertain_campaigns", "conflicts"):
            print(f"{key}: {len(cast(list[object], facts[key]))}")
        print(f"History: {history['relation']} (retained cuts only; no replay)")
        print("Effectful commands: none")
        if publication["state"] in {"invalid", "unsupported"}:
            print("Inspect retained digest/version/size policy before retry; no artifact was changed.")
        if health["correlation"] == "mismatch":
            print("Health and publication are separate observations; re-read after producer publication completes.")
        if health["state"] == "valid":
            data = cast(dict[str, object], health["data"])
            if data["succeeded"] is False:
                print("Last source refresh failed; publication is retained, not a freshness guarantee.")
                print("Inspect named-source diagnostic classes in --json output; only the producer may refresh.")
        if history["relation"] in {"gap", "unavailable"}:
            print("Requested history is unavailable; use a validated full-snapshot resync, not invented replay.")
        if args.operation == "inspect":
            print(canonical(facts["projection"]).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
