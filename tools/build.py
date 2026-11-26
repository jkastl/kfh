#!/usr/bin/env python3
"""Build the Kastl Family History site.

Standard library only. Reads content/pages/*.md and content/people.json, writes static HTML
into the repo root (index.html, people/, book/, about/, search/). Fails if any quoted fact in
people.json does not appear verbatim in the transcription of the page it cites.

    python3 tools/build.py
"""
import html
import json
import re
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SITE_URL = "https://jkastl.github.io/kfh/"
TITLE = "Kastl Family History"

FACT_LABELS = {
    "name": "Name", "birth": "Born", "death": "Died", "burial": "Buried",
    "marriage": "Married", "immigration": "Emigrated", "homestead": "Homestead",
    "occupation": "Occupation", "residence": "Lived", "note": "Noted",
}
FACT_ORDER = ["name", "birth", "occupation", "residence", "marriage", "immigration",
              "homestead", "death", "burial", "note"]
CONFLICT_TYPES = {"birth", "death", "burial", "immigration", "marriage"}

esc = html.escape

# Fragments kept out of f-string expressions so the script runs on Python 3.8+ (macOS ships 3.9).
CURRENT = ' aria-current="page"'
DIFFERS_ROW = ' class="differs-row"'
ON_LINE_LI = ' class="on-line"'
LINE_TAG = ' <span class="line-tag">the line continues</span>'


def marr_span(m):
    return f' <span class="muted">· {inline(m)}</span>' if m else ""


# ----------------------------------------------------------------------------- pages
def load_pages():
    pages = []
    for f in sorted((CONTENT / "pages").glob("s*.md")):
        text = f.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f
        fm, body = text[4:].split("\n---\n", 1)
        meta = json.loads(fm)
        meta["body"] = body.strip("\n")
        pages.append(meta)
    # book structure: s001-s068 = 1985 book, s069-s076 = 1986 supplement
    for p in pages:
        n = int(p["scan"][1:])
        p["supplement"] = n >= 69
        pp = p.get("printed_page")
        if p["scan"] == "s001":
            p["slug"], p["label"], p["short"] = "cover", "Cover", "Cover"
        elif p["scan"] == "s002":
            p["slug"], p["label"], p["short"] = "title", "Title page", "Title"
        elif p["scan"] == "s003":
            p["slug"], p["label"], p["short"] = "contents", "Contents", "Contents"
        elif not p["supplement"]:
            if not pp:  # s016 = p.14 (contents lists the Ancestral Chart on p.14); s066 = p.64 by sequence
                pp = {"s016": "14", "s066": "64"}[p["scan"]]
                p["inferred_page"] = True
            p["slug"], p["label"], p["short"] = f"p{pp}", f"Page {pp}", f"p. {pp}"
        else:
            sp = pp or {"s069": "1", "s070": "2"}[p["scan"]]
            if not pp:
                p["inferred_page"] = True
            p["slug"] = f"supplement-{sp}"
            p["label"] = "Supplement, title page" if sp == "1" else f"Supplement page {sp}"
            p["short"] = f"Supp. p. {sp}"
    return pages


def page_title(p):
    """First heading on the page, else a description of what it holds."""
    for line in p["body"].splitlines():
        m = re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            return strip_md(m.group(2))
    if p["photos"]:
        cap = p["photos"][0].get("caption")
        if cap:
            return cap
    return {"cover": "Cover", "title": "Title page", "blank": "Blank page", "photos": "Photographs",
            "map": "Map"}.get(p["kind"], "")


def strip_md(s):
    return re.sub(r"\*+", "", s).strip()


# ----------------------------------------------------------------------------- markdown
def inline(s):
    s = esc(s, quote=False)
    s = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = s.replace("{sic}", '<span class="sic" title="As printed in the book">[sic]</span>')
    s = re.sub(r"\[\?\]", '<span class="unsure" title="Uncertain reading of the scan">[?]</span>', s)
    s = s.replace("[illegible]", '<span class="unsure">[illegible]</span>')
    s = s.replace("[cut off]", '<span class="unsure">[cut off]</span>')
    return s


