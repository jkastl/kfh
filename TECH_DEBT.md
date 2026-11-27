# Tech debt and open items

## Repository size
The two source PDFs (`source/`, ~28 MB each) and the 76 page images (`media/pages`, ~24 MB) are
committed directly. They fit within GitHub's limits (100 MB per file, Pages 1 GB per site), but
every future change to these binaries grows the history permanently. If the scans are ever
re-done at higher resolution, move them to a release asset or external storage instead of
committing new copies.

## Transcription verification gaps
- Every text page had a second, independent proofread against the images. The pass over scans
  s030–s036 (John Kastl chapter, pp. 28–34) made too few image reads to have checked every crop,
  so treat those pages as single-checked until U4a/U4b re-verify them. (s028–s029 were
  re-proofread word by word in U3.)
- s071 (supplement p. 3): resolved in U2. Every number in the Peter section was re-read on a
  high-resolution scan and matches the transcription; the OCR misreads (e.g. Donald Harling
  1928 for 1923) are OCR errors.
- Ancestral chart (s016, p. 14): in its typewriter face "a" and "e" are nearly identical, so the
  names Jan, Tomas, Alzbeta, Marie, Frances, Anna carry `[?]` marks; Barbara Kellner's birth day
  is typed over (24 over 14?). p. 62 prints 14 April 1828.

## Scope
Built out as structured people so far: the shared roots and the branches of Peter, Wenzel,
Josef, Thomas, Andrew and Anna Kastl Zima. John and Jacob exist in the book reader
(transcriptions + scans) only until U4–U5 land (see BACKLOG.md).
