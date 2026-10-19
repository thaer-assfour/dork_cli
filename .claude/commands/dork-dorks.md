---
description: Develop and expand the dork library, optionally tailored to a target's stack.
argument-hint: [target-domain or topic to focus on]
allowed-tools: Bash(uv run dork *), Bash(sqlite3 -readonly *)
---

Help me develop the dork library. Focus (optional): `$ARGUMENTS`.

1. Show the current library: `uv run dork dorks list`.
2. If a target domain was given, look at what recent scans revealed about its
   stack (titles, security.txt, categories that hit) to propose sharper dorks.
   Read the database read-only for this.
3. Propose 5-10 new dork templates. Each must use `{target}` for the host, have
   a category (exposure, panels, secrets, config, errors, files, vcs, cloud)
   and a risk (low|medium|high|critical). Explain what each is meant to surface.
4. After I approve, add the good ones:
   `uv run dork dorks add '<template>' --category <cat> --risk <risk>`.

Keep templates scoped: they should constrain to the target host via `{target}`
or a `site:` operator. Do not propose dorks that target hosts outside an
authorized program.
