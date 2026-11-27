# Tech debt and open items

## Repository size
The two source PDFs (`source/`, ~28 MB each) and the 76 page images (`media/pages`, ~24 MB) are
committed directly. They fit within GitHub's limits (100 MB per file, Pages 1 GB per site), but
every future change to these binaries grows the history permanently. If the scans are ever
re-done at higher resolution, move them to a release asset or external storage instead of
committing new copies.

## Transcription verification gaps
- Every text page had a second, independent proofread against the images. The weak pass over
  s028–s036 was redone word by word in U3 and U4a (no text errors found).
- s071 (supplement p. 3): resolved in U2. Every number in the Peter section was re-read on a
  high-resolution scan and matches the transcription; the OCR misreads (e.g. Donald Harling
  1928 for 1923) are OCR errors.
- Ancestral chart (s016, p. 14): in its typewriter face "a" and "e" are nearly identical, so the
  names Jan, Tomas, Alzbeta, Marie, Frances, Anna carry `[?]` marks; Barbara Kellner's birth day
  is typed over (24 over 14?). p. 62 prints 14 April 1828.

## Scope
All seven brothers' branches, Anna Kastl Zima's and the shared roots are built out as
structured people (1,284 from the book, 1 owner addition). Integration (U7), the automated checks
and the targeted audit (BACKLOG step 8) are done; the full per-branch audit (F5) is optional.

## Narrative links (F1)
Links cover the narrative chapters, the chapter openings, the articles and the obituary
(`content/links.json`). The genealogy lists themselves are not linked inline: their people are
already the structured records, listed under "People … on this page" in the reader. Excerpts
on person pages (e.g. the 1935 obituary on Jacob) are rendered without links.
