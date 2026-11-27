# Backlog

Durable record of planned work, so any session can pick it up. Update it as items land.
Conventions live in `CLAUDE.md`; known gaps in `TECH_DEBT.md`; how to turn book pages into
people data in `docs/EXTRACTION.md`.

## Status (2026-11-26)

- Done: scans, page images, verified transcriptions of all 76 scans (`content/pages/`).
- Done: first end-to-end slice — the father-to-son line Andreas Kastl → Matthew Richard Kastl
  with immediate families (55 people), person pages, book reader, search.
- Done: steps 1–5 below (refocus on the brothers, per-branch data files, tree, table, PDF links).
- Done: step 8a/8b (build checks). Step 6: U1 (Josef), U2 (Peter), U3 (Wenzel, Thomas, Zima), U6 (Andrew), U4a+U4b (John), U5a+U5b (Jacob) and U7 (integration) done. Step 6 is complete. Steps 6 and 8 (targeted) done. Next: the owner's future-session list (F1–F5) below.

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
| U1 | Josef — DONE (2026-11-26): 147 people, 39 families; all 40 printed headings checked | 41–43 (s043–s045) | p.41, p.42 ×2 (s073–s076 top) | was 10 / 39 + supp. pp.5–8 (actually ~35 family groups) |
| U2 | Peter — DONE (2026-11-26): 205 people, 49 families; 54 headings checked | 15–25 (s017–s027) | p.20, p.21, p.22 ×2 (s071–s072) | 36 / 122 |
| U3 | Wenzel + Thomas + Anna Kastl Zima — DONE (2026-11-26): 70 people, 15 families; 16 headings checked | 26–27, 56, 62 (s028–s029, s058, s064) | p.26, p.27 (s072) | 15 / 65 |
| U4a | John, first part — DONE (2026-11-27): 199 people, 48 families; 47 headings checked | 28–33 (s030–s035) | p.31 (s073) | split at a sub-family boundary |
| U4b | John, second part — DONE (2026-11-27): 150 people, 41 families; John's chapter fully checked | 34–40 (s036–s042) | pp.34–35 (s076) | (John total 80 / 244) |
| U5a | Jacob, first part — DONE (2026-11-27): 134 people, 37 families; 40 headings checked | 44–49 (s046–s051) | p.47 (s076) | split at a sub-family boundary |
| U5b | Jacob, second part — DONE (2026-11-27): 187 people, 47 families; Jacob's chapter fully checked | 50–55 (s052–s057) | p.54 (s076) | (Jacob total 72 / 229) |
| U6 | Andrew — DONE (2026-11-27): 164 people, 38 families; 41 headings/sub-lists checked | 57–61 (s059–s063) | p.60 (s076) | 35 / 120 |
| U7 | Integration — DONE (2026-11-27) | all | all | cross-branch marriages, duplicate people, unresolved supplement entries, final counts |

U1 notes: spouses named only in a child line stay `marriage` facts (Howard Thomas, Laura Foote,
Marianne Niemann, Louis Vanek, Bill Rohwer, Joyce Simodynes, Pamela Barsell, Ron Poskochil,
Patricia Sabol, Philip Edwards, James R. Bowen). Book-caused exceptions are in
`content/verification/allow-josef.json` (Shalon lineages; Patrick's children split 2 + 1 across his
two marriages). The supplement adds far more than the 1985 pages, so size other units by their
supplement sections too.

U2 notes: Thomas J. Kastl's children are recorded as Kastle ("Family changed name to Kastle").
Not attached to anyone, because the caption is ambiguous: "Joseph Sedlacek (cousin)" in s017-ph2,
and the "Joseph C. Kastl Ranch" photo (s020). Two 1986 "Their grandchild:" lines name no parents
and are notes. s071 numbers re-checked by eye (all match the transcription).

