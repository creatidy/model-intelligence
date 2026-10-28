"""Bounded public inputs for the selected source slice, never an arbitrary crawler."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime
from http.client import HTTPException, IncompleteRead
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from model_intelligence.evidence import instant

TERMINAL_BENCH_SUBMISSIONS_PREFIX = (
    "/harbor-framework/terminal-bench/6964e9252c90227fc1cfa26cbc59aee4134792e4/leaderboard/submissions/"
)


@dataclass(frozen=True)
class Source:
    source_id: str
    reference: str
    max_bytes: int
    license: str

    def __post_init__(self) -> None:
        parsed = urlsplit(self.reference)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in {"raw.githubusercontent.com", "docs.z.ai"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in {None, 443}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("unexpected-source-origin")
        if parsed.hostname == "raw.githubusercontent.com" and not any(
            parsed.path.startswith(prefix) for prefix in ("/anomalyco/models.dev/", TERMINAL_BENCH_SUBMISSIONS_PREFIX)
        ):
            raise ValueError("unexpected-source-path")
        if (
            not self.source_id.strip()
            or not self.license.strip()
            or type(self.max_bytes) is not int
            or self.max_bytes < 1
        ):
            raise ValueError("invalid-source-policy")


@dataclass(frozen=True)
class Capture:
    source: Source
    data: bytes
    acquired_at: datetime
    http_status: int = 200

    def __post_init__(self) -> None:
        if type(self.http_status) is not int or self.http_status != 200:
            raise ValueError("source-http-status")
        object.__setattr__(self, "acquired_at", instant(self.acquired_at))
        if not self.data or len(self.data) > self.source.max_bytes:
            raise ValueError("source-size-policy")
        try:
            _ = self.data.decode("utf-8", errors="strict")
        except UnicodeError as error:
            raise ValueError("source-encoding") from error

    @property
    def revision(self) -> str:
        return "content-sha256:" + hashlib.sha256(self.data).hexdigest()


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: object, fp: object, code: int, msg: str, headers: object, newurl: str
    ) -> Request | None:
        raise ValueError("source-redirect-rejected")


def fetch(source: Source, *, at: datetime, timeout: float) -> Capture:
    if type(timeout) is bool or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("invalid-source-timeout")
    request = Request(
        source.reference, headers={"Accept-Encoding": "identity", "User-Agent": "model-intelligence-evidence"}
    )
    try:
        with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=timeout) as response:
            if response.status != 200 or response.geturl() != source.reference:
                raise ValueError("source-partial-or-unexpected-response")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ValueError("source-compressed-response")
            data = response.read(source.max_bytes + 1)
            length = response.headers.get("Content-Length")
            declared_length: int | None = None
            if length is not None:
                if not length.isdecimal():
                    raise ValueError("source-incomplete-response")
                try:
                    declared_length = int(length)
                except ValueError:
                    raise ValueError("source-incomplete-response") from None
                if declared_length < len(data):
                    raise ValueError("source-incomplete-response")
                if len(data) <= source.max_bytes and declared_length != len(data):
                    raise ValueError("source-incomplete-response")
            if len(data) > source.max_bytes:
                raise ValueError("source-size-policy")
            return Capture(source, data, at, response.status)
    except IncompleteRead:
        raise ValueError("source-incomplete-response") from None
    except HTTPException:
        raise ValueError("source-http-protocol-failed") from None
    except (HTTPError, URLError, TimeoutError, UnicodeError, OSError) as error:
        # Only a diagnostic class escapes; never echo response bodies or headers.
        raise ValueError("source-retrieval-failed") from error
