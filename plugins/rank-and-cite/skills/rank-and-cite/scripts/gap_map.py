#!/usr/bin/env python3
"""Build the consensus-vs-gap map from the top-10 extracts (Gate 3 input).

Each extract is a serp_extract.py record. The agent may add a "topics" list to a
record (normalized subtopic labels it read off the page). Without one, H2/H3
headings are clustered by token overlap. Coverage counts, thresholds and the
SERP profile are computed here so the brief rests on arithmetic, not vibes.

Usage:
  gap_map.py extracts/*.json [--paa paa.json] [--consensus 5] [--must 7] > gapmap.json

paa.json: ["question", ...] from People Also Ask / related searches / AI Overview fan-out.
"""
import argparse
import datetime as dt
import json
import re
import statistics
import sys

STOP = set("""a an and are as at be by can do does for from how i in is it its of on or our should
the their this to vs what when where which who why will with you your we us best guide complete
ultimate 2023 2024 2025 2026 2027 step steps tips""".split())


def stem(w):
    # Light plural folding so "audit costs" and "audit cost" cluster; deliberately not a full stemmer.
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def tokens(s):
    return {stem(w) for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def cluster(labels_by_page, threshold):
    clusters = []  # [{"label": str, "tok": set, "pages": set}]
    for page, labels in labels_by_page.items():
        for lab in labels:
            t = tokens(lab)
            if not t:
                continue
            best, score = None, 0.0
            for c in clusters:
                s = jaccard(t, c["tok"])
                if s > score:
                    best, score = c, s
            if best and score >= threshold:
                best["pages"].add(page)
                best["variants"].add(lab)
            else:
                clusters.append({"label": lab, "tok": t, "pages": {page}, "variants": {lab}})
    return clusters


def parse_date(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")[:25]).date()
    except ValueError:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(s))
        return dt.date(*map(int, m.groups())) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("extracts", nargs="+")
    ap.add_argument("--paa")
    ap.add_argument("--consensus", type=int, default=5, help="pages (of 10) for a topic to count as consensus")
    ap.add_argument("--must", type=int, default=7, help="pages (of 10) for a topic to be mandatory coverage")
    ap.add_argument("--similarity", type=float, default=0.5)
    a = ap.parse_args()

    pages, failed = [], []
    for path in a.extracts:
        rec = json.load(open(path))
        (failed if rec.get("error") or rec.get("warning") else pages).append(rec)
    n = len(pages)
    if n < 5:
        print(json.dumps({"error": f"only {n} usable extracts ({len(failed)} failed or thin). Refetch before mapping; a gap map on <5 pages is noise.",
                          "failed": [f.get("url") for f in failed]}, indent=2))
        sys.exit(1)

    # Scale thresholds when fewer than 10 pages were usable, so "5 of 10" stays "half".
    cons = max(2, round(a.consensus * n / 10))
    must = max(cons, round(a.must * n / 10))

    labels = {}
    for p in pages:
        key = p.get("url") or str(p.get("position"))
        labels[key] = p.get("topics") or [h["text"] for h in p.get("headings", []) if h["level"] in (2, 3)]
    cl = cluster(labels, a.similarity)
    rows = sorted(({"topic": c["label"], "pages": len(c["pages"]), "variants": sorted(c["variants"])[:4]} for c in cl),
                  key=lambda r: -r["pages"])

    paa = json.load(open(a.paa)) if a.paa else []
    all_heads = [tokens(x) for ls in labels.values() for x in ls]
    unanswered = [q for q in paa if max((jaccard(tokens(q), h) for h in all_heads), default=0) < a.similarity]

    wc = [p["word_count"] for p in pages if p.get("word_count")]
    today = dt.date.today()
    ages = [(today - d).days for d in (parse_date(p.get("date_modified") or p.get("date_published")) for p in pages) if d]
    schema = {}
    for p in pages:
        for t in set(p.get("schema_types") or []):
            schema[t] = schema.get(t, 0) + 1

    out = {
        "pages_used": n, "pages_failed": [f.get("url") for f in failed],
        "thresholds": {"consensus": cons, "must_cover": must},
        "must_cover": [r for r in rows if r["pages"] >= must],
        "consensus": [r for r in rows if cons <= r["pages"] < must],
        "long_tail": [r for r in rows if 2 <= r["pages"] < cons],
        "singletons": [r["topic"] for r in rows if r["pages"] == 1][:40],
        "paa_unanswered_by_serp": unanswered,
        "serp_profile": {
            "word_count_median": int(statistics.median(wc)) if wc else None,
            "word_count_range": [min(wc), max(wc)] if wc else None,
            "pages_with_tables": sum(1 for p in pages if p.get("tables")),
            "stat_mentions_median": statistics.median([p.get("numbers", 0) for p in pages]),
            "pages_with_author": sum(1 for p in pages if p.get("author")),
            "schema_types": dict(sorted(schema.items(), key=lambda kv: -kv[1])),
            "freshness_days_median": int(statistics.median(ages)) if ages else None,
            "pages_dated": len(ages),
        },
        "gap_candidates_note": "Gaps = paa_unanswered_by_serp + singletons the reader needs + anything the SERP states without data. "
                               "A gap only counts once a source the user holds can fill it.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
