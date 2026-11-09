# Schema mapping (pending raw-data inspection)

The TSE catalogue resource labels do **not** establish actual CSV column names. Do not fabricate a mapping prior to reading real archive members and headers.

## Target canonical keys

`year, election, round, office, uf, municipality_code_original, municipality_code_normalised, municipality_name, electoral_zone, section, candidate_or_vote_category`.

## Required quantities

- Round 1: each presidential candidate count, both eventual finalists, blank and null categories, total turnout, electorate.
- Round 2: W/L (symmetrically assigned), blank and null counts; independently specified turnout and electorate.
- Section continuity: missing/created/merged sections, changes in identifiers, optional polling-place ID **only when official data support it**.

## Mapping procedure

1. Run `src/inspect_archives.py` to enumerate archive members, infer safe decoding, delimiter and exact CSV headers.
2. Determine official vote category codes and office codes from official documentation and observed rows.
3. Explicitly map official columns to canonical names in a versioned mapping file, including ambiguous cases.
4. Validate exact count conservation and reconciled municipality/UF totals *before* creating training data.
5. Record SHA-256 of every input and version the extraction script.

**No field mapping, row count or join match is presently certified.**
