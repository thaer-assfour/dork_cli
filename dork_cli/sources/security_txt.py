"""security.txt discovery (RFC 9116).

Given a domain, fetch /.well-known/security.txt (then /security.txt as a
fallback) and, if found, record the domain as a target with the raw policy
text and any Policy: URL. The presence of security.txt is a strong signal the
operator accepts vulnerability reports.
"""

from __future__ import annotations

import httpx

from ..db.models import Target
from .base import TargetSource
from ..core.scope import normalize_host

PATHS = ["/.well-known/security.txt", "/security.txt"]
USER_AGENT = "dork-cli/0.1 (+security-research)"


def _parse_field(text: str, field: str) -> str | None:
    prefix = field.lower() + ":"
    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


class SecurityTxtSource(TargetSource):
    name = "security_txt"

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def discover(self, seed: str) -> list[Target]:
        host = normalize_host(seed)
        if not host:
            return []
        for scheme in ("https", "http"):
            for path in PATHS:
                url = f"{scheme}://{host}{path}"
                try:
                    resp = httpx.get(
                        url, timeout=self.timeout, follow_redirects=True,
                        headers={"User-Agent": USER_AGENT},
                    )
                except httpx.HTTPError:
                    continue
                ctype = resp.headers.get("content-type", "")
                if resp.status_code == 200 and "text" in ctype:
                    text = resp.text
                    if "contact" not in text.lower():
                        continue
                    return [
                        Target(
                            domain=host,
                            name=host,
                            source=self.name,
                            program_url=_parse_field(text, "Policy"),
                            security_txt=text[:8000],
                        )
                    ]
        return []
