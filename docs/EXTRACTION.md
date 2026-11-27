# Extracting people from the book

How to turn transcribed pages (`content/pages/sNNN.md`) into structured people data. Every work
unit in `BACKLOG.md` follows this. The first slice (`content/people.json`, Josef's line) is the
worked example — copy its shape.

## Ground rules
1. **The book is the only source.** No outside facts, no guesses, no "fixing" the book.
2. **Every fact carries at least one verbatim quote** from the page it comes from. The build
   (`python3 tools/build.py`) fails if a quote is not found word for word in that page's
   transcription (whitespace and `*` emphasis ignored). Quote the smallest span that proves the
   fact, but enough to be unambiguous.
3. **Disagreements are recorded, not resolved.** If the 1985 pages and the 1986 supplement (or the
   chart and the text) give different values, add one fact per reading, each with its own sources.
   The site marks these "The sources differ".
4. **Spellings as printed.** Use the book's spelling for `name`. Other forms of the same
   person's name go in one `name` fact whose value lists just those forms ("Joseph Kastl"); its
   sources show where each appears, so don't describe locations in the value. Use two or more
   `name` facts only when the sources genuinely disagree on who the person was named.
5. If the transcription itself looks wrong, check the scan (`media/pages/sNNN.jpg`). Fix the
   transcription only for a real transcription error, and note it in the commit message.
6. If you cannot tell who a passage refers to (e.g. several Joseph Kastls), leave it out and
   note it in `BACKLOG.md` under the unit.

## Additions from outside the book (owner only)
Only the site owner can add something the book doesn't contain (CLAUDE.md). Mark it so it can't be
mistaken for the book: give the person `"owner_added": true` and give each fact the source
`{"owner": "Added by the site owner, <date>"}` instead of a scan and quote. The site labels these
"Unsourced", the About page counts them, and the child-count
check ignores owner-added children. On a book record, an owner addition may only be a `note`.

## How the book is laid out
- Each brother's chapter opens with a narrative about him, then "The children of …" list, then
  one **family group** per married descendant: heading "The family of X and Y", a paragraph
  "X (lineage) born …, son/daughter of …, married Y …", then "Their children:" as a numbered list.
- The **lineage parentheses** name ancestors back to the brother: "STANLEY KASTL (Joseph, Josef)";
  for descendants through a daughter, her married name appears: "(Marie Kastl Burnett, Stanley,
  Joseph W., Josef)". Use them to place people; they are the most reliable structural signal.
- Child-list lines: `N. NAME — (b) date—place. (d) date. (m) Spouse—date.` `(bur)` buried,
  `(div)` divorced, `(2)` second spouse, `aka` also known as.
- The **1986 Supplement** (s071–s076) is arranged by the page it corrects: "*(Page 41 Correction
  and Addition)*". Its entries add children born after 1985, fuller dates and corrections. Treat
  each as a separate source; keep the 1985 reading too.

## Who gets a record
- Everyone listed as a **child** in a family group or child list.
- Both **partners** of every family group heading ("The family of X and Y").
- Parents of an in-marrying spouse only if the book names them as a pair with dates or as a
  family (otherwise keep it in a fact: "daughter of Joseph Nemecek").
- A spouse named only inside a child line ("(m) Caroline Kunasek—16 Nov. 1926") with no family
  group of their own → a `marriage` fact on the child, not a separate record.

## File and record shape
Write only your branch file: `content/people/<branch>.json` (until the split in BACKLOG step 2
lands, add to `content/people.json`). Shape:

```json
{
  "people": {
    "frank-kastl-1900": {
      "name": "Frank Kastl",
      "sex": "M",
      "branch": "josef",
      "facts": [
        {"type": "birth", "value": "22 September 1900, Central City, Nebraska",
         "sources": [{"scan": "s043", "quote": "FRANK KASTL (Joseph, Josef) born 22 September 1900, Central City, Nebraska"}]}
      ],
      "photos": ["s044-ph1"]
    }
  },
  "families": [
    {"id": "frank1900-caroline", "partners": ["frank-kastl-1900", "caroline-kunasek"],
     "heading": "The family of Frank Kastl and Caroline Kunasek",
     "marriage": [{"value": "16 November 1926", "sources": [{"scan": "s044", "quote": "Caroline Kunasek 16 November 1926."}]}],
     "children": ["mary-ann-kastl-1927", "margaret-kastl-1931"], "sources": ["s043", "s044"]}
  ]
}
```

- **ids**: `given-surname-birthyear` in lowercase ASCII (`mary-ann-kastl-1927`); no birth year →
  `given-surname-<parentid-fragment>` (e.g. `robert-kastl-of-john1906`). Must be unique across
  all files; check before adding.
- **fact types**: `name`, `birth`, `death`, `burial`, `marriage`, `immigration`, `homestead`,
  `occupation`, `residence`, `note`. Values are written out plainly ("22 September 1900, Central
  City, Nebraska"); the quote carries the printed form ("22 Sept. 1900—Central City, NE.").
- **children** in printed order, even when out of birth order; say so in the family `note`.
- Multiple marriages: one family per marriage, with `"order": 1`, `2`. A marriage whose spouse
  the book doesn't name (e.g. "Two children were born to first marriage") is a family with one
  partner; so is a heading naming one parent ("The family of Therese Kripal").
- Which marriage a child list belongs to, when a paragraph names two spouses before "Their
  children:" and the book doesn't say: if the heading names one spouse, the children go with that
  spouse; if it names both, they go with the marriage the list follows (the last one named).
  Explain it in the family `note`. Cases: Lawrence A. Prchal (heading names Frances), Theophal
  Kastl (heading names both; list follows Virginia McCaston).
- Don't turn an inference into a fact. A source that simply omits a date is another source for
  the dated fact, not a second reading.
- `heading`: the printed heading text without `### `. Use a list when the same family is printed
  under several headings (1985 and 1986 forms). The build matches every printed heading to a
  family by this text, so copy it exactly.
- `sex`: `M`/`F` from son/daughter/he/she or an unambiguous given name, else `U`.
- `summary` (brothers and Anna only): one short line for their card on the home page, e.g.
  "Came to America in 1868". It must be backed by facts cited on the same record.
- `photos`: photo ids from page front matter (`s044-ph1`) where the caption names the person.

## Checklist before committing a unit
- [ ] Every `###` family heading in the unit's pages (and its supplement sections) is represented
      by a family, or listed in the commit message with the reason it isn't.
- [ ] For each family, the number of children equals the printed list (count them).
- [ ] Supplement additions/corrections for the unit's pages are merged as extra sources/facts.
- [ ] Add the branch key to `CHECKED_BRANCHES` in `tools/checks.py`.
- [ ] While working (other units may be running), use the check-only mode, which writes
      nothing: `KFH_CHECK_BRANCHES=<branch> python3 tools/build.py --check`.
- [ ] `python3 tools/build.py` passes and the branch pages render. Besides quotes, the build checks
      that every printed family heading in the branch's chapter and supplement section has a
      family, that child counts match the printed lists, and that each printed lineage
      "(Parent, Grandparent, …)" matches the data's line of descent. Where the book itself
      causes a mismatch, add an entry with a `note` to `content/verification/allow-<branch>.json`;
      never bend the data to pass. Read `content/verification/build-warnings.txt`
      (plausibility) and check each new warning against the scan.
- [ ] Spot-check at least ten facts against the scan images, not just the transcription.
- [ ] Update `BACKLOG.md` (unit done, anything left out and why).
