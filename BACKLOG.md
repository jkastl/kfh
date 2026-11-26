# Backlog

Durable record of planned work, so any session can pick it up. Update it as items land.
Conventions live in `CLAUDE.md`; known gaps in `TECH_DEBT.md`; how to turn book pages into
people data in `docs/EXTRACTION.md`.

## Status (2026-11-26)

- Done: scans, page images, verified transcriptions of all 76 scans (`content/pages/`).
- Done: first end-to-end slice — the father-to-son line Andreas Kastl → Matthew Richard Kastl
  with immediate families (55 people), person pages, book reader, search.
- Done: steps 1–5 below (refocus on the brothers, per-branch data files, tree, table, PDF links).
- Next: step 6, building out the branches, when the owner gives the go-ahead.

## Next, in order

### 1. Refocus the site on the seven brothers (owner request) — DONE
- Home page: the family's story and the **seven brothers** (Peter, Wenzel, John, Josef, Jacob,
  Thomas, Andrew) plus half-sister Anna Kastl Zima as the entry points — one card per branch with
  arrival, where they settled, and a link to the branch's tree/people and chapter.
- The ancestors above them (Andreas → Wolfgang Jan → Jan → Thomas) as a short shared-roots strip.
- Remove "the line of Matthew Richard Kastl" framing from home, person-page kickers and About.
  Person pages should say how someone connects (e.g. "Grandson of Josef Kastl · Josef's branch").
- Keep the generational "line" view only as a generic feature (e.g. "show line to the brothers"
  from any person), not a featured individual.

### 2. Split people data per branch (prerequisite for parallel build-out) — DONE
- Move `content/people.json` → `content/people/_roots.json` (Andreas … Thomas & wives, the
  brothers and half-siblings) + one file per branch: `peter.json`, `wenzel.json`, `john.json`,
  `josef.json`, `jacob.json`, `thomas.json`, `andrew.json`, `zima.json`.
- `tools/build.py` merges all files, rejects duplicate ids, and cross-file references must resolve.
- Each person gets `branch`. Generation number computed from the brothers (brother = gen 1).

### 3. Tree diagram (owner request) — DONE
- Interactive descendant tree per branch (and whole family): SVG, pan/zoom, collapse/expand,
  click a person → their page. Vanilla JS, no CDN dependency needed; data from a generated JSON.
- Must stay usable on a phone (start collapsed to 2–3 generations; search-to-focus).

### 4. Table view (owner request) — DONE
- One page listing everyone: name, born, died, places, spouse(s), parents, branch, generation,
  source pages. Client-side filter (text, branch, has-conflict), sortable columns, CSV download.
- Dates are free text as printed; derive a sortable year field at build time (first 4-digit
  year), keep the printed value for display.

### 5. PDF links open in a new tab — DONE
- Footer and book-index PDF links: `target="_blank" rel="noopener"`, labelled with size
  ("PDF, 28 MB") so the download/new tab isn't a surprise.

### 6. Build out the rest of the tree — work units
Each unit is self-contained: an agent or a fresh session takes the unit, follows
`docs/EXTRACTION.md`, writes only its own `content/people/<branch>.json`, runs the build (which
must pass the quote check), and commits. Supplement pages hold corrections for every branch —
each unit must also read the supplement sections that name its pages.

| Unit | Branch | Book pages (scans) | Supplement sections (scan) | Size (family groups / child entries) |
|---|---|---|---|---|
| U1 | Josef — finish siblings' descendants | 41–43 (s043–s045) | p.41, p.42 ×2 (s073–s075); p.47 is Jacob | 10 / 39 + most of supp. pp.5–8 |
| U2 | Peter | 15–25 (s017–s027) | p.20, p.21, p.22 ×2 (s071–s072) | 36 / 122 |
| U3 | Wenzel + Thomas + Anna Kastl Zima | 26–27, 56, 62 (s028–s029, s058, s064) | p.26, p.27 (s072) | 15 / 65 |
| U4a | John, first part | 28–33 (s030–s035) | p.31 (s073) | split at a sub-family boundary |
| U4b | John, second part | 34–40 (s036–s042) | pp.34–35 (s076) | (John total 80 / 244) |
| U5a | Jacob, first part | 44–49 (s046–s051) | p.47 (s076) | split at a sub-family boundary |
| U5b | Jacob, second part | 50–55 (s052–s057) | p.54 (s076) | (Jacob total 72 / 229) |
| U6 | Andrew | 57–61 (s059–s063) | p.60 (s076) | 35 / 120 |
| U7 | Integration | all | all | cross-branch marriages, duplicate people, unresolved supplement entries, final counts |

Notes for the split units: pick the boundary where one child-of-the-brother's sub-family ends
(check the lineage parentheses), and record the exact boundary here before starting.
Run U4a/U4b and U5a/U5b one after another or give them disjoint id prefixes, so ids don't clash.

### 7. Verification debt (see TECH_DEBT.md)
- Re-proofread s028–s036 against the images (the second pass there was not thorough). Do this
  before or as part of U3/U4a.
- Re-check numbers on s071 (supplement p.3) by eye during U2.

## Later / ideas
- Tree: optional top-down layout; show in-marrying spouses as their own boxes; print/export.
- Table: a places column; filter by place and by decade.
- Places index (Všepadly, Hradiště, Stara Hut, Plasi, Weston, Brainard, Omaha…) and a map,
  including the book's own maps (p.6 Pilsen sheet, p.11 homestead map).
- Timeline: emigration (1866–1872), homesteads, deaths.
- Per-branch reading guide: chapter narrative + photos.
- Link narrative mentions in transcriptions to person pages where unambiguous.

## Open questions for the owner
- Search indexing: currently indexable (no `noindex`). Keep, or hide from search engines?
- Pages source is assumed to be `main` / root. Confirm.