def render_md(body, photos, prefix):
    """Render the small Markdown dialect used by the transcriptions."""
    photo_by_id = {ph["id"]: ph for ph in photos}
    out, para, stack = [], [], []  # stack of open list types with indent

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def close_lists(to_indent=-1):
        while stack and stack[-1][1] > to_indent:
            out.append(f"</li></{stack.pop()[0]}>")

    for raw in body.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            continue
        m_ph = re.match(r"^\[\[photo ([\w-]+)\]\]$", line.strip())
        m_h = re.match(r"^(#{2,3})\s+(.*)$", line)
        m_ol = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        m_ul = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if m_ph:
            flush_para(); close_lists()
            ph = photo_by_id.get(m_ph.group(1))
            if ph:
                out.append(figure(ph, prefix))
        elif m_h:
            flush_para(); close_lists()
            lvl = len(m_h.group(1))
            text = m_h.group(2)
            out.append(f'<h{lvl + 1} id="{slugify(strip_md(text))}">{inline(text)}</h{lvl + 1}>')
        elif m_ol or m_ul:
            flush_para()
            indent = len((m_ol or m_ul).group(1))
            kind = "ol" if m_ol else "ul"
            if stack and stack[-1][1] == indent and stack[-1][0] == kind:
                out.append("</li>")
            else:
                close_lists(indent)
                if stack and stack[-1][1] == indent:  # same indent, different list type
                    out.append(f"</li></{stack.pop()[0]}>")
                if kind == "ol":
                    out.append(f'<ol start="{m_ol.group(2)}">')
                else:
                    out.append("<ul>")
                stack.append((kind, indent))
            if m_ol:
                out.append(f'<li value="{m_ol.group(2)}">{inline(m_ol.group(3))}')
            else:
                out.append(f"<li>{inline(m_ul.group(2))}")
        else:
            if stack and raw.startswith(" "):  # continuation of a list item
                out.append(" " + inline(line.strip()))
                continue
            close_lists()
            para.append(line.strip())
    flush_para()
    close_lists()
    return "\n".join(out)


def figure(ph, prefix, link=None):
    src = f"{prefix}media/photos/{ph['id']}.jpg"
    w, h = jpeg_size(ROOT / "media" / "photos" / f"{ph['id']}.jpg")
    cap = ph.get("caption")
    alt = ph.get("description") or cap or ""
    img = f'<img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">'
    img = f'<a href="{esc(link or src)}">{img}</a>'
    capt = f"<figcaption>{inline(cap)}</figcaption>" if cap else ""
    return f'<figure class="photo">{img}{capt}</figure>'


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def jpeg_size(path):
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        seglen = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seglen
    raise ValueError(path)


# ----------------------------------------------------------------------------- quote check
def norm(s):
    s = s.replace("**", "").replace("*", "")
    s = re.sub(r"^\s*-\s+", "", s, flags=re.M)
    return re.sub(r"\s+", " ", s).strip()


def check_quotes(data, pages_by_scan):
    corpus = {}
    for scan, p in pages_by_scan.items():
        caps = " ".join((ph.get("caption") or "") for ph in p["photos"])
        corpus[scan] = norm(p["body"] + " " + caps)
    problems = []

    def chk(scan, q, where):
        if scan not in corpus:
            problems.append(f"{where}: unknown scan {scan}")
        elif norm(q) not in corpus[scan]:
            problems.append(f"{where}: quote not found in {scan}: {q[:90]!r}")

    for pid, p in data["people"].items():
        for f in p["facts"]:
            for s in f["sources"]:
                chk(s["scan"], s["quote"], pid)
        for e in p.get("excerpts", []):
            chk(e["scan"], e["text"], pid + " excerpt")
    for fam in data["families"]:
        for m in fam.get("marriage", []):
            for s in m["sources"]:
                chk(s["scan"], s["quote"], fam["id"])
        for x in fam["partners"] + fam["children"]:
            if x not in data["people"]:
                problems.append(f"{fam['id']}: unknown person {x}")
    return problems


