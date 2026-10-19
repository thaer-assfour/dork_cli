"""disclose.io program list: self-hosted / independent VDPs and bug bounties.

Pulls the community-maintained program-list.json and filters it by the seed
(matched against program name, policy URL, and contact). This favours
self-hosted programs, i.e. ones that run their own disclosure policy rather
than living only on a platform.
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from ..db.models import Target
from .base import TargetSource

PROGRAM_LIST_URL = (
    "https://raw.githubusercontent.com/disclose/diodb/master/program-list.json"
)


def _domain_from_url(url: str) -> str | None:
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url
    host = urlparse(url).netloc.lower()
    return host or None


class DiscloseIoSource(TargetSource):
    name = "discloseio"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def _fetch(self) -> list[dict]:
        resp = httpx.get(PROGRAM_LIST_URL, timeout=self.timeout,
                         follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("programs", [])

    def discover(self, seed: str) -> list[Target]:
        seed = seed.strip().lower()
        programs = self._fetch()
        out: list[Target] = []
        for p in programs:
            name = (p.get("program_name") or "").strip()
            policy = p.get("policy_url") or ""
            contact = p.get("contact_url") or p.get("contact_email") or ""
            hay = " ".join([name, policy, contact]).lower()
            if seed and seed not in hay:
                continue
            domain = _domain_from_url(policy) or _domain_from_url(contact)
            if not domain:
                continue
            out.append(
                Target(
                    domain=domain,
                    name=name or None,
                    source=self.name,
                    program_url=policy or None,
                )
            )
        return out
