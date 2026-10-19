"""Turn a dork template plus a target host into a concrete search query.

Templates use {target} where the host belongs, e.g.
    site:{target} intitle:"index of" "backup"
    site:{target} ext:sql
If a template has no {target} placeholder and no site: operator, a
`site:<host>` prefix is added so every generated query stays scoped to the
target. The builder never emits a query without a host constraint.
"""

from __future__ import annotations

import re

from .scope import normalize_host

_SITE_RE = re.compile(r"\bsite:", re.IGNORECASE)


class ScopeError(ValueError):
    pass


def build_query(target_host: str, template: str) -> str:
    host = normalize_host(target_host)
    tmpl = template.strip()

    if "{target}" in tmpl:
        query = tmpl.replace("{target}", host)
    elif _SITE_RE.search(tmpl):
        # Template already constrains a site; make sure it is this host.
        query = tmpl
    else:
        query = f"site:{host} {tmpl}"

    if host not in query:
        raise ScopeError(
            f"Built query does not reference target host '{host}': {query!r}"
        )
    return query.strip()
