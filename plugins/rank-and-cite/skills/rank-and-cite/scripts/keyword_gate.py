#!/usr/bin/env python3
"""Gate 1 (demand) and the SERP read, decided in code so the same numbers always give the same answer.

Philosophy: the only reason to kill a keyword is that nobody searches for it at all.
Difficulty, SERP format, intent, AI Overviews and an existing page are reasons to
shape the article, not to drop it: good content that educates the buyer still earns
rankings and AI citations over time. So `serp` mode never kills; it returns notes
for the brief.

"Nobody searches" is judged on evidence, not one tool's number. Keyword tools
report 0 for many real long-tail queries, so a 0 only kills when there is also no
other sign of demand (autocomplete, People Also Ask, forum threads, a related
keyword with volume).

Usage:
  keyword_gate.py demand metrics.json
  keyword_gate.py serp   serp.json

metrics.json:
  {"keyword": "...", "locale": "us-en",
   "volume": 320 | 0 | null,                 # monthly searches from any provider; null = no provider answered
   "kd": 0-100 | null, "intent": "informational|commercial|transactional|navigational" | null,
   "trend_12m": [ints] | null,
   "demand_evidence": ["autocomplete: '<kw> for startups'", "PAA: 'how do I ...'", "reddit thread 2026-08 ..."],
   "related": [{"keyword": "...", "volume": 90, "kd": 12}],
   "existing_url": "https://site/page" | null, "existing_position": int | null}

serp.json:
  {"keyword": "...", "site_authority": 0-100 | null, "kd": 0-100 | null,
   "results": [{"position": 1, "url": "...", "type": "article|product|category|tool|video|forum|homepage|other", "domain_authority": int | null}],
   "features": ["ai_overview", "featured_snippet", "people_also_ask", "video", "shopping", "local_pack"]}

Exit: 0 PROCEED, 2 NEEDS_INPUT (no number and no evidence yet: go get some, or ask the user), 3 KILL.
"""
import argparse
import json
import statistics
import sys

PROCEED, NEEDS_INPUT, KILL = "PROCEED", "NEEDS_INPUT", "KILL"
EXIT = {PROCEED: 0, NEEDS_INPUT: 2, KILL: 3}


def demand(m):
    vol = m.get("volume")
    evidence = [e for e in (m.get("demand_evidence") or []) if str(e).strip()]
    related = sorted([r for r in (m.get("related") or []) if (r.get("volume") or 0) > 0], key=lambda r: -(r.get("volume") or 0))
    notes = []

    if vol and vol > 0:
        verdict = PROCEED
        notes.append(f"{vol} searches/month: people search this.")
    elif evidence or related:
        verdict = PROCEED
        why = []
        if evidence:
            why.append(f"{len(evidence)} demand signal(s): " + "; ".join(evidence[:3]))
        if related:
            why.append(f"related queries with volume: " + ", ".join(f"{r['keyword']} ({r['volume']})" for r in related[:3]))
        notes.append(("tool volume is 0" if vol == 0 else "no tool volume") + ", but there is demand. " + " | ".join(why))
        notes.append("Consider targeting the highest-volume related query as the primary keyword and this one as a section.")
    elif vol == 0:
        verdict = KILL
        notes.append("volume is 0 and no other demand signal was found (autocomplete, People Also Ask, forums, related queries). Nobody is searching for this.")
    else:
        verdict = NEEDS_INPUT
        notes.append("no volume figure and no demand evidence yet. Check autocomplete, People Also Ask and forums, or ask the user for a number.")

    # Advisory notes only. None of these change the verdict.
    trend = m.get("trend_12m") or []
    if len(trend) >= 6:
        h = len(trend) // 2
        first, last = statistics.mean(trend[:h]), statistics.mean(trend[h:])
        if first > 0 and last / first < 0.5:
            notes.append(f"note: demand fell {round(100 * (1 - last / first))}% across the last 12 months.")
    intent = (m.get("intent") or "").lower()
    if intent in ("transactional", "navigational"):
        notes.append(f"note: intent reads {intent}; the article should still help, but expect product/brand pages to dominate.")
    if m.get("existing_url"):
        pos = m.get("existing_position")
        notes.append(f"note: the site already has {m['existing_url']}" + (f" (position {pos})" if pos else "")
                     + ". Decide with the user: refresh that page, or differentiate this one so the two don't compete.")

    return {"gate": "demand", "verdict": verdict, "keyword": m.get("keyword"), "volume": vol, "notes": notes,
            "related_with_volume": [{"keyword": r["keyword"], "volume": r.get("volume"), "kd": r.get("kd")} for r in related[:5]]}


def serp(s):
    results = sorted(s.get("results") or [], key=lambda r: r.get("position", 99))[:10]
    if not results:
        return {"gate": "serp", "verdict": NEEDS_INPUT, "notes": ["no SERP results supplied; get the top 10 first."]}
    types = [(r.get("type") or "other").lower() for r in results]
    counts = {t: types.count(t) for t in set(types)}
    article_share = (counts.get("article", 0) + counts.get("forum", 0)) / len(types)
    notes = [f"top-10 mix: " + ", ".join(f"{t} {n}" for t, n in sorted(counts.items(), key=lambda kv: -kv[1]))]
    if article_share < 0.3:
        dom = max(counts, key=counts.get)
        notes.append(f"few articles rank ({round(article_share * 100)}%). Make the article do what the {dom} pages do for the reader "
                     "(a worked example, a table, a calculator-style walkthrough) so it serves the same task.")
    kd, auth = s.get("kd"), s.get("site_authority")
    das = sorted(r["domain_authority"] for r in results if r.get("domain_authority") is not None)
    if kd is not None and auth is not None:
        notes.append(f"difficulty {kd} vs site authority {auth}" + (f"; weakest ranking domain {das[0]}" if das else "")
                     + (". Expect a slow climb; lean on information gain and internal links." if kd - auth > 25 else "."))
    feats = {f.lower() for f in (s.get("features") or [])}
    if "ai_overview" in feats:
        notes.append("AI Overview present: write quotable, answer-first passages with sourced figures to earn the citation.")
    if "featured_snippet" in feats:
        notes.append("featured snippet present: put a 40-60 word direct answer under a heading that mirrors the query.")
    if "people_also_ask" in feats:
        notes.append("People Also Ask present: map each question to a heading or an answer inside a section.")
    return {"gate": "serp", "verdict": PROCEED, "keyword": s.get("keyword"), "article_share": round(article_share, 2), "notes": notes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["demand", "serp"])
    ap.add_argument("file")
    a = ap.parse_args()
    data = json.load(open(a.file))
    out = demand(data) if a.mode == "demand" else serp(data)
    print(json.dumps(out, indent=2))
    sys.exit(EXIT[out["verdict"]])


if __name__ == "__main__":
    main()
