# Working in this repo

## Always start from the latest code

Before any development work (and again when resuming a session, before committing, and before
pushing), make sure the work sits on the latest code:

1. `git fetch origin main`.
2. Check whether local `main` is behind `origin/main` (`git log HEAD..origin/main`).
3. If it is, fast-forward (`git pull --ff-only`) before writing anything.
4. If the update fails, conflicts, or would need a force push or other history rewrite: stop and
   raise it with the user. Don't build on code that may be stale.
5. Say briefly what the check found ("up to date with main", "main had 3 new commits, pulled").

## Where the plan lives

- `BACKLOG.md`: what's next, the work units for building out the rest of the tree, open
  questions. Update it when an item lands or a decision is made.
- `docs/EXTRACTION.md`: how to turn transcribed pages into people data (the rules every work
  unit follows). `TECH_DEBT.md`: known gaps.

## How this site is built and deployed

- GitHub Pages deploys straight from `main` (root). **No GitHub Actions** — the owner has
  little Actions budget. Do not add workflows.
- The site is plain static files. `python3 tools/build.py` (standard library only — no pip, no
  npm) regenerates every HTML page from `content/`. Generated output is committed.
- `.nojekyll` must stay, so Pages serves the files as-is.
- Page counts: `assets/js/stats.js` (GoatCounter, site code `jkastl`). Every page loads it.
- This site must **not** be added to the jkastl.github.io index page or its sitemap.

## The content is a real, published family history

- `content/pages/sNNN.md` is a faithful transcription of scan `sNNN` of the book (1985) and its
  1986 supplement. Transcriptions keep the book's own spellings, typos and inconsistencies.
  Never "correct" the book; only fix transcription mistakes, checked against the page image.
- `content/people/*.json` hold the structured family data (one file per branch, plus `_roots.json`). Every fact cites the scan(s) it comes
  from. When sources disagree (book vs. supplement, chart vs. text), record every reading with its
  source; never silently pick one.
- Do not add facts from outside the book without the owner's say-so, and label them if added.

## Versioning

The site uses semantic versioning. The version lives in `VERSION`, shows in every page's footer,
and each release gets an entry in `CHANGELOG.md` and an annotated git tag (`vX.Y.Z`) on `main`.
- **MAJOR**: a break for anyone linking to the site or using its data, e.g. person URLs or ids
  change, pages removed, the CSV/JSON shape changes.
- **MINOR**: something new, e.g. a new page or feature (map, timeline, photo album, narrative links)
  or a substantial addition of people.
- **PATCH**: fixes, e.g. data or transcription corrections, audit fixes, wording, styling.
Bump `VERSION`, add the changelog entry, rebuild, commit, then tag the commit and push the tag.
