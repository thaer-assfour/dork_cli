# Credits & data sources

The dork library in `data/` is partly derived from community dork collections.
The `data/curated_dorks.yaml` file was produced by a one-time extraction that
selected high-signal entries, normalized them to `{target}` templates, and
mapped them onto this project's categories and risk levels.

## Sources

- **Proviesec/google-dorks** — https://github.com/Proviesec/google-dorks
  Dork lists licensed **CC-BY-4.0**. Attribution is required: portions of
  `data/curated_dorks.yaml` tagged `src:proviesec` are adapted from this
  project. Each adapted entry was reformatted into our schema.

- **tc4dy/GoogleDorkArchive** — https://github.com/tc4dy/GoogleDorkArchive
  Licensed **MIT**. Entries tagged `src:tc4dy` are adapted from this project;
  their descriptions are preserved in the `tags` field.

- **Exploit-DB Google Hacking Database (GHDB)** —
  https://www.exploit-db.com/google-hacking-database
  Imported at runtime via `dork dorks ghdb` (not redistributed in this repo).

## Note

These lists are search-query templates only. Running them against a host is
governed by this project's scope guard and must stay within an authorized bug
bounty program.
