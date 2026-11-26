# Tech debt and open items

## Repository size
The two source PDFs (`source/`, ~28 MB each) and the 76 page images (`media/pages`, ~24 MB) are
committed directly. They fit within GitHub's limits (100 MB per file, Pages 1 GB per site), but
every future change to these binaries grows the history permanently. If the scans are ever
re-done at higher resolution, move them to a release asset or external storage instead of
committing new copies.

## Transcription verification gaps
- Every text page had a second, independent proofread against the images. The pass over scans
  s028–s036 (John Kastl chapter, pp. 26–34) made too few image reads to have checked every crop,
  so treat those pages as single-checked until re-verified. They are outside the current lineage
  scope.
- s071 (supplement p. 3) shows several number mismatches against the embedded machine OCR
  (e.g. Donald Harling's birth year: image reads 1923, OCR 1928). The image reading is used;
  re-check by eye when the Peter Kastl branch is built out.
- Ancestral chart (s016, p. 14): in its typewriter face "a" and "e" are nearly identical, so the
  names Jan, Tomas, Alzbeta, Marie, Frances, Anna carry `[?]` marks; Barbara Kellner's birth day
  is typed over (24 over 14?). p. 62 prints 14 April 1828.

## Scope
Only Matthew Richard Kastl's direct paternal line and its immediate families are built out as
structured people. Everyone else exists in the book reader (transcriptions + scans) only.
