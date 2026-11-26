"""Structural checks run on every build (BACKLOG step 8a/8b).

Independent of the people data: they read the transcriptions again and compare what the book
prints with what the data says.

- lineage: "RICHARD DENNIS KASTL (Dennis, Stanley, Joseph W., Josef) born …" must name, in
  order, the parents in the data's line of descent.
- counts: every "### The family of …" / "### The children of …" heading in a checked branch's
  chapter (and its supplement section) must match a family, and the family must have as many
  children as the printed list.
- labels: known relationship labels (tests for Tree.relation).
- connected: everyone is reachable from Andreas through families.
- plausibility: warnings only, since the book has real oddities.

Book-caused exceptions go in content/verification/allow-<branch>.json, each with a note.
Standard library only; must run on Python 3.8.
"""
import json
import os
import re
import unicodedata

# Branches whose chapters have been built out and are checked for headings and counts.
# Add a branch key here when its work unit lands.
CHECKED_BRANCHES = {"josef", "wenzel", "thomas", "zima"}
# A work unit in progress can add its branch for a run without editing this file:
#   KFH_CHECK_BRANCHES=peter python3 tools/build.py --check
CHECKED_BRANCHES |= {b for b in os.environ.get("KFH_CHECK_BRANCHES", "").split(",") if b}

# Relationship-label tests: (person id, expected label). Add a case whenever a bug is found.
LABEL_CASES = [
    ("thomas-kastl-1806", "Father of the seven brothers"),
    ("maria-marsalek", "Mother of the seven brothers"),
    ("maria-muzik", "Grandmother of the seven brothers"),
    ("andreas-muzik", "Great-grandfather of the seven brothers"),
    ("josef-marsalek", "Grandfather of the seven brothers"),
    ("andreas-kastl", "2× great-grandfather of the seven brothers"),
    ("josef-kastl-1840", "One of the seven brothers"),
    ("anna-kastl-1865", "Half-sister of the seven brothers"),
    ("eva-kastl", "Sister of the seven brothers"),
    ("josef-kastl-1867", "Half-brother of the seven brothers"),
    ("barbara-kellner", "Second wife of Thomas Kastl"),
    ("simon-kellner", "Father of Barbara Kellner"),
    ("dorota-blaha", "Wife of Josef Kastl"),
    ("joseph-kastl-1869", "Son of Josef Kastl"),
    ("frances-fixa", "Wife of Joseph Kastl"),
    ("rose-kastl-1919", "Granddaughter of Josef Kastl"),
    ("matthew-richard-kastl-1983", "3× great-grandson of Josef Kastl"),
]

# Given names the book uses interchangeably (English / Czech / German forms).
EQUIV = [{"john", "jan", "johann"}, {"joseph", "josef"}, {"jacob", "jakob", "jakub"},
         {"thomas", "tomas"}, {"andreas", "andrew", "andress"}, {"wenzel", "vaclav"},
         {"peter", "petr"}]

BRANCH_OF_CHAPTER = [("peter", "peter"), ("wenzel", "wenzel"), ("john", "john"),
                     ("josef", "josef"), ("joseph", "josef"), ("jacob", "jacob"),
                     ("andrew", "andrew"), ("thomas", "thomas"), ("tomas", "zima"), ("zima", "zima")]
END_OF_CHAPTERS = ("conclusion", "notes", "supplementary")


