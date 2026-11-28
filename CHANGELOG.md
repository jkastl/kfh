# Changelog

All notable changes to this site. Versions follow [semantic versioning](https://semver.org/);
see `CLAUDE.md` for what counts as major, minor and patch here.

## 1.2.0 — 2026-11-28

- **Emigration timeline.** A new Timeline page, "Coming to America", follows the seven brothers
  from Bohemia to America, 1865–1872: who came when, on which ship and with whom, then the
  homesteads and log houses, the first deaths in America, and the family's later moves to
  Illinois, California, Oklahoma and Kansas, through the death of Jacob, the last brother, in
  1935. Every entry quotes the book. Where the book disagrees with itself (Peter's year, 1865
  or 1866; John's ship, SS Baltimore or SS Berlin) both readings are shown. People on the
  timeline get a link to it from their page.
- Peter Kastl's record now shows both readings of his emigration year: the family story that
  places it in 1865 was missing.

## 1.1.0 — 2026-11-27

- **Names in the narrative link to people.** In the history chapters, the chapter openings and the
  reprinted articles and obituary, 223 names now link to the person they refer to (88 people),
  wherever the book makes clear who is meant. Each person's page lists where the book's chapters
  and articles mention them. The transcriptions themselves are unchanged; the links are kept in
  `content/links.json` and checked on every build. 18 references that could mean more than one
  person are deliberately left unlinked and listed with the reason.
- **Photo album.** A new Photos page shows all 46 pictures in the book: 32 photographs grouped by
  chapter, each with the book's caption, its page and the people in it, then the maps, documents
  and drawings.
- The family tree's legend no longer says only one branch is built out.

## 1.0.0 — 2026-11-27

First complete release of *Kastl Family History* (1985) and its 1986 Supplementary Section.

- **The book:** all 76 scanned pages with verified transcriptions, arranged by the book's own
  sections; the two source PDFs.
- **People:** 1,285 people in 322 families: the shared ancestors, the seven Kastl brothers
  (Peter, Wenzel, John, Josef, Jacob, Thomas, Andrew), their half-sister Anna Kastl Zima, and
  every descendant the book names. Every fact cites its page with the book's exact words; where
  the 1985 pages and the 1986 supplement (or chart and text) disagree, every reading is shown.
  One person is an owner addition, marked "Unsourced".
- **Explore:** an interactive family tree (pan, zoom, search), a sortable and filterable table of
  everyone with CSV download, and full-text search.
- **Checks on every build:** each quoted passage is verified word for word against its
  transcription; every printed family heading and child list matches the data (308 lists); every
  printed lineage matches the line of descent (285); relationship-label tests; plausibility
  warnings.
- **Verification:** all transcriptions proofread twice against the scans; a targeted audit of the
  88 riskiest records against the scans (80 confirmed, 6 fixed, 2 decided); an unlisted review
  report at `/review/`.
