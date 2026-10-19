"""Scope guard: only ever query hosts you are authorized to test.

A target's scope is a list of host patterns (exact hosts or wildcards like
"*.example.com"). A target with an empty scope is treated as "self only":
its own apex domain and subdomains are allowed, nothing else. This keeps
every generated query inside an authorized program.
"""

from __future__ import annotations

import fnmatch


def normalize_host(host: str) -> str:
    host = host.strip().lower()
    host = host.replace("https://", "").replace("http://", "")
    host = host.split("/")[0]
    if host.startswith("*."):
        return host
    return host


def default_scope(domain: str) -> list[str]:
    d = normalize_host(domain)
    return [d, f"*.{d}"]


def is_in_scope(host: str, scope: list[str]) -> bool:
    host = normalize_host(host)
    if not scope:
        return False
    for pattern in scope:
        pattern = normalize_host(pattern)
        if host == pattern:
            return True
        if fnmatch.fnmatch(host, pattern):
            return True
    return False


def effective_scope(domain: str, scope: list[str]) -> list[str]:
    """Scope to enforce for a target: its declared scope, or self-only."""
    return scope if scope else default_scope(domain)