# ----------------------------------------------------------------------------- data model
class Tree:
    def __init__(self, data):
        self.data = data
        self.people = data["people"]
        self.families = data["families"]
        self.line = data["line"]
        self.parents_of, self.families_of = {}, {}
        for fam in self.families:
            for c in fam["children"]:
                self.parents_of[c] = fam
            for x in fam["partners"]:
                self.families_of.setdefault(x, []).append(fam)
        for fams in self.families_of.values():
            fams.sort(key=lambda f: f.get("order", 1))

    def relation(self, pid):
        """How someone off the line connects to it, e.g. 'Son of Joseph Kastl'."""
        sex = self.people[pid].get("sex")
        pf = self.parents_of.get(pid)
        if pf:
            on = [x for x in pf["partners"] if x in self.line]
            if on:
                return f"{'Son' if sex == 'M' else 'Daughter'} of {self.people[on[0]]['name']}"
        for fam in self.families_of.get(pid, []):
            on = [x for x in fam["partners"] if x in self.line]
            if on:
                return f"{'Husband' if sex == 'M' else 'Wife'} of {self.people[on[0]]['name']}"
            for c in fam["children"]:
                for f2 in self.families_of.get(c, []):
                    on = [x for x in f2["partners"] if x in self.line and x != c]
                    if on:
                        return f"{'Father' if sex == 'M' else 'Mother'}-in-law of {self.people[on[0]]['name']}"
        return "Family of the line"

    def gen(self, pid):
        return self.line.index(pid) + 1 if pid in self.line else None

    def facts(self, pid, t):
        return [f for f in self.people[pid]["facts"] if f["type"] == t]

    def years(self, pid):
        def yrs(t):
            out = []
            for f in self.facts(pid, t):
                for y in re.findall(r"\b1[5-9]\d\d\b", f["value"]):
                    if y not in out:
                        out.append(y)
            return out
        b, d = yrs("birth"), yrs("death")
        bs = "/".join(b) if b else ""
        ds = "/".join(d) if d else ""
        if not bs and not ds:
            return ""
        if bs and not ds:
            return f"b. {bs}"
        if ds and not bs:
            return f"d. {ds}"
        return f"{bs}–{ds}"


# ----------------------------------------------------------------------------- layout
CSS_VERSION = "1"


