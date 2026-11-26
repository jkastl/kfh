# Transcription spec — Kastl Family History (1985 book + later supplement)

You are producing a FAITHFUL, page-by-page transcription of a scanned genealogy book. This transcription is the
single source of truth for a website, so accuracy of every name, date, place and relationship matters more than speed.

## Inputs per scan id (e.g. s073), all under 
- `web/sNNN.jpg`      full page, 1400px wide — use for layout, columns, reading order, photos
- `crops/sNNN_1.jpg`, `_2.jpg`, `_3.jpg`  top/middle/bottom thirds at higher resolution (with ~12% overlap) — READ ALL THREE; use them to verify every name, number and date
- `ocr/sNNN.txt`      machine OCR of the page (pdftotext -layout). Only a hint: it often merges the two columns line-by-line, confuses l/!/1/I ("Kast!" = "Kastl"), and drops spaces. Never trust it over the image.

## Output: write `trans/sNNN.md` (one file per scan), exactly this shape

```
---
scan: s073
printed_page: "5"          # page number printed on the page, as a string; null if none visible
kind: genealogy            # one of: cover, title, toc, text, genealogy, photos, map, chart, mixed, blank
running_head: null         # any running header text, else null
continues_from_previous: true   # does the first text on the page continue a sentence/entry from the prior page?
continues_to_next: false        # does the last text run on to the next page?
photos:                    # one entry per photograph/illustration/map/document image on the page; [] if none
  - id: s073-ph1
    bbox: [0.05, 0.10, 0.48, 0.42]   # approx [x0, y0, x1, y1] as FRACTIONS of web/sNNN.jpg width/height (be generous, include the whole image but not caption)
    caption: "exact caption text as printed, or null"
    description: "short neutral description of what is shown (people count, setting, building...)"
annotations:               # stamps, handwriting, library marks — anything NOT part of the printed book; [] if none
  - "Handwritten in margin: ..."
notes: "anything odd: smudges, cut-off text, uncertain readings summary"
---

<markdown body>
```

## Body rules
1. **Reading order**: full-width headings first where they span both columns; otherwise left column top→bottom, then right column top→bottom. If a block clearly spans both columns (a chapter title, a wide photo caption) place it where it occurs.
2. **Chapter/section titles** (large bold, e.g. "The Family of Joseph Kastl", "Preface", "John Kastl") → `## Title`.
   Italic sub-notes under titles (e.g. "(Page 41 Correction and Addition)") → keep on their own line in italics: `*(Page 41 Correction and Addition)*`.
3. **Family-group headings** (bold "The family of X and Y") → `### The family of X and Y` — exact spelling as printed.
4. **Paragraphs**: join lines into paragraphs. Remove end-of-line hyphenation that only exists because of line wrap ("mar-\nried" → "married", "Miriov-\nsky" → "Miriovsky"), but keep real hyphens/dashes. Keep the em-dash "—" exactly as used (e.g. "Elznic—8 March 1980", "1. RICHARD DENNIS — (b) 15 Feb. 1957").
5. **Child lists**: one list item per child, e.g. `1. MATTHEW RICHARD — (b) 23 Sept. 1983.` Keep ALL CAPS names in caps, keep "(b)", "(m)", "(d)", "(bur)", "(div)" etc. exactly. Wrapped continuation lines are joined into the same item.
6. **Do not correct the book.** Preserve original spellings, typos, inconsistent name forms (Kastl/Kastel, Josef/Joseph, Sept./Sep.), punctuation. If you are sure the PRINT has a typo, still transcribe it as printed; you may add `{sic}` right after it only when it would otherwise look like a transcription error.
7. **Uncertainty**: if a character/word is unclear even on the crops, write your best reading followed by `[?]`, e.g. `Hentges[?]`. Truly unreadable → `[illegible]`. Text cut off by the scan edge → `[cut off]`.
8. **Photos / illustrations / maps / charts** in the body: put a placeholder line where it sits in reading order: `[[photo s073-ph1]]` (ids matching the frontmatter). The caption goes in frontmatter only — do not also duplicate it in the body.
9. **Charts/tables** (e.g. an ancestral/pedigree chart): transcribe their full textual content as a structured nested markdown list that preserves who connects to whom, plus a note on layout. Be extremely careful here — this encodes the tree.
10. **Page number** printed at the bottom: goes in `printed_page` only, not in body. Running headers likewise.
11. Library stamps, microfilm stamps, handwritten notes, call numbers → `annotations` only, never in body.
12. Use straight ASCII quotes in YAML; quote any YAML string containing a colon.

## Before finishing each page
Re-read every name, date and number in your transcription against the crops one more time. Dates and spellings of names are the
most important data on the site. Count the children in each list and confirm the numbering matches the print.
Write the file with the Write tool. Do not touch any other directory. Do not modify any file outside `trans/`.

## Final report (your reply)
Keep it short: for each scan, one line `sNNN | printed_page | kind | first heading or first words | any [?] count`.
Then list anything structurally notable (e.g. "s045 seems to duplicate s044", "page order jumps from p.20 to p.23", "this is a supplement page").