def fold(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def given_names(person):
    """Folded words of a person's name and of every printed variant."""
    names = [person["name"]]
    for f in person["facts"]:
        if f["type"] == "name":
            names += f["value"].split(",")
    words = set()
    for n in names:
        words.update(w.strip(".") for w in fold(n).split())
    for group in EQUIV:
        if words & group:
            words |= group
    return words


def name_matches(token, person):
    first = fold(token).split()[0].strip(".") if token.strip() else ""
    return bool(first) and first in given_names(person)


def load_allow(folder):
    """Merge allow.json and allow-<branch>.json (one file per work unit, so units don't clash)."""
    out = {"lineage": [], "count": []}
    for f in sorted(folder.glob("allow*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for kind in ("lineage", "count"):
            for e in d.get(kind, []):
                if not e.get("note"):
                    raise SystemExit(f"{f.name}: every {kind} entry needs a note: {e}")
                out[kind].append(e)
    return out


# ----------------------------------------------------------------------------- page stream
HEADING = re.compile(r"^### (.+?)\s*$")
CHILD = re.compile(r"^(\d{1,2})(?:\.\s+[A-Z]|\s+[A-Z]{2,} )")  # "7 ANN MARIE" is printed without the period
UNNUMBERED_CHILD = re.compile(r"^[A-Z][A-Z .'\-]+ — \(")
# A children sub-list inside a family, one per marriage: "Children of Louis Kastl and (1) Doris
# Howard:". It is matched to a family like a heading, by its text without the final ":" or ".".
SUBLIST = re.compile(r"^(?:The c|C)hildren of (.+?)[:.]?$")
LINEAGE = re.compile(r"^([A-Z][A-Z .'\-]+?) \(([^)]*)\)\s*(?:,\s*)?(born|son|daughter|died)")


def sections(pages):
    """Yield every family heading in reading order, with its chapter branch, its scan, the
    children it lists (numbered or not) and the lineage paragraph that follows it. A list that
    runs onto the next page stays with its heading."""
    out, cur, chapter = [], None, None
    for p in pages:
        if p["scan"] < "s017":
            continue
        for raw in p["body"].split("\n"):
            line = raw.strip()
            if line.startswith("## "):
                low = fold(line)
                hit = [b for k, b in BRANCH_OF_CHAPTER if k in low]
                if hit:
                    chapter = hit[0]
                elif any(k in low for k in END_OF_CHAPTERS):
                    chapter = None
                cur = None
                continue
            if line.startswith("*(Page"):
                cur = None
                continue
            m = HEADING.match(line)
            if m:
                text = m.group(1)
                if text.startswith(("The family of", "The children of")):
                    cur = {"heading": text, "scan": p["scan"], "branch": chapter,
                           "children": [], "lineage": None}
                    out.append(cur)
                else:
                    cur = None
                continue
            if cur is None:
                continue
            sm = SUBLIST.match(line)
            if sm:
                cur = {"heading": line.rstrip(":."), "scan": p["scan"], "branch": cur["branch"],
                       "children": [], "lineage": None}
                out.append(cur)
                continue
            if CHILD.match(line) or UNNUMBERED_CHILD.match(line):
                cur["children"].append(line)
                continue
            lm = LINEAGE.match(line)
            if lm and cur["lineage"] is None and not cur["children"]:
                tokens = []
                for t in (t.strip() for t in lm.group(2).split(",")):
                    if re.fullmatch(r"[A-Z]\.", t) and tokens:  # "(John R., Joseph, W., Josef)": stray comma
                        tokens[-1] += " " + t
                    elif t:
                        tokens.append(t)
                cur["lineage"] = (lm.group(1), tokens, p["scan"])
    return out


def family_index(families):
    by = {}
    for fam in families:
        hs = fam.get("heading") or []
        if isinstance(hs, str):
            hs = [hs]
        for h in hs:
            by.setdefault(h, []).append(fam)
    return by


def pick_family(cands, scan):
    for fam in cands:
        if scan in fam.get("sources", []):
            return fam
    return cands[0] if cands else None


# ----------------------------------------------------------------------------- checks
def check_lineage_and_counts(tree, pages, allow):
    errors = []
    by_heading = family_index(tree.families)
    allow_lin = {(e["scan"], e["person"]) for e in allow.get("lineage", [])}
    allow_cnt = {(e["scan"], e["heading"]) for e in allow.get("count", [])}
    n_lineage = n_counts = 0
    for sec in sections(pages):
        fam = pick_family(by_heading.get(sec["heading"], []), sec["scan"])
        checked = sec["branch"] in CHECKED_BRANCHES
        if fam is None:
            if checked:
                errors.append(f"{sec['scan']}: no family for printed heading “{sec['heading']}”")
            continue
        # child count
        if sec["children"] and (sec["scan"], sec["heading"]) not in allow_cnt:
            n_counts += 1
            if len(sec["children"]) != len(fam["children"]):
                errors.append(f"{sec['scan']}: “{sec['heading']}” prints {len(sec['children'])} children, "
                              f"family {fam['id']} has {len(fam['children'])}")
        # lineage
        if sec["lineage"]:
            caps, tokens, scan = sec["lineage"]
            who = [x for x in fam["partners"] if name_matches(caps, tree.people[x])]
            pid = who[0] if who else next((x for x in fam["partners"] if tree.is_blood(x)), None)
            if pid is None or (scan, pid) in allow_lin:
                continue
            n_lineage += 1
            up = list(reversed(tree.chain(pid)))[1:]  # parent, grandparent, …
            bad = len(tokens) > len(up) or any(not name_matches(t, tree.people[a]) for t, a in zip(tokens, up))
            if bad:
                got = ", ".join(tree.people[a]["name"] for a in up[:len(tokens)])
                errors.append(f"{scan}: lineage of {pid} printed ({', '.join(tokens)}), data has ({got})")
    return errors, n_lineage, n_counts


def check_labels(tree):
    errors = []
    for pid, want in LABEL_CASES:
        if pid not in tree.people:
            errors.append(f"label test: unknown person {pid}")
            continue
        got = tree.relation(pid)
        if got != want:
            errors.append(f"label test: {pid} is “{got}”, expected “{want}”")
    return errors


def check_connected(tree, root):
    seen, todo = {root}, [root]
    while todo:
        x = todo.pop()
        fams = list(tree.families_of.get(x, []))
        if x in tree.parents_of:
            fams.append(tree.parents_of[x])
        for fam in fams:
            for y in fam["partners"] + fam["children"]:
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
    return [f"not connected to {root}: {pid}" for pid in tree.people if pid not in seen]


def first_year(tree, pid, t):
    ys = tree.year_list(pid, t)
    return int(ys[0]) if ys else None


def plausibility(tree):
    warn = []
    for pid in tree.people:
        b, d = first_year(tree, pid, "birth"), first_year(tree, pid, "death")
        if b and d and d < b:
            warn.append(f"{pid}: died ({d}) before born ({b})")
    for fam in tree.families:
        kids = [(c, first_year(tree, c, "birth")) for c in fam["children"]]
        for x in fam["partners"]:
            pb = first_year(tree, x, "birth")
            pd = first_year(tree, x, "death")
            for c, cb in kids:
                if cb and pb and cb - pb < 13:
                    warn.append(f"{c}: born {cb}, parent {x} born {pb}")
                if cb and pd and tree.people[x].get("sex") == "F" and cb > pd:
                    warn.append(f"{c}: born {cb}, after mother {x} died {pd}")
        years = [cb for _, cb in kids if cb]
        my = None
        for m in fam.get("marriage", []):
            ys = re.findall(r"\b1[5-9]\d\d\b", m["value"])
            if ys:
                my = int(ys[0]) if my is None else min(my, int(ys[0]))
        if my and years and min(years) < my:
            warn.append(f"{fam['id']}: married {my}, first child born {min(years)}")
    seen = {}
    for pid, p in tree.people.items():
        for f in tree.facts(pid, "birth"):
            key = (p["name"], f["value"])
            if key in seen and seen[key] != pid:
                warn.append(f"possible duplicate: {seen[key]} and {pid} ({p['name']}, born {f['value']})")
            seen[key] = pid
    return warn


def run(tree, pages, root, content_dir):
    """Run every check. Returns (errors, warnings, summary)."""
    allow = load_allow(content_dir / "verification")
    errors, n_lin, n_cnt = check_lineage_and_counts(tree, pages, allow)
    errors += check_labels(tree)
    errors += check_connected(tree, root)
    warnings = plausibility(tree)
    summary = (f"{n_lin} printed lineages and {n_cnt} child lists checked, "
               f"{len(LABEL_CASES)} label tests, {len(warnings)} plausibility warnings")
    return errors, warnings, summary