def layout(prefix, title, body, *, description, path, active=""):
    full_title = f"{title} · {TITLE}" if title != TITLE else TITLE
    url = SITE_URL + path
    nav = [("index.html", "Line of descent", "home"), ("book/index.html", "The book", "book"),
           ("about/index.html", "About", "about")]
    links = "".join(
        f'<a href="{prefix}{h}"{CURRENT if k == active else ""}>{t}</a>'
        for h, t, k in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{SITE_URL}media/thumbs/s001.jpg">
<meta name="theme-color" content="#f4eee2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1b1814" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/site.css?v={CSS_VERSION}">
<script src="{prefix}assets/js/stats.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <div class="wrap head-inner">
    <a class="brand" href="{prefix}index.html"><span class="brand-mark" aria-hidden="true">K</span><span>Kastl Family History</span></a>
    <nav class="site-nav" aria-label="Main">{links}
      <form class="nav-search" action="{prefix}search/index.html" role="search">
        <label class="visually-hidden" for="q">Search</label>
        <input id="q" name="q" type="search" placeholder="Search names, places…" autocomplete="off">
      </form>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <p>Transcribed from <cite>Kastl Family History</cite> by Evelyn Coufal and Francis Vech (printed 1985, Catholic Quote, Valparaiso, Nebraska) and its 1986 Supplementary Section. Names, dates and spellings are given as the book prints them.</p>
    <p><a href="{prefix}about/index.html">About this site</a> · <a href="{prefix}book/index.html">Read the book</a> · <a href="{prefix}source/kastl-family-history-part1.pdf">PDF part 1</a> · <a href="{prefix}source/kastl-family-history-part2.pdf">PDF part 2</a></p>
  </div>
</footer>
</body>
</html>
"""


def write(rel_path, content):
    out = ROOT / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


# ----------------------------------------------------------------------------- sources
def src_link(scan, pages_by_scan, prefix, quote=None):
    p = pages_by_scan[scan]
    label = p["short"]
    if scan == "s016":
        label = "Chart, p. 14"
    href = f"{prefix}book/{p['slug']}/index.html"
    t = f' title="{esc(quote)}"' if quote else ""
    return f'<a class="src" href="{href}"{t}>{esc(label)}</a>'


def sources_block(sources, pages_by_scan, prefix):
    links = []
    seen = set()
    for s in sources:
        if s["scan"] not in seen:
            seen.add(s["scan"])
            links.append(src_link(s["scan"], pages_by_scan, prefix))
    quotes = "".join(
        f'<li><q>{inline(s["quote"])}</q> <span class="q-src">— {src_link(s["scan"], pages_by_scan, prefix)}</span></li>'
        for s in sources)
    return (f'<span class="srcs">{" ".join(links)}</span>'
            f'<details class="printed"><summary>As printed</summary><ul>{quotes}</ul></details>')


# ----------------------------------------------------------------------------- person pages
def person_link(tree, pid, prefix, cls=""):
    p = tree.people[pid]
    yrs = tree.years(pid)
    c = f' class="{cls}"' if cls else ""
    y = f' <span class="yrs">{esc(yrs)}</span>' if yrs else ""
    return f'<a{c} href="{prefix}people/{pid}/index.html">{esc(p["name"])}</a>{y}'


def build_person(tree, pid, pages_by_scan, root_name):
    prefix = "../../"
    p = tree.people[pid]
    gen = tree.gen(pid)
    parts = []

    # heading
    kicker = (f"Generation {gen} of {len(tree.line)} · the line of {esc(root_name)}" if gen
              else esc(tree.relation(pid)))
    if p.get("uncertain"):
        kicker += " · existence unconfirmed"
    parts.append(f'<p class="kicker">{kicker}</p>')
    parts.append(f'<h1>{esc(p["name"])}</h1>')
    yrs = tree.years(pid)
    if yrs:
        parts.append(f'<p class="lede-years">{esc(yrs)}</p>')

    # line navigation
    if gen:
        prev_id = tree.line[gen - 2] if gen > 1 else None
        next_id = tree.line[gen] if gen < len(tree.line) else None
        nav = []
        if prev_id:
            nav.append(f'<a class="ln-prev" href="{prefix}people/{prev_id}/index.html">↑ {esc(tree.people[prev_id]["name"])}<small>previous generation</small></a>')
        if next_id:
            nav.append(f'<a class="ln-next" href="{prefix}people/{next_id}/index.html">↓ {esc(tree.people[next_id]["name"])}<small>next generation</small></a>')
        parts.append(f'<nav class="line-nav" aria-label="Line of descent">{"".join(nav)}</nav>')

    # photos
    photos = []
    photo_index = {ph["id"]: (ph, pg) for pg in pages_by_scan.values() for ph in pg["photos"]}
    for ph_id in p.get("photos", []):
        ph, pg = photo_index[ph_id]
        fig = figure(ph, prefix, link=f"{prefix}book/{pg['slug']}/index.html")
        photos.append(fig.replace("</figure>", f'<p class="fig-src">{src_link(pg["scan"], pages_by_scan, prefix)}</p></figure>'))
    body_cols = []

    # facts
    rows = []
    by_type = {}
    for f in p["facts"]:
        by_type.setdefault(f["type"], []).append(f)
    for t in FACT_ORDER:
        fs = by_type.get(t, [])
        if not fs:
            continue
        numbered = all(f["value"].startswith("(") for f in fs)
        differs = t in CONFLICT_TYPES and len(fs) > 1 and not numbered
        for i, f in enumerate(fs):
            label = FACT_LABELS[t] if i == 0 else ""
            flag = ""
            if differs and i == 0:
                flag = '<span class="differs">The sources differ</span>'
            rows.append(
                f'<tr{DIFFERS_ROW if differs else ""}><th scope="row">{label}{flag}</th>'
                f'<td><span class="fact">{inline(f["value"])}</span>{sources_block(f["sources"], pages_by_scan, prefix)}</td></tr>')
    body_cols.append(f'<section class="facts" aria-labelledby="facts-h"><h2 id="facts-h">What the book records</h2>'
                     f'<table class="fact-table"><tbody>{"".join(rows)}</tbody></table></section>')

    # family
    fam_html = []
    pf = tree.parents_of.get(pid)
    if pf:
        par = " and ".join(person_link(tree, x, prefix) for x in pf["partners"])
        fam_html.append(f'<h3>Parents</h3><p>{par}</p>')
    for fam in tree.families_of.get(pid, []):
        other = [x for x in fam["partners"] if x != pid]
        heading = "Spouse" if len(tree.families_of[pid]) == 1 else ("First wife" if fam.get("order") == 1 else "Second wife")
        sp = " ".join(person_link(tree, x, prefix) for x in other)
        m = ""
        if fam.get("marriage"):
            m = "".join(
                f'<p class="marr">Married {inline(mm["value"])} {sources_block(mm["sources"], pages_by_scan, prefix)}</p>'
                for mm in fam["marriage"])
        kids = []
        for c in fam["children"]:
            on_line = c in tree.line
            kids.append(f'<li{ON_LINE_LI if on_line else ""}>{person_link(tree, c, prefix)}'
                        f'{LINE_TAG if on_line else ""}</li>')
        note = f'<p class="note">{esc(fam["note"])}</p>' if fam.get("note") else ""
        fam_html.append(f'<h3>{heading}</h3><p>{sp}</p>{m}<h3>Children</h3><ol class="kids">{"".join(kids)}</ol>{note}')
    if p.get("continues"):
        links = ", ".join(src_link(s, pages_by_scan, prefix) for s in p["continues"])
        fam_html.append(f'<p class="continues">This family’s descendants are listed in the book: {links}. '
                        f'They are not yet built out as separate pages.</p>')
    if p.get("chapter"):
        fam_html.append(f'<p class="continues">Read the chapter in the book: {src_link(p["chapter"], pages_by_scan, prefix)}.</p>')
    if fam_html:
        body_cols.append(f'<section class="family" aria-labelledby="fam-h"><h2 id="fam-h">Family</h2>{"".join(fam_html)}</section>')

    # excerpts
    if p.get("excerpts"):
        ex = "".join(
            f'<blockquote class="excerpt">{render_md(e["text"], [], prefix)}<footer>{src_link(e["scan"], pages_by_scan, prefix)}</footer></blockquote>'
            for e in p["excerpts"])
        body_cols.append(f'<section class="excerpts" aria-labelledby="ex-h"><h2 id="ex-h">From the book</h2>{ex}</section>')

    photo_html = f'<div class="person-photos">{"".join(photos)}</div>' if photos else ""
    content = f'<article class="wrap person">{"".join(parts)}{photo_html}{"".join(body_cols)}</article>'
    desc_bits = [p["name"], yrs] + [f["value"] for f in tree.facts(pid, "birth")[:1]]
    desc = f'{p["name"]} ({yrs}) in Kastl Family History.' if yrs else f'{p["name"]} in Kastl Family History.'
    write(f"people/{pid}/index.html",
          layout(prefix, p["name"], content, description=desc, path=f"people/{pid}/", active="home"))


# ----------------------------------------------------------------------------- home
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def short_fact(tree, pid, t):
    fs = tree.facts(pid, t)
    if not fs:
        return ""
    vals = []
    for f in fs:
        if f["value"] not in vals:
            vals.append(f["value"])
    return vals[0] + (" (sources differ)" if len(vals) > 1 and t in CONFLICT_TYPES else "")


def build_home(tree, pages_by_scan):
    prefix = ""
    root = tree.people[tree.data["root"]]
    cards = []
    for i, pid in enumerate(tree.line):
        p = tree.people[pid]
        born = short_fact(tree, pid, "birth")
        died = short_fact(tree, pid, "death")
        vit = []
        if born:
            vit.append(f"<span>Born {inline(born)}</span>")
        if died:
            vit.append(f"<span>Died {inline(died)}</span>")
        fams = []
        for fam in tree.families_of.get(pid, []):
            other = [x for x in fam["partners"] if x != pid]
            m = fam.get("marriage", [{}])[0].get("value", "")
            sp = ", ".join(f'<a href="people/{x}/index.html">{esc(tree.people[x]["name"])}</a>' for x in other)
            kids = []
            for c in fam["children"]:
                cls = "chip on-line" if c in tree.line else "chip"
                yr = tree.years(c)
                kids.append(f'<a class="{cls}" href="people/{c}/index.html">{esc(tree.people[c]["name"].split(" ")[0])}'
                            f'{f"<small>{esc(yr)}</small>" if yr else ""}</a>')
            fams.append(
                f'<div class="gen-fam"><p class="gen-spouse">m. {sp}{marr_span(m)}</p>'
                + (f'<div class="chips" aria-label="Children">{"".join(kids)}</div>' if kids else "") + "</div>")
        cards.append(f"""<li class="gen" id="gen-{i + 1}">
  <div class="gen-num" aria-hidden="true">{ROMAN[i]}</div>
  <div class="gen-card">
    <p class="gen-label">Generation {i + 1}</p>
    <h3><a href="people/{pid}/index.html">{esc(p["name"])}</a> <span class="yrs">{esc(tree.years(pid))}</span></h3>
    <p class="gen-vitals">{" ".join(vit)}</p>
    {"".join(fams)}
  </div>
</li>""")
    crumbs = "".join(
        f'<li><a href="#gen-{i + 1}">{esc(tree.people[pid]["name"].split(" ")[0])}</a></li>'
        for i, pid in enumerate(tree.line))
    body = f"""<section class="hero">
  <div class="wrap hero-inner">
    <div>
      <p class="kicker">From Bohemia to Nebraska</p>
      <h1>The Kastl Family History</h1>
      <p class="lede">A family history compiled by Evelyn Coufal and Francis Vech, printed in 1985, with a supplement in 1986. It follows the seven Kastl brothers who left Bohemia for America in the 1860s and 1870s, and their descendants.</p>
      <p class="lede">This site begins with one thread through the book: the line from the earliest recorded Kastl, Andreas, down to {esc(root["name"])}, born in 1983.</p>
      <p class="hero-links"><a class="btn" href="#line">Follow the line</a> <a class="btn ghost" href="book/index.html">Read the book</a></p>
    </div>
    <a class="hero-cover" href="book/cover/index.html"><img src="media/pages/s001.jpg" alt="The book's cover: a sailing ship, its sails lettered Kastl Family History" width="{jpeg_size(ROOT / 'media/pages/s001.jpg')[0]}" height="{jpeg_size(ROOT / 'media/pages/s001.jpg')[1]}"></a>
  </div>
</section>
<section class="wrap" id="line" aria-labelledby="line-h">
  <div class="section-head">
    <h2 id="line-h">The line of descent</h2>
    <button class="btn ghost small" type="button" id="flip" aria-pressed="false">Start from {esc(root["name"].split(" ")[0])}</button>
  </div>
  <p class="muted">Ten generations, father to son. Each card shows the couple and their children as the book lists them; the child who carries the line is marked. Open anyone for every recorded fact and the page it comes from.</p>
  <ol class="crumbs" aria-label="Generations">{crumbs}</ol>
  <ol class="generations" id="generations">
{"".join(cards)}
  </ol>
</section>
<script>
(function(){{var b=document.getElementById('flip'),l=document.getElementById('generations');
if(!b||!l)return;b.addEventListener('click',function(){{var on=b.getAttribute('aria-pressed')!=='true';
b.setAttribute('aria-pressed',on);l.classList.toggle('reversed',on);
b.textContent=on?'Start from Andreas':'Start from {esc(root["name"].split(" ")[0])}';
Array.prototype.slice.call(l.children).reverse().forEach(function(c){{l.appendChild(c);}});}});}})();
</script>"""
    write("index.html", layout(prefix, TITLE, body,
                               description="Explore Kastl Family History (1985): the Kastl family from Bohemia to Nebraska, with page scans, transcriptions and the line of descent.",
                               path="", active="home"))


# ----------------------------------------------------------------------------- book
SECTIONS = [  # (first scan, title) — from the book's own contents page (s003)
    ("s001", "Front matter"), ("s004", "Preface"), ("s005", "How to Use the Book"),
    ("s006", "A Brief History of Czechoslovakia (Bohemia/Moravia)"),
    ("s009", "The Kastls: from Bohemia to America"), ("s012", "The Kastls: in Pioneer Nebraska"),
    ("s015", "The Kastls: in California and Oklahoma; Newspaper Items in the 1890s"),
    ("s016", "Ancestral Chart"), ("s017", "The Family of Peter Kastl"),
    ("s028", "The Family of Wenzel Kastl"), ("s030", "The Family of John Kastl"),
    ("s043", "The Family of Joseph Kastl"), ("s046", "The Family of Jacob Kastl"),
    ("s058", "The Family of Thomas Kastl"), ("s059", "The Family of Andrew Kastl"),
    ("s064", "Second Marriage of Thomas Kastl; The Family of Anna Kastl Zima"),
    ("s065", "And in Conclusion"), ("s067", "Back matter"),
    ("s069", "Supplementary Section (1986)"),
]


def section_of(scan):
    cur = SECTIONS[0][1]
    for s, t in SECTIONS:
        if scan >= s:
            cur = t
    return cur


def people_on_page(tree):
    on = {}
    for pid, p in tree.people.items():
        for f in p["facts"]:
            for s in f["sources"]:
                on.setdefault(s["scan"], [])
                if pid not in on[s["scan"]]:
                    on[s["scan"]].append(pid)
    return on


def build_book(tree, pages, pages_by_scan):
    on_page = people_on_page(tree)
    # index
    prefix = "../"
    groups = []
    for i, (start, title) in enumerate(SECTIONS):
        end = SECTIONS[i + 1][0] if i + 1 < len(SECTIONS) else "s999"
        ps = [p for p in pages if start <= p["scan"] < end]
        tiles = "".join(
            f'<li><a href="{p["slug"]}/index.html"><img src="{prefix}media/thumbs/{p["scan"]}.jpg" alt="" width="{jpeg_size(ROOT / "media/thumbs" / (p["scan"] + ".jpg"))[0]}" height="{jpeg_size(ROOT / "media/thumbs" / (p["scan"] + ".jpg"))[1]}" loading="lazy"><span>{esc(p["short"])}</span></a></li>'
            for p in ps)
        groups.append(f'<section class="toc-sec"><h2><a href="{ps[0]["slug"]}/index.html">{esc(title)}</a></h2><ol class="thumbs">{tiles}</ol></section>')
    body = f"""<div class="wrap book-index">
<p class="kicker">The book</p>
<h1>Kastl Family History</h1>
<p class="lede">All 76 scanned pages of the 1985 book and its 1986 Supplementary Section, each shown beside a faithful transcription. Sections follow the book’s own contents page.</p>
<p><a class="btn ghost small" href="{prefix}source/kastl-family-history-part1.pdf">Download scans, part 1 (PDF, 28 MB)</a> <a class="btn ghost small" href="{prefix}source/kastl-family-history-part2.pdf">Part 2 (PDF, 27 MB)</a></p>
{"".join(groups)}
</div>"""
    write("book/index.html", layout(prefix, "The book", body,
                                    description="Read every page of Kastl Family History (1985) and its 1986 supplement: page scans with transcriptions.",
                                    path="book/", active="book"))

    # each page
    prefix = "../../"
    for i, p in enumerate(pages):
        prev_p = pages[i - 1] if i > 0 else None
        next_p = pages[i + 1] if i + 1 < len(pages) else None
        title = page_title(p)
        w, h = jpeg_size(ROOT / "media/pages" / f"{p['scan']}.jpg")
        img_src = f"{prefix}media/pages/{p['scan']}.jpg"
        trans = render_md(p["body"], p["photos"], prefix) if p["body"].strip() else '<p class="muted">No printed text on this page.</p>'
        meta_bits = []
        if p.get("inferred_page"):
            meta_bits.append("The page number is not printed; it is inferred from the page’s position.")
        if p["continues_from_previous"]:
            meta_bits.append("The text at the top continues from the previous page.")
        if p["continues_to_next"]:
            meta_bits.append("The text at the bottom continues on the next page.")
        ppl = on_page.get(p["scan"], [])
        ppl_html = ""
        if ppl:
            ppl_html = ('<section class="on-page"><h2>People from the line of descent on this page</h2><ul>'
                        + "".join(f"<li>{person_link(tree, x, prefix)}</li>" for x in ppl) + "</ul></section>")
        notes = ""
        if p.get("notes"):
            notes += f'<details class="tnotes"><summary>Transcriber’s notes</summary><p>{inline(p["notes"])}</p></details>'
        if p.get("annotations"):
            notes += ('<details class="tnotes"><summary>Library stamps and handwriting (not part of the book)</summary><ul>'
                      + "".join(f"<li>{inline(a)}</li>" for a in p["annotations"]) + "</ul></details>")
        pager = ('<nav class="pager" aria-label="Pages">'
                 + (f'<a rel="prev" href="../{prev_p["slug"]}/index.html">← {esc(prev_p["short"])}</a>' if prev_p else "<span></span>")
                 + f'<a href="../index.html">All pages</a>'
                 + (f'<a rel="next" href="../{next_p["slug"]}/index.html">{esc(next_p["short"])} →</a>' if next_p else "<span></span>")
                 + "</nav>")
        source_line = ("1986 Supplementary Section" if p["supplement"] else "1985 book")
        body = f"""<div class="wrap reader">
<p class="kicker"><a href="../index.html">The book</a> · {esc(section_of(p["scan"]))}</p>
<h1>{esc(p["label"])}{f' <span class="h-sub">{esc(title)}</span>' if title and title != p["label"] else ""}</h1>
{pager}
<div class="spread">
  <figure class="scan">
    <a href="{img_src}" title="Open the full-size scan"><img src="{img_src}" alt="Scan of {esc(p["label"])}, {esc(source_line)}" width="{w}" height="{h}"></a>
    <figcaption>Scan {p["scan"][1:]} · {esc(source_line)} · <a href="{img_src}">full size</a></figcaption>
  </figure>
  <div class="transcription">
    <p class="t-label">Transcription</p>
    {"".join(f'<p class="t-meta">{esc(b)}</p>' for b in meta_bits)}
    {trans}
    {ppl_html}
    {notes}
  </div>
</div>
{pager}
</div>"""
        desc = f"{p['label']} of Kastl Family History" + (f": {title}." if title else ".")
        write(f"book/{p['slug']}/index.html",
              layout(prefix, f"{p['label']}{' — ' + title if title and title != p['label'] else ''}", body,
                     description=desc, path=f"book/{p['slug']}/", active="book"))


# ----------------------------------------------------------------------------- about + search
def build_about(tree):
    prefix = "../"
    n_people = len(tree.people)
    body = f"""<article class="wrap prose">
<p class="kicker">About</p>
<h1>About this site</h1>
<p class="lede"><cite>Kastl Family History</cite> was compiled by Evelyn Coufal and Francis Vech and printed in 1985 by Catholic Quote of Valparaiso, Nebraska. A Supplementary Section followed in 1986. This site presents the book page by page, and draws out one line of descent from it as linked family records.</p>

<h2>What is here</h2>
<ul>
<li><a href="{prefix}book/index.html">The book</a>: all 76 scanned pages, each beside a transcription of its text.</li>
<li><a href="{prefix}index.html#line">The line of descent</a>: ten generations from Andreas Kastl to {esc(tree.people[tree.data["root"]]["name"])}, with spouses, children and the parents of spouses — {n_people} people so far. The rest of the book’s families will follow.</li>
</ul>

<h2>How it was made</h2>
<ol>
<li>The scans come from a microfilm copy held by the Family History Library; its library stamps and handwritten call numbers appear on a few pages and are noted separately from the book’s own text.</li>
<li>Every page was transcribed from the images, then proofread a second time, independently, against the images. Names, dates and numbers were also cross-checked against the scan’s machine-read text.</li>
<li>Each fact on a person’s page is tied to the page it comes from, with the exact words the book uses under “As printed”. The site is rebuilt only if every one of those quotations still appears, word for word, in the transcription.</li>
</ol>

<h2>Reading conventions</h2>
<ul>
<li><strong>Spellings are the book’s own.</strong> The authors wrote that “no attempt has been made to standardize the spelling of names”: Josef and Joseph, Jan and John, Marsalek and Marselek all appear. Typing slips are kept too, marked <span class="sic">[sic]</span> where they might look like transcription errors.</li>
<li><strong>When the book disagrees with itself</strong>, every version is shown with its source, marked “The sources differ”. The 1986 Supplement often corrects the 1985 pages; both readings are kept.</li>
<li><span class="unsure">[?]</span> marks a reading that the scan does not make certain.</li>
<li>Nothing has been added from outside the book.</li>
</ul>

<h2>The book’s own words</h2>
<blockquote class="excerpt"><p>It is hoped that most of the information here is correct, or nearly so. Apologies are made for any errors, omissions, or inconsistencies.</p><footer>Preface, <a class="src" href="{prefix}book/p2/index.html">p. 2</a></footer></blockquote>
</article>"""
    write("about/index.html", layout(prefix, "About", body,
                                     description="About this edition of Kastl Family History: sources, transcription and reading conventions.",
                                     path="about/", active="about"))


def build_search(tree, pages):
    prefix = "../"
    index = {
        "people": [{"id": pid, "n": p["name"], "y": tree.years(pid),
                    "t": " ".join([p["name"]] + [f["value"] for f in p["facts"]])} for pid, p in tree.people.items()],
        "pages": [{"s": p["slug"], "l": p["label"], "h": page_title(p),
                   "t": strip_md(re.sub(r"\[\[photo [^\]]+\]\]", "", p["body"])) + " " +
                        " ".join((ph.get("caption") or "") for ph in p["photos"])} for p in pages],
    }
    write("search/index.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))
    body = f"""<div class="wrap search">
<p class="kicker">Search</p>
<h1>Search the book</h1>
<form class="search-form" role="search" action="index.html">
  <label class="visually-hidden" for="sq">Search</label>
  <input id="sq" name="q" type="search" placeholder="A name, a place, a year…" autocomplete="off" autofocus>
  <button class="btn" type="submit">Search</button>
</form>
<p class="muted" id="search-status" aria-live="polite"></p>
<div id="results"></div>
</div>
<script src="{prefix}assets/js/search.js" defer></script>"""
    write("search/index.html", layout(prefix, "Search", body,
                                      description="Search the transcribed text of Kastl Family History.",
                                      path="search/"))


# ----------------------------------------------------------------------------- main
def main():
    pages = load_pages()
    pages_by_scan = {p["scan"]: p for p in pages}
    data = json.loads((CONTENT / "people.json").read_text(encoding="utf-8"))
    problems = check_quotes(data, pages_by_scan)
    if problems:
        print("Quote check failed:", *problems, sep="\n  ")
        sys.exit(1)
    tree = Tree(data)
    root_name = tree.people[data["root"]]["name"]
    for d in ("people", "book"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    for pid in tree.people:
        build_person(tree, pid, pages_by_scan, root_name)
    build_home(tree, pages_by_scan)
    build_book(tree, pages, pages_by_scan)
    build_about(tree)
    build_search(tree, pages)
    nq = (sum(len(f["sources"]) for p in data["people"].values() for f in p["facts"])
          + sum(len(p.get("excerpts", [])) for p in data["people"].values())
          + sum(len(m["sources"]) for fam in data["families"] for m in fam.get("marriage", [])))
    print(f"Built {len(tree.people)} people, {len(pages)} book pages; {nq} cited quotes verified.")


if __name__ == "__main__":
    main()
