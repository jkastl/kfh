#!/usr/bin/env python3
"""Build the Kastl Family History site.

Standard library only. Reads content/pages/*.md and content/people/*.json, writes static HTML
into the repo root (index.html, people/, tree/, book/, about/, search/). Fails if any quoted fact
does not appear verbatim in the transcription of the page it cites.

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
DIFFERS_DOT = ' <span class="differs-dot" title="The sources differ on a fact">≠</span>'


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
BRANCHES = [  # (branch key, founder id, label) in the book's chapter order
    ("peter", "peter-kastl-1827", "Peter"),
    ("wenzel", "wenzel-kastl-1831", "Wenzel"),
    ("john", "john-kastl-1835", "John"),
    ("josef", "josef-kastl-1840", "Josef"),
    ("jacob", "jacob-kastl-1847", "Jacob"),
    ("thomas", "thomas-kastl-1850", "Thomas"),
    ("andrew", "andrew-kastl-1853", "Andrew"),
    ("zima", "anna-kastl-1865", "Anna Kastl Zima"),
]
BRANCH_LABEL = {k: lbl for k, _, lbl in BRANCHES}
BRANCH_LABEL["roots"] = "Shared roots"
FATHER_OF_BROTHERS = "thomas-kastl-1806"
MOTHER_OF_BROTHERS = "maria-marsalek"
TREE_ROOT = "andreas-kastl"


def load_people():
    """Merge content/people/*.json. Ids must be unique across files."""
    people, families = {}, []
    for f in sorted((CONTENT / "people").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for pid, p in d.get("people", {}).items():
            if pid in people:
                sys.exit(f"Duplicate person id {pid} in {f.name}")
            people[pid] = p
        families.extend(d.get("families", []))
    return {"people": people, "families": families}


def kin(n, sex, down):
    """Kinship word n generations away: kin(1,'M',True)='Son', kin(3,'F',False)='Great-grandmother'."""
    base = ("Son" if sex == "M" else "Daughter") if down else ("Father" if sex == "M" else "Mother")
    if n == 1:
        return base
    grand = "grand" + base.lower()
    if n == 2:
        return grand[0].upper() + grand[1:]
    if n == 3:
        return "Great-" + grand
    return f"{n - 2}× great-{grand}"


class Tree:
    def __init__(self, data):
        self.data = data
        self.people = data["people"]
        self.families = data["families"]
        self.parents_of, self.families_of = {}, {}
        for fam in self.families:
            for c in fam["children"]:
                self.parents_of[c] = fam
            for x in fam["partners"]:
                self.families_of.setdefault(x, []).append(fam)
        for fams in self.families_of.values():
            fams.sort(key=lambda f: f.get("order", 1))
        self.founders = {fid: key for key, fid, _ in BRANCHES}
        self._chain = {}

    # --- descent
    def blood_parent(self, pid):
        """The parent through whom pid descends from Andreas (the Kastl side), if any."""
        fam = self.parents_of.get(pid)
        if not fam:
            return None
        for x in fam["partners"]:
            if x == TREE_ROOT or x in self.parents_of:
                return x
        return fam["partners"][0]

    def chain(self, pid):
        """Ancestors from the tree root down to pid, following the Kastl-side parent."""
        if pid not in self._chain:
            out, cur = [pid], pid
            while True:
                bp = self.blood_parent(cur)
                if not bp:
                    break
                out.append(bp)
                cur = bp
            self._chain[pid] = list(reversed(out))
        return self._chain[pid]

    def is_blood(self, pid):
        return self.chain(pid)[0] == TREE_ROOT

    def spouses(self, pid):
        out = []
        for fam in self.families_of.get(pid, []):
            out += [x for x in fam["partners"] if x != pid]
        return out

    def anchor(self, pid):
        """For married-in people, the blood relative they married (first one)."""
        if self.is_blood(pid):
            return pid
        for s in self.spouses(pid):
            if self.is_blood(s):
                return s
        return None

    def branch(self, pid):
        return self.people[pid].get("branch", "roots")

    def generation(self, pid):
        """Generations below the brothers (a brother = 1); None above or outside."""
        a = self.anchor(pid)
        if not a:
            return None
        ch = self.chain(a)
        for i, x in enumerate(ch):
            if x in self.founders:
                return len(ch) - i
        return None

    def up_from_brothers(self, pid, _seen=None):
        """Generations above the seven brothers through either parent (their parents = 1), else None."""
        if pid in self.founders and pid != "anna-kastl-1865":
            return 0
        best = None
        for fam in self.families_of.get(pid, []):
            for c in fam["children"]:
                k = self.up_from_brothers(c)
                if k is not None and (best is None or k + 1 < best):
                    best = k + 1
        return best

    def relation(self, pid):
        p = self.people[pid]
        sex = p.get("sex")
        if pid in self.founders:
            if pid == "anna-kastl-1865":
                return "Half-sister of the seven brothers"
            return "One of the seven brothers"
        n = self.up_from_brothers(pid)
        if n:
            return f"{kin(n, sex, False)} of the seven brothers"
        if self.is_blood(pid):
            ch = self.chain(pid)
            for i, x in enumerate(ch):
                if x in self.founders:
                    return f"{kin(len(ch) - 1 - i, sex, True)} of {self.people[x]['name']}"
            fam = self.parents_of.get(pid)
            if fam and FATHER_OF_BROTHERS in fam["partners"]:
                if MOTHER_OF_BROTHERS in fam["partners"]:
                    return ("Brother" if sex == "M" else "Sister") + " of the seven brothers"
                return ("Half-brother" if sex == "M" else "Half-sister") + " of the seven brothers"
        for s in self.spouses(pid):
            if s == FATHER_OF_BROTHERS:
                return "Second wife of Thomas Kastl"
            if self.is_blood(s):
                return f"{'Husband' if sex == 'M' else 'Wife'} of {self.people[s]['name']}"
        for fam in self.families_of.get(pid, []):
            for c in fam["children"]:
                return f"{'Father' if sex == 'M' else 'Mother'} of {self.people[c]['name']}"
        return ""

    def facts(self, pid, t):
        return [f for f in self.people[pid]["facts"] if f["type"] == t]

    def year_list(self, pid, t):
        out = []
        for f in self.facts(pid, t):
            for y in re.findall(r"\b1[5-9]\d\d\b", f["value"]):
                if y not in out:
                    out.append(y)
        return out

    def years(self, pid):
        b, d = self.year_list(pid, "birth"), self.year_list(pid, "death")
        bs, ds = "/".join(b), "/".join(d)
        if not bs and not ds:
            return ""
        if bs and not ds:
            return f"b. {bs}"
        if ds and not bs:
            return f"d. {ds}"
        return f"{bs}–{ds}"

    def has_conflict(self, pid):
        by = {}
        for f in self.people[pid]["facts"]:
            by.setdefault(f["type"], []).append(f)
        return any(t in CONFLICT_TYPES and len(fs) > 1 and not all(f["value"].startswith("(") for f in fs)
                   for t, fs in by.items())

    def descendants(self, pid):
        out = []
        for fam in self.families_of.get(pid, []):
            for c in fam["children"]:
                out.append(c)
                out += self.descendants(c)
        return out


def short_fact(tree, pid, t):
    fs = tree.facts(pid, t)
    if not fs:
        return ""
    vals = []
    for f in fs:
        if f["value"] not in vals:
            vals.append(f["value"])
    return vals[0] + (" (sources differ)" if len(vals) > 1 and t in CONFLICT_TYPES else "")


# ----------------------------------------------------------------------------- layout
CSS_VERSION = "3"
PDFS = [("source/kastl-family-history-part1.pdf", "Scans, part 1", "PDF, 28 MB"),
        ("source/kastl-family-history-part2.pdf", "Scans, part 2", "PDF, 27 MB")]


def pdf_links(prefix, cls=""):
    c = f' class="{cls}"' if cls else ""
    return " ".join(
        f'<a{c} href="{prefix}{href}" target="_blank" rel="noopener" title="Opens in a new tab">{label} <span class="muted">({size})</span><span class="visually-hidden"> (opens in a new tab)</span> <span aria-hidden="true">↗</span></a>'
        for href, label, size in PDFS)


def layout(prefix, title, body, *, description, path, active=""):
    full_title = f"{title} · {TITLE}" if title != TITLE else TITLE
    url = SITE_URL + path
    nav = [("tree/index.html", "Family tree", "tree"), ("people/index.html", "People", "people"),
           ("book/index.html", "The book", "book"), ("about/index.html", "About", "about")]
    links = "".join(
        f'<a href="{prefix}{h}"{CURRENT if k == active else ""}>{t}</a>' for h, t, k in nav)
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
    <p><a href="{prefix}about/index.html">About this site</a> · <a href="{prefix}book/index.html">Read the book</a> · {pdf_links(prefix)}</p>
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


def descent_html(tree, pid, prefix):
    a = tree.anchor(pid)
    if not a:
        return ""
    ch = tree.chain(a)
    if len(ch) < 2 and a == pid:
        return ""
    items = []
    for x in ch:
        name = esc(tree.people[x]["name"])
        if x == pid:
            items.append(f'<li aria-current="page"><span>{name}</span></li>')
        else:
            cls = ' class="founder"' if x in tree.founders else ""
            items.append(f'<li{cls}><a href="{prefix}people/{x}/index.html">{name}</a></li>')
    lead = "Descent" if a == pid else f"Married into the family · descent of {esc(tree.people[a]['name'])}"
    if a != pid:
        items.append(f'<li aria-current="page"><span>{esc(tree.people[pid]["name"])}</span></li>')
    return (f'<nav class="descent" aria-label="Line of descent"><p class="descent-h">{lead}</p>'
            f'<ol>{"".join(items)}</ol></nav>')


def build_person(tree, pid, pages_by_scan):
    prefix = "../../"
    p = tree.people[pid]
    parts = []
    br = tree.branch(pid)
    rel = tree.relation(pid)
    bits = [esc(rel)] if rel else []
    if br in BRANCH_LABEL and br != "roots":
        bits.append(f'<a href="{prefix}tree/index.html?focus={pid}">{esc(BRANCH_LABEL[br])}’s branch</a>')
    if p.get("uncertain"):
        bits.append("existence unconfirmed")
    parts.append(f'<p class="kicker">{" · ".join(bits)}</p>')
    parts.append(f'<h1>{esc(p["name"])}</h1>')
    yrs = tree.years(pid)
    if yrs:
        parts.append(f'<p class="lede-years">{esc(yrs)}</p>')
    parts.append(descent_html(tree, pid, prefix))
    parts.append(f'<p class="person-tools"><a class="btn ghost small" href="{prefix}tree/index.html?focus={pid}">Show in the family tree</a></p>')

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
            flag = '<span class="differs">The sources differ</span>' if differs and i == 0 else ""
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
    fams = tree.families_of.get(pid, [])
    for fam in fams:
        other = [x for x in fam["partners"] if x != pid]
        if len(fams) == 1:
            heading = "Spouse"
        else:
            heading = {1: "First marriage", 2: "Second marriage", 3: "Third marriage"}.get(fam.get("order", 1), "Marriage")
        sp = " ".join(person_link(tree, x, prefix) for x in other)
        m = "".join(
            f'<p class="marr">Married {inline(mm["value"])} {sources_block(mm["sources"], pages_by_scan, prefix)}</p>'
            for mm in fam.get("marriage", []))
        kids = "".join(f"<li>{person_link(tree, c, prefix)}</li>" for c in fam["children"])
        note = f'<p class="note">{esc(fam["note"])}</p>' if fam.get("note") else ""
        kids_html = f'<h3>Children</h3><ol class="kids">{kids}</ol>' if kids else ""
        fam_html.append(f'<h3>{heading}</h3><p>{sp}</p>{m}{kids_html}{note}')
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
    desc = (f'{p["name"]} ({yrs}), {rel.lower() if rel else "of the Kastl family"}, in Kastl Family History.')
    write(f"people/{pid}/index.html",
          layout(prefix, p["name"], content, description=desc, path=f"people/{pid}/", active="people"))


# ----------------------------------------------------------------------------- home
def build_home(tree, pages_by_scan):
    roots = tree.chain(FATHER_OF_BROTHERS)
    root_strip = "".join(
        f'<li><a href="people/{x}/index.html">{esc(tree.people[x]["name"])}</a> <span class="yrs">{esc(tree.years(x))}</span></li>'
        for x in roots)
    cards = []
    for key, fid, label in BRANCHES:
        p = tree.people[fid]
        born = short_fact(tree, fid, "birth")
        arrived = short_fact(tree, fid, "immigration")
        died = short_fact(tree, fid, "death")
        marr = [f["value"] for f in tree.facts(fid, "marriage")]
        n_desc = len(set(tree.descendants(fid)))
        built = n_desc > 0
        rows = []
        if born:
            rows.append(f"<dt>Born</dt><dd>{inline(born)}</dd>")
        if marr:
            rows.append(f"<dt>Married</dt><dd>{inline('; '.join(marr))}</dd>")
        if arrived:
            rows.append(f"<dt>Came to America</dt><dd>{inline(arrived)}</dd>")
        if died:
            rows.append(f"<dt>Died</dt><dd>{inline(died)}</dd>")
        chap = pages_by_scan[p["chapter"]] if p.get("chapter") else None
        links = [f'<a href="people/{fid}/index.html">About {esc(label if key != "zima" else "Anna")}</a>']
        if chap:
            links.append(f'<a href="book/{chap["slug"]}/index.html">Chapter, {esc(chap["short"])}</a>')
        links.append(f'<a href="tree/index.html?focus={fid}">In the tree</a>')
        status = (f'<p class="branch-status built">{n_desc} descendants recorded so far</p>' if built
                  else '<p class="branch-status">Family to be added — read it in the book for now</p>')
        kind = "Half-sister" if key == "zima" else "Brother"
        cards.append(f"""<li class="brother">
  <p class="gen-label">{kind}</p>
  <h3><a href="people/{fid}/index.html">{esc(p["name"])}</a> <span class="yrs">{esc(tree.years(fid))}</span></h3>
  <dl class="b-facts">{"".join(rows)}</dl>
  {status}
  <p class="b-links">{" · ".join(links)}</p>
</li>""")
    w, h = jpeg_size(ROOT / "media/pages/s001.jpg")
    body = f"""<section class="hero">
  <div class="wrap hero-inner">
    <div>
      <p class="kicker">From Bohemia to Nebraska</p>
      <h1>The Kastl Family History</h1>
      <p class="lede">In the 1860s and early 1870s, seven Kastl brothers — sons of Thomas Kastl, a farmer near Všepadly in Bohemia — left for America. Six made their homes in Nebraska; Thomas settled in Illinois. This is their family’s history, compiled by Evelyn Coufal and Francis Vech and printed in 1985, with a supplement in 1986.</p>
      <p class="hero-links"><a class="btn" href="#brothers">Meet the brothers</a> <a class="btn ghost" href="tree/index.html">Family tree</a> <a class="btn ghost" href="book/index.html">Read the book</a></p>
    </div>
    <a class="hero-cover" href="book/cover/index.html"><img src="media/pages/s001.jpg" alt="The book's cover: a sailing ship, its sails lettered Kastl Family History" width="{w}" height="{h}"></a>
  </div>
</section>
<section class="wrap" aria-labelledby="roots-h">
  <h2 id="roots-h">Shared roots</h2>
  <p class="muted">The earliest Kastls the book could trace, from church records in the archives at Plzen. Thomas married twice: Maria Marsalek, mother of the seven brothers, and after her death Barbara Kellner.</p>
  <ol class="roots">{root_strip}</ol>
</section>
<section class="wrap" id="brothers" aria-labelledby="brothers-h">
  <h2 id="brothers-h">The seven brothers</h2>
  <p class="muted">Each brother has his own chapter in the book. A half-sister, Anna, stayed in Bohemia; her son James Zima came to Nebraska in 1922.</p>
  <ol class="brothers">
{"".join(cards)}
  </ol>
</section>
<section class="wrap explore" aria-labelledby="explore-h">
  <h2 id="explore-h">Explore</h2>
  <ul class="explore-grid">
    <li><a href="tree/index.html"><strong>Family tree</strong><span>From Andreas Kastl down through every branch built so far.</span></a></li>
    <li><a href="people/index.html"><strong>Everyone, in a table</strong><span>Filter and sort by name, dates, branch; download as CSV.</span></a></li>
    <li><a href="book/index.html"><strong>The book, page by page</strong><span>All 76 scans beside their transcriptions.</span></a></li>
    <li><a href="search/index.html"><strong>Search</strong><span>Names, places and years across the whole book.</span></a></li>
  </ul>
</section>"""
    write("index.html", layout("", TITLE, body,
                               description="Kastl Family History (1985): seven Kastl brothers from Bohemia and their descendants in Nebraska — family tree, people and the full book with transcriptions.",
                               path=""))


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
<p class="pdf-links">{pdf_links(prefix)}</p>
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
<p class="lede"><cite>Kastl Family History</cite> was compiled by Evelyn Coufal and Francis Vech and printed in 1985 by Catholic Quote of Valparaiso, Nebraska. A Supplementary Section followed in 1986. This site presents the book page by page and is turning its family lists into linked records you can browse as a tree or a table.</p>

<h2>What is here</h2>
<ul>
<li><a href="{prefix}book/index.html">The book</a>: all 76 scanned pages, each beside a transcription of its text.</li>
<li><a href="{prefix}tree/index.html">The family tree</a> and <a href="{prefix}people/index.html">a table of everyone</a> — {n_people} people so far. The shared ancestors, the brothers and Josef Kastl’s descendants down to the youngest generation are in; the other branches are being added one at a time.</li>
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


# ----------------------------------------------------------------------------- people table
def person_row(tree, pid, pages_by_scan):
    p = tree.people[pid]
    born, died = short_fact(tree, pid, "birth"), short_fact(tree, pid, "death")
    by, dy = tree.year_list(pid, "birth"), tree.year_list(pid, "death")
    scans = []
    for f in p["facts"]:
        for s in f["sources"]:
            if s["scan"] not in scans:
                scans.append(s["scan"])
    scans.sort()
    gen = tree.generation(pid)
    return {
        "id": pid, "name": p["name"], "sex": p.get("sex", ""), "branch": tree.branch(pid),
        "relation": tree.relation(pid), "generation": gen if gen is not None else "",
        "born": born, "born_year": by[0] if by else "", "died": died, "died_year": dy[0] if dy else "",
        "spouses": "; ".join(tree.people[s]["name"] for s in tree.spouses(pid)),
        "parents": " and ".join(tree.people[x]["name"] for x in tree.parents_of[pid]["partners"]) if pid in tree.parents_of else "",
        "differs": tree.has_conflict(pid),
        "pages": ", ".join(pages_by_scan[s]["short"] for s in scans),
    }


def build_people_index(tree, pages_by_scan):
    import csv
    import io
    prefix = "../"
    order = sorted(tree.people, key=lambda x: (tree.people[x]["name"].split()[-1], tree.people[x]["name"]))
    rows = [person_row(tree, pid, pages_by_scan) for pid in order]
    # CSV
    buf = io.StringIO()
    cols = ["id", "name", "sex", "branch", "relation", "generation", "born", "died", "spouses", "parents", "pages"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    write("people/people.csv", buf.getvalue())
    branches = [("roots", "Shared roots")] + [(k, BRANCH_LABEL[k]) for k, _, _ in BRANCHES]
    opts = "".join(f'<option value="{k}">{esc(l)}</option>' for k, l in branches)
    trs = []
    for r in rows:
        trs.append(
            f'<tr data-branch="{r["branch"]}" data-differs="{1 if r["differs"] else 0}">'
            f'<td data-sort="{esc(r["name"].split()[-1] + " " + r["name"])}"><a href="{r["id"]}/index.html">{esc(r["name"])}</a>'
            f'{DIFFERS_DOT if r["differs"] else ""}</td>'
            f'<td data-sort="{r["born_year"] or 9999}">{inline(r["born"])}</td>'
            f'<td data-sort="{r["died_year"] or 9999}">{inline(r["died"])}</td>'
            f'<td>{esc(r["relation"])}</td>'
            f'<td data-sort="{r["generation"] if r["generation"] != "" else 99}">{r["generation"]}</td>'
            f'<td>{esc(BRANCH_LABEL.get(r["branch"], r["branch"]))}</td>'
            f'<td class="pages-col">{esc(r["pages"])}</td></tr>')
    body = f"""<div class="wrap people-index">
<p class="kicker">People</p>
<h1>Everyone in the book, so far</h1>
<p class="lede">{len(rows)} people. Filter by name, place or year; sort by any column. Dates are as the book prints them. <a href="people.csv" download>Download as CSV</a>.</p>
<form class="table-tools" id="tools" onsubmit="return false">
  <label>Filter <input type="search" id="f-text" placeholder="Name, place, year…" autocomplete="off"></label>
  <label>Branch <select id="f-branch"><option value="">All</option>{opts}</select></label>
  <label class="check"><input type="checkbox" id="f-differs"> Only where the sources differ</label>
  <span class="muted" id="f-count" aria-live="polite"></span>
</form>
<div class="table-scroll">
<table class="people-table" id="people">
<thead><tr>
  <th scope="col" aria-sort="ascending"><button type="button" data-col="0">Name</button></th>
  <th scope="col"><button type="button" data-col="1" data-num>Born</button></th>
  <th scope="col"><button type="button" data-col="2" data-num>Died</button></th>
  <th scope="col"><button type="button" data-col="3">Relationship</button></th>
  <th scope="col"><button type="button" data-col="4" data-num title="Generations below the seven brothers (a brother is 1)">Gen.</button></th>
  <th scope="col"><button type="button" data-col="5">Branch</button></th>
  <th scope="col">Pages</th>
</tr></thead>
<tbody>
{"".join(trs)}
</tbody>
</table>
</div>
</div>
<script src="{prefix}assets/js/table.js" defer></script>"""
    write("people/index.html", layout(prefix, "People", body,
                                      description="Everyone recorded so far from Kastl Family History, in a filterable, sortable table.",
                                      path="people/", active="people"))


# ----------------------------------------------------------------------------- tree
def build_tree(tree):
    prefix = "../"
    nodes = {}
    for pid, p in tree.people.items():
        if not tree.is_blood(pid):
            continue
        kids, sp = [], []
        for fam in tree.families_of.get(pid, []):
            other = [x for x in fam["partners"] if x != pid]
            sp += [tree.people[x]["name"] for x in other]
            for c in fam["children"]:
                kids.append([c, fam.get("order", 1)])
        mf = tree.facts(pid, "marriage")
        if not all(f["value"].startswith("(") for f in mf):
            mf = mf[:1]  # differing readings of one marriage: show the first, the page has both
        marr = [f["value"].split(",")[0] for f in mf] if not sp else []
        nodes[pid] = {"n": p["name"], "y": tree.years(pid), "s": p.get("sex", ""), "b": tree.branch(pid),
                      "sp": sp or marr, "c": kids, "f": 1 if pid in tree.founders else 0,
                      "u": 1 if p.get("uncertain") else 0}
    write("tree/tree.json", json.dumps({"root": TREE_ROOT, "nodes": nodes}, ensure_ascii=False, separators=(",", ":")))
    body = f"""<div class="wrap tree-page">
<p class="kicker">Family tree</p>
<h1>The Kastl family tree</h1>
<p class="lede">From Andreas Kastl, the earliest Kastl in the records, through Thomas Kastl, his children, and their descendants. Click a name to open their page; click <span class="kbd">+</span> to open a family. Drag to move, scroll or pinch to zoom.</p>
<div class="tree-tools" role="toolbar" aria-label="Tree controls">
  <button class="btn ghost small" type="button" data-act="brothers">Show the brothers</button>
  <button class="btn ghost small" type="button" data-act="expand">Open everything</button>
  <button class="btn ghost small" type="button" data-act="fit">Fit to screen</button>
  <span class="zoom"><button class="btn ghost small" type="button" data-act="in" aria-label="Zoom in">+</button><button class="btn ghost small" type="button" data-act="out" aria-label="Zoom out">−</button></span>
  <label class="tree-find">Find <input type="search" id="tree-find" list="tree-names" placeholder="Name…" autocomplete="off"></label>
  <datalist id="tree-names"></datalist>
</div>
<div class="tree-wrap" id="tree-wrap">
  <svg id="tree" role="img" aria-label="Family tree diagram. The table of people lists the same information as text."></svg>
</div>
<p class="muted tree-legend"><span class="lg lg-founder"></span> one of the seven brothers (or half-sister Anna) · dashed line: child of a second marriage · <span class="lg lg-more">+3</span> children not shown yet. Only Josef Kastl’s branch is built out so far; the <a href="../people/index.html">table</a> has the same people as text.</p>
</div>
<script src="{prefix}assets/js/tree.js" defer></script>"""
    write("tree/index.html", layout(prefix, "Family tree", body,
                                    description="Interactive family tree of the Kastl family: Andreas Kastl, Thomas Kastl, the seven brothers and their descendants.",
                                    path="tree/", active="tree"))


# ----------------------------------------------------------------------------- main
def main():
    pages = load_pages()
    pages_by_scan = {p["scan"]: p for p in pages}
    data = load_people()
    problems = check_quotes(data, pages_by_scan)
    if problems:
        print("Quote check failed:", *problems, sep="\n  ")
        sys.exit(1)
    tree = Tree(data)
    for d in ("people", "book", "tree"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    for pid in tree.people:
        build_person(tree, pid, pages_by_scan)
    build_people_index(tree, pages_by_scan)
    build_tree(tree)
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