U5 split boundary (recorded 2026-11-27): **U5a** = s046–s053 up to, not including, "### The family
of Jacob Kastl and Mary Stara" (chapter opening, marriage agreement, 1935 obituary, all 11
children, the Dobry and John Joseph Kastl sub-families) plus s076 "Page 47 Correction".
**U5b** = from "The family of Jacob Kastl and Mary Stara" (s053) through s057, plus s076 from
"*(Page 54 Correction and Addition)*" to "## Andrew Kastl" (Rerucha, Kohoutek).
For U5b: reuse U5a's ids for Jacob's children (`jacob-kastl-1885`, `frank-kastl-1885`,
`anton-peter-kastl-1887`, `elizabeth-kastl-1891`, `antonia-kastl-1893`), remove their `continues`,
add Jacob Jr.'s s053 birth "20 March 1883" as a second reading, add the s076 Page 54 "ELIZABETH
KASTL RERUCHA (d) 1968." as a second source on Elizabeth's 1968 death, and give records to the
spouses U5a left as marriage facts (Mary Stara, Frances Rathovec, Julia Hanska, J. Cyril Rerucha,
Joseph Rathovec). Then add "jacob" to CHECKED_BRANCHES.

U7 results (2026-11-27): 1,285 people (1,284 from the book + 1 owner addition) and 322 families;
_roots 21/8, peter 206/49, wenzel 42/8, john 350/89, josef 148/39, jacob 322/84, thomas 11/2,
andrew 165/38, zima 20/5. Every printed family heading and children sub-list in all chapters and
the supplement matches (308 child lists, 285 printed lineages). Duplicate scan: 35 same-name
pairs, all different people (different parents/dates); Thomas's two Karls (1877, 1879) are
separate as printed ("given the same name as his brother"). No cross-branch marriages in the book's
families; no person carries the Kastl surname without descending from Andreas; no `continues` left.
Supplement coverage: every line of s071–s076 is cited somewhere (the s071 Log House addition is an
excerpt on Josef). ~100 in-law records have no facts of their own: the book names them only in a
family heading. 39 people show "The sources differ". Roots: s030/s046 "Joseph Marselek" added
as sources on Josef Marsalek's name.

U5b notes: Frank Kohoutek and Ludvick (Louis Peter) Rerucha were adopted by Elizabeth Kastl and
J. Cyril Rerucha (1921); no other marriage of Elizabeth's is in the book. June/Jane Marie and
Tyko/Tyk are differing readings (1986 correction). Zita's husband: Frank Vavruska (1985) vs John
A. Surlak (1986). Theophal's three children sit with his second wife, Virginia McCaston (the
list follows that marriage), with a note.

U4b notes: Curtis Mares's six children are printed under "…and Delores Johnson" but their own
entries name Delores Englebrecht (his second wife), so they sit in the second-marriage family
(allow-listed). Adopted children kept where printed, with notes (Curtis; Patricia and Jeanne
Mares). No supplement section for pp. 36–40.

U5a notes: Elizabeth's death 1965 (1985) vs 1968 (1986). "Step-son from second marriage (2)
Rachel Wall" (Gary Allen) is a one-parent family of Rachel Wall; allow-listed. The 1872 marriage
agreement and the 1935 obituary are excerpts on Jacob.

U4a notes: all nine of John's children have records; `anna-kastl-1870` and `john-kastl-1883`
carry `continues` until U4b builds their families (U4b removes it and adds "john" to
CHECKED_BRANCHES). "Children of Pat Hulse" (printed inside Virgil Pokorny's paragraph) is a
one-parent family; allow-listed. David James Ptacek (s076) = son of Donald L. Ptacek.
s030–s036 proofread word by word: no text errors.

U6 notes: Leontine Kastl's marriage (15 vs 24 Sept. 1945) and Ron Herms ("(d) 6 Apr. 1980" in
1985, "still living" in 1986) are kept as differing readings. Ernest Janak "(Son of Anton)" is
born 1915, before Frances married Anton in 1920 (plausibility warning, as printed). Inline
grandchildren on s061 (Pomeroy) are notes, not records. Childless second marriages with no
heading are marriage facts. The newspaper article on s057 is an excerpt on Andrew.

U3 notes: the 1986 supplement says "The family of John Kastl and Mary is an error. It should be:
The family of Martin Kastl", so the six children are Martin's (one-parent family carrying both
headings); John keeps both readings ("Mary" / "never married"). The 1867 ship list's "Wenzel,
age 6 months" fits no child in the list and is a note, not linked. s028–s029 fully re-proofread.

