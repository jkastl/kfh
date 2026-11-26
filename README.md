# Kastl Family History

A site for reading and exploring *Kastl Family History* (Evelyn Coufal and Francis Vech, printed
1985 by Catholic Quote, Valparaiso, Nebraska) and its 1986 Supplementary Section.

Live at <https://jkastl.github.io/kfh/>.

## Layout

| Path | What it is |
|---|---|
| `source/` | The scanned book as two PDFs (Family History Library microfilm scan). |
| `media/pages/`, `media/thumbs/` | One image per scan, `s001`–`s076`, cut from the PDFs. |
| `content/pages/sNNN.md` | Faithful transcription of each scan (JSON front matter + Markdown). |
| `content/people.json` | Structured people and families, every fact cited to a scan. |
| `content/verification/` | Logs from the independent proofreading pass. |
| `tools/build.py` | Regenerates all HTML. Python 3 standard library only. |

## Build

```bash
python3 tools/build.py
```

Then commit the regenerated files and push to `main`. Pages serves `main` as-is (no Actions).

See `CLAUDE.md` for conventions and `TECH_DEBT.md` for known gaps.