U4 split boundary (recorded 2026-11-27): **U4a** = s030 (John's chapter opening and his list of
nine children, all nine get records) through s038 up to, not including, "### The family of Anna
Kastl and Frank Mares" — i.e. the sub-families of Vaclav and of Barbara Kastl / Albert Mares
(incl. the 1922 Emporia Gazette article s033–s035), plus supplement p.31 (s073, Kantor families)
and pp.34–35 (s076, Ptacek). **U4b** = from "### The family of Anna Kastl and Frank Mares" (s038)
through s042: the Anna Kastl / Frank Mares and John Kastl / Frances Havlovic sub-families. U4b
extends john.json and reuses U4a's ids for John's children.

Notes for the split units: pick the boundary where one child-of-the-brother's sub-family ends
(check the lineage parentheses), and record the exact boundary here before starting.
Run U4a/U4b and U5a/U5b one after another or give them disjoint id prefixes, so ids don't clash.

### 8. Full verification of relationships and facts, after the build-out (owner request)
Why: a spot check after the refocus found 3 wrong relationship labels (Thomas Kastl shown as
"Half-brother of the seven brothers"; Maria Mužik and Andreas Mužik not shown as ancestors).
The underlying data was right — the bug was in the code that turns data into kinship words — but
nothing tested that code, and the build-out will multiply both data and labels ~25×. Check both.

a. **Automated checks in the build** — DONE (`tools/checks.py`; failures stop the build,
   plausibility warnings go to `content/verification/build-warnings.txt`; book-caused
   exceptions in `content/verification/allow-<branch>.json`). Heading and count checks apply to the
   branches in `CHECKED_BRANCHES`; lineage checks apply to every family already in the data.
   Mutation-tested: a moved child, a dropped link, a wrong sex and an orphan are all caught.
   - **Printed lineage vs. computed ancestry.** Nearly every family paragraph prints the person's
     line back to a brother, e.g. "RICHARD DENNIS KASTL (Dennis, Stanley, Joseph W., Josef)".
     Parse it and compare it, name by name, with the parent chain in the data. This is an
     independent check of every parent link, straight from the book. Mismatches the book itself
     causes (e.g. Thomas Shalon printed as "(Mary Kastl Shalon, Joseph, Josef)") go in an
     allow-list with a note.
   - Child counts per family equal the printed numbered list.
   - Plausibility warnings (not failures — the book has real oddities): child born before parent
     is 13 or after mother's death; marriage after the first child; birth after own death;
     same name + same birth date twice (possible duplicate).
   - Every person reachable from Andreas or married to someone who is; no orphan records.
b. **Tests for the label code** — DONE (`LABEL_CASES` in `tools/checks.py`, 17 cases). A table of known cases checked on each build: Thomas = "Father of
   the seven brothers", Maria Mužik = "Grandmother…", Andreas Mužik = "Great-grandfather…",
   Matthew Richard Kastl = "3× great-grandson of Josef Kastl", Barbara Kellner = "Second wife of
   Thomas Kastl", a half-sibling, a spouse, an in-law's parent. Add cases whenever a bug is found.
c. **Targeted audit — DONE (2026-11-27, owner chose A + B):** one independent agent re-checked
   the 88 riskiest items against the scans (every "sources differ" person, every warning, every
   allow-list note, 26 family-structure judgement calls): 80 OK, 6 extraction slips fixed (missing
   "(1)" on first marriages), 2 decisions made. Report: `content/verification/audit-targeted-2026-11.md`.
   The full per-branch audit below remains optional (~1.5–2 token windows).
   **Full independent audit per branch (optional).** A different agent from the one that extracted the branch
   re-reads the branch's pages (scans, not just transcriptions) and checks every person and family
   record: parents, spouse(s), children and order, each fact's value against its quote. Output: a
   findings list per branch; fixes go in as separate commits that cite the finding.
d. **Owner review aid — DONE:** `/review/` (unlisted, noindex). A generated, unlisted report page: per branch, every person with their
   parents, spouses, children and the page links, plus all warnings from (a) and the "sources
   differ" cases — so the owner can scan for anything that looks wrong from family knowledge.
e. Results (2026-11-27): automated checks pass on all 1,285 people (308 child lists, 285 printed
   lineages, 3,829 quotes, 17 label tests); targeted audit as in (c). Open: the optional full audit.

Items (a) and (b) are cheap and should land **before** the build-out starts (U1), so every unit
is checked as it goes; (c)–(e) run after U7.

### 7. Verification debt (see TECH_DEBT.md)
- Done: s028–s029 (U3) and s030–s036 (U4a) re-proofread word by word against the images.

## Future sessions (owner's to-do, 2026-11-27)
Each item is meant for its own session. Start with `CLAUDE.md` (sync with main first), keep the
book as the only source, keep the build passing, and commit to `main` when done. The owner's token
window is limited, so prefer scripts to agents and run at most one or two agents per session.

### F1. Links in the narrative
Link names in chapter narratives and articles (`content/pages/sNNN.md`) to person pages where the
reference is unambiguous ("his son Frank" inside Peter's chapter, "Mrs. Albert Mares" → Barbara
Kastl). Never guess: the book has many Josephs, Johns and Marys, so skip anything ambiguous and
list it. Suggested approach: store links as data (e.g. `content/links.json`: scan, exact phrase,
person id), not by editing transcriptions, so they stay faithful; render them in the book reader
and check each phrase exists, like the quote check. One agent per chapter group at most.

### F2. Photo album page
One page with every photo in the book (46 crops in `media/photos/`, ids and captions in page front
matter), grouped by chapter or branch, each with its caption, page link, and links to the people
it is attached to (26 photos are on person pages). Include the scene photos (dugout, Omaha 1867,
Plasi livery stable, rabbit drive, cattle drives) and the uncaptioned ones. Script-only; no agent.

### F3. Map page
Places from facts (births, deaths, burials, residences, homesteads), normalised to a place list
(Všepadly, Stara Hut, Plasi, Brainard, Weston, Wahoo, Omaha, Bakersfield, Yukon…), each with the
people connected to it. Show them on a map plus a places index; also link the book's own maps
(p.6 Pilsen sheet, p.11 homestead map). Coordinates must be added by hand (or from a static
gazetteer file committed to the repo), not fetched at runtime; keep spellings as printed with a
normalised key. Map library: a pinned CDN version only if needed, or a simple inline SVG of
Nebraska plus a Bohemia inset.

### F4. Emigration timeline
1866–1872: each brother's arrival (date, port, ship, who came with him), then homesteads,
first deaths in America, moves to California, Oklahoma and Illinois. Built from `immigration`,
`homestead` and `residence` facts. Where sources differ (Peter's year; John's ship, SS Baltimore
vs SS Berlin), show both readings. Script-only; no agent.

### F5. Full independent audit per branch (backlog 8c, full version)
Optional. A fresh agent per branch (not the one that extracted it) re-reads the branch's scans
and checks every person and family: parents, spouses, children and order, each fact's value
against its quote. The targeted audit already covered the riskiest 88 items, and the automated
checks cover counts, lineages and quotes. Cost: about 1.5–2 token windows in total, so split it
over several sessions, one or two branches each (e.g. John + Wenzel, Jacob, Peter, Andrew + Josef
+ Thomas + Zima + roots). Write findings to `content/verification/audit-<branch>.md`; fixes go in
as separate commits that cite the finding.

### Smaller ideas
- Tree: optional top-down layout; in-marrying spouses as their own boxes; print/export.
- Tree: check "Open everything" performance on an older phone (about 1,300 nodes).
- Table: a places column; filter by place and by decade.
- Per-branch reading guide: chapter narrative plus photos.
- A "suppressed" flag, should a living relative ever ask to be removed.

## Decisions
- The book is the best available fact. The owner does not know the people in it personally, so
  family-knowledge review is not possible; step 8d's report is for scanning for oddities only
  (owner, 2026-11-26).
- Search indexing: keep the site indexable (owner, 2026-11-26). Search results and 404 are noindex.
- Pages serves `main` / root (confirmed by owner).

## Owner to-do
- Optional: submit https://jkastl.github.io/kfh/sitemap.xml in Google Search Console
  (jkastl.github.io property) so the site is found sooner.
