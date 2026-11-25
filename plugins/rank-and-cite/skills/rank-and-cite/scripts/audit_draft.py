#!/usr/bin/env python3
"""Gate 5: the quality audit. Every check that can be decided by code is decided here.

Hard checks fail the gate (exit 1). Soft checks are reported with a fix but don't
block. Judgment checks (helpfulness questions, accuracy of claims) live in
references/quality-signals.md and are done by the agent; this script covers the
mechanical half so it is identical on every run.

Usage:
  audit_draft.py article.md --jsonld article.jsonld --ledger ledger.json
                 [--gapmap gapmap.json] [--site example.com]
                 [--no-em-dash] [--min-external 3] [--min-internal 2] [--json]

Exit: 0 all hard checks pass, 1 any hard check fails, 2 bad input.
"""
import argparse
import datetime as dt
import json
import os
import re
import statistics
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from frontmatter import read_article  # noqa: E402

STAT_RE = re.compile(r"(?<![\w.#/-])(\d{1,3}(?:[.,]\d+)?\s?%|[$€£]\s?\d[\d,.]*\s?(?:[kmb]|million|billion)?|\d[\d,.]*\s?(?:million|billion|x\b|times\b))", re.I)
CITE_RE = re.compile(r"\]\(https?://|\[\^[^\]]+\]|\baccording to\b|\(source:", re.I)

# Strong tells: any single hit is worth fixing. Weak tells only count in density.
RESIDUE = [r"\bI hope this helps\b", r"\bas an AI\b", r"\bcertainly!", r"\bgreat question\b", r"\bin this (article|post|guide),? (we|you)('ll| will)\b",
           r"\blet'?s dive\b", r"\bwithout further ado\b", r"\[insert", r"\bTODO\b", r"\blorem ipsum\b"]
TELLS = [r"\bnot (just|only|merely)\b[^.]{0,80}?\bbut( also)?\b", r"\bit(?:'s| is) (important|worth) (to note|noting|mentioning)\b", r"\bin today'?s\b",
         r"\bdelv(e|es|ing)\b", r"\btapestry\b", r"\btestament to\b", r"\bpivotal\b", r"\bunderscor(e|es|ing)\b", r"\bever-evolving\b",
         r"\b(evolving|digital|competitive) landscape\b", r"\bnavigat(e|ing) the\b", r"\bunlock(s|ing)? the\b", r"\bleverag(e|es|ing)\b",
         r"\bseamless(ly)?\b", r"\brobust\b", r"\bgame[- ]chang", r"\bin conclusion\b", r"\bwhether you'?re\b", r"\bharness(ing)? the power\b",
         r"\bin the realm of\b", r"\bat the end of the day\b", r"\bplays a (crucial|vital|key) role\b", r"\bcrucial\b", r"\bfostering\b",
         r"\bembark\b", r"\bmeticulous", r"\bshowcas(e|es|ing)\b", r"\bvibrant\b", r"\bboasts?\b", r"^\s*(Additionally|Moreover|Furthermore),", r"\bexperts (say|agree)\b"]
QUESTION_START = re.compile(r"^(how|what|why|when|where|which|who|is|are|can|should|does|do|will)\b", re.I)


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%$ ]", " ", s.lower())).strip()


def split_sections(body):
    """Return (h1 list, sections[{level,heading,text}], intro_paragraphs)."""
    h1s, sections, intro = [], [], []
    cur = None
    for line in body.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 1:
                h1s.append(txt)
                continue
            cur = {"level": lvl, "heading": txt, "text": []}
            sections.append(cur)
        elif cur is None:
            intro.append(line)
        else:
            cur["text"].append(line)
    paras = [p.strip() for p in "\n".join(intro).split("\n\n") if p.strip() and not p.strip().startswith(("![", "<", "|"))]
    for s in sections:
        s["text"] = "\n".join(s["text"])
    return h1s, sections, paras


def plain(md):
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"^\[\^[^\]]+\]:.*$", " ", md, flags=re.M)  # footnote definitions only
    md = re.sub(r"\[\^[^\]]+\]", "", md)  # inline markers; keep the rest of the sentence
    md = re.sub(r"^\s*\|.*\|\s*$", " ", md, flags=re.M)
    return re.sub(r"[#*_>`]", " ", md)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“(])", re.sub(r"\s+", " ", text)) if s.strip()]


def syllables(w):
    w = w.lower()
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups) - (1 if w.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--jsonld")
    ap.add_argument("--ledger")
    ap.add_argument("--gapmap")
    ap.add_argument("--site")
    ap.add_argument("--no-em-dash", action="store_true", help="treat any em dash as a hard fail (house style)")
    ap.add_argument("--min-external", type=int, default=3)
    ap.add_argument("--min-internal", type=int, default=2)
    ap.add_argument("--min-info-gain", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    try:
        fm, body = read_article(a.article)
    except OSError as e:
        print(f"cannot read article: {e}", file=sys.stderr)
        sys.exit(2)
    results = []

    def check(cid, ok, severity, detail, fix=""):
        results.append({"id": cid, "pass": bool(ok), "severity": severity, "detail": detail, "fix": "" if ok else fix})

    h1s, sections, intro = split_sections(body)
    text = plain(body)
    words = text.split()
    wc = len(words)
    kw = (fm.get("primary_keyword") or "").strip()
    kw_tok = set(norm(kw).split())

    # --- Metadata and structure -------------------------------------------------
    title = fm.get("title") or (h1s[0] if h1s else "")
    meta = fm.get("meta_description") or ""
    check("one_h1", len(h1s) == 1, "hard", f"{len(h1s)} H1 heading(s)", "Use exactly one '# ' heading: the article title.")
    check("title_present", bool(title), "hard", title or "missing", "Set `title` in frontmatter.")
    check("title_has_keyword", kw_tok and kw_tok <= set(norm(title).split()), "soft", f"keyword '{kw}' in title: {title}",
          "Work the primary keyword (or all its words) into the title naturally.")
    check("title_length", 0 < len(title) <= 60, "soft", f"{len(title)} chars (heuristic; Google truncates by width)", "Trim the title to about 60 characters.")
    check("meta_length", 70 <= len(meta) <= 160, "soft", f"{len(meta)} chars", "Write a 70-160 character meta description that states the answer.")
    slug = fm.get("slug") or ""
    check("slug_format", bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+){0,7}", slug)), "soft", slug or "missing",
          "Lowercase, hyphenated, 1-8 words, no dates or stop-word padding.")

    first = intro[0] if intro else ""
    first_wc = len(plain(first).split())
    check("answer_first", 25 <= first_wc <= 90, "hard", f"first paragraph {first_wc} words",
          "Open with a self-contained 40-80 word answer to the query, before any background.")
    first150 = set(norm(" ".join(words[:150])).split())
    check("keyword_early", not kw_tok or kw_tok <= first150, "soft", "primary keyword words in first 150 words",
          "Use the primary keyword (or its words) in the opening answer.")

    h2 = [s for s in sections if s["level"] == 2]
    check("h2_count", len(h2) >= 4, "soft", f"{len(h2)} H2 sections", "Cover the must-cover subtopics as H2 sections.")
    q_share = sum(1 for s in h2 if s["heading"].rstrip().endswith("?") or QUESTION_START.match(s["heading"])) / max(1, len(h2))
    check("question_headings", q_share >= 0.4, "soft", f"{round(q_share * 100)}% of H2s are phrased as the reader's question",
          "Phrase more H2s as the questions searchers ask (People Also Ask, fan-out sub-questions).")
    long_secs = []
    for s in h2:
        sub = [x for x in sections if x is not s]
        sec_wc = len(plain(s["text"]).split())
        if sec_wc > 400:
            long_secs.append(f"{s['heading']} ({sec_wc}w)")
    check("section_length", not long_secs, "soft", ", ".join(long_secs) or "all H2 sections under 400 words",
          "Split long sections with H3s so each passage answers one thing.")
    weak_openers = []
    for s in h2:
        sents = sentences(plain(s["text"]))
        if sents and (len(sents[0].split()) > 35 or re.match(r"^(this|that|these|it|there)\b", sents[0], re.I)):
            weak_openers.append(s["heading"])
    check("section_openers", len(weak_openers) <= max(1, len(h2) // 4), "soft", ", ".join(weak_openers) or "sections open with a direct statement",
          "Open each H2 with a standalone sentence that answers the heading without needing context.")

    # --- Evidence ---------------------------------------------------------------
    uncited = [s for s in sentences(re.sub(r"^#.*$", "", body, flags=re.M)) if STAT_RE.search(plain(s)) and not CITE_RE.search(s)
               and not re.search(r"\b(19|20)\d{2}\b$", s)]
    check("stats_cited", not uncited, "hard", f"{len(uncited)} statistic sentence(s) without a source in the same sentence",
          "Put a link or footnote in the same sentence as every number. Examples: " + " | ".join(u[:110] for u in uncited[:3]))
    stat_n = len(STAT_RE.findall(text))
    check("stat_density", stat_n >= 3, "soft", f"{stat_n} statistics", "Add at least 3 sourced figures; statistics raise citation odds in AI answers.")
    quote = bool(re.search(r"^>\s|“[^”]{20,}”\s*(?:,|—|-)?\s*(?:said|says|writes|according)|\"[^\"]{20,}\"\s*,?\s*(?:said|says|writes)", body, re.M))
    check("attributed_quote", quote, "soft", "attributed quotation or first-hand statement present" if quote else "none found",
          "Add one attributed quote from a named practitioner or the author's own first-hand observation.")

    links = re.findall(r"\]\((https?://[^)\s]+)\)", body)
    malformed = [l for l in links if not urllib.parse.urlparse(l).netloc]
    site = (a.site or fm.get("site") or "").lower().removeprefix("www.")
    hosts = [urllib.parse.urlparse(l).netloc.lower().removeprefix("www.") for l in links]
    internal = [l for l, h in zip(links, hosts) if site and (h == site or h.endswith("." + site))]
    rel_internal = re.findall(r"\]\((/[^)\s]*)\)", body)
    external = [l for l, h in zip(links, hosts) if not site or not (h == site or h.endswith("." + site))]
    check("links_wellformed", not malformed, "hard", f"{len(malformed)} malformed", "Fix: " + ", ".join(malformed[:3]))
    check("external_sources", len(set(external)) >= a.min_external, "hard", f"{len(set(external))} unique external sources",
          f"Cite at least {a.min_external} primary sources (studies, docs, official data), not other blog summaries.")
    if site:
        n_int = len(set(internal)) + len(set(rel_internal))
        check("internal_links", n_int >= a.min_internal, "hard", f"{n_int} internal links",
              f"Link to at least {a.min_internal} existing pages on {site} with descriptive anchors (verify each URL exists).")
    bad_anchor = re.findall(r"\[(click here|here|this|read more|link)\]\(", body, re.I)
    check("anchor_text", not bad_anchor, "soft", f"{len(bad_anchor)} vague anchors", "Use descriptive anchor text.")

    imgs = re.findall(r"!\[([^\]]*)\]\(", body)
    check("image_alt", all(x.strip() for x in imgs), "hard" if imgs else "soft",
          f"{len(imgs)} images, {sum(1 for x in imgs if not x.strip())} missing alt", "Write descriptive alt text for every image.")

    # --- E-E-A-T signals --------------------------------------------------------
    authors = fm.get("author")
    authors = authors if isinstance(authors, list) else [authors] if authors else []
    real = [x for x in authors if isinstance(x, dict) and x.get("name") and x.get("url")]
    check("author_byline", bool(real), "hard", ", ".join(x["name"] for x in real) or "missing",
          "Name a real author with a `url` to a bio page showing relevant experience. Never invent one; leave it to the user if unknown.")
    check("author_credentials", any(x.get("jobTitle") or x.get("description") for x in real), "soft",
          "credentials stated" if real else "no author", "Add the author's role or relevant experience (jobTitle/description).")
    check("date_published", bool(fm.get("date_published")), "hard", str(fm.get("date_published")), "Set `date_published` (ISO 8601).")
    disclosure = re.search(r"(AI|machine)[- ]assisted|drafted with|how (we|this) (made|wrote|researched)|methodology", body, re.I)
    check("process_disclosure", bool(disclosure), "soft", "how-this-was-made note present" if disclosure else "none",
          "Add a one-line note on how the piece was researched (and AI assistance, where readers would expect to know).")

    # --- AI tells (the humanizer pass verifies against these) ----------------------
    residue = [m.group(0) for p in RESIDUE for m in re.finditer(p, body, re.I)]
    check("chatbot_residue", not residue, "hard", ", ".join(residue) or "none", "Delete chat/drafting leftovers.")
    tells = {}
    for p in TELLS:
        for m in re.finditer(p, text, re.I | re.M):
            tells[m.group(0).lower()] = tells.get(m.group(0).lower(), 0) + 1
    per_k = sum(tells.values()) / max(1, wc) * 1000
    check("ai_tell_density", per_k <= 2.0, "hard", f"{per_k:.1f} tells per 1,000 words: " + ", ".join(f"{k}×{v}" for k, v in sorted(tells.items(), key=lambda kv: -kv[1])[:8]),
          "Run the humanizer pass: replace each with the specific fact it was standing in for.")
    em = body.count("—")
    check("em_dashes", em == 0 if a.no_em_dash else em <= max(2, wc // 500), "hard" if a.no_em_dash else "soft", f"{em} em dashes",
          "Replace em dashes with commas, colons, parentheses or full stops.")
    excl = len(re.findall(r"!(?=\s|$)", text))
    check("exclamations", excl == 0, "soft", f"{excl} exclamation marks", "Remove exclamation marks.")
    bold = len(re.findall(r"\*\*[^*]+\*\*", body))
    check("bold_density", bold <= max(3, wc // 300), "soft", f"{bold} bold spans", "Use bold sparingly; not as decoration on every list item.")
    sents = sentences(text)
    lens = [len(s.split()) for s in sents if s.split()]
    if len(lens) > 10:
        cv = statistics.pstdev(lens) / statistics.mean(lens)
        check("sentence_variety", cv >= 0.35, "soft", f"sentence length variation {cv:.2f}", "Vary sentence length; uniform rhythm reads as generated.")
        syl = sum(syllables(w) for w in re.findall(r"[A-Za-z]+", text))
        fre = 206.835 - 1.015 * (wc / len(lens)) - 84.6 * (syl / max(1, wc))
        check("readability", fre >= 40, "soft", f"Flesch reading ease {fre:.0f}", "Shorten sentences and swap jargon for plain words.")
    specific = len(STAT_RE.findall(text)) + len(re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b", text))
    density = specific / max(1, wc) * 500
    check("specificity", density >= 8, "soft", f"{density:.1f} specifics (named entities, figures) per 500 words",
          "Replace generic claims with named tools, people, places, dates and figures.")

    # --- Information gain ledger -----------------------------------------------------
    ig_score = None
    if a.ledger:
        led = json.load(open(a.ledger))
        items = led.get("info_gain") or []
        ntext = norm(body)
        found = [it for it in items if it.get("evidence") and norm(it["evidence"]) in ntext]
        sourced = [it for it in found if it.get("source")]
        first_party = [it for it in sourced if it.get("type") in ("first_party_data", "experience", "original_analysis", "expert_quote")]
        check("info_gain_count", len(sourced) >= a.min_info_gain, "hard",
              f"{len(sourced)}/{len(items)} ledger items are in the text with a source",
              f"Need at least {a.min_info_gain} sourced items whose `evidence` phrase appears verbatim in the article. "
              + ("Not found in text or unsourced: " + "; ".join((it.get("claim") or "?")[:60] for it in items if it not in sourced) if len(sourced) < len(items) else "Add more first-party or primary-source items."))
        check("first_party_present", bool(first_party), "hard", f"{len(first_party)} first-party item(s)",
              "Inject at least one first-party item (own data, test, case, expert quote). Without it the page is the 11th copy.")
        claims = led.get("claims") or []
        if claims:
            pts = {"net_new": 3, "contradiction": 2}
            net = sum(1 for c in claims if c.get("class") == "net_new" and c.get("source"))
            ig_score = round(net / len(claims), 2)
            check("info_gain_ratio", 0.15 <= ig_score, "soft", f"IG ratio {ig_score} ({net} supported net-new of {len(claims)} claims); points {sum(pts.get(c.get('class'), 0) for c in claims if c.get('source'))}",
                  "Raise the share of supported net-new claims to at least 0.15.")
            unsupported = [c["text"][:70] for c in claims if c.get("class") in ("net_new", "contradiction") and not c.get("source")]
            check("no_unsupported_novelty", not unsupported, "hard", f"{len(unsupported)} unsupported novel claim(s)",
                  "Source or cut: " + " | ".join(unsupported[:3]))

    # --- Consensus coverage --------------------------------------------------------
    if a.gapmap:
        gm = json.load(open(a.gapmap))
        skipped = {norm(x.get("topic", "")) for x in (json.load(open(a.ledger)).get("consensus_skipped") or [])} if a.ledger else set()
        missing = []
        body_tok = set(norm(text).split())
        for t in gm.get("must_cover", []):
            tt = {w for w in norm(t["topic"]).split() if len(w) > 3}
            if norm(t["topic"]) in skipped:
                continue
            if tt and len(tt & body_tok) / len(tt) < 0.6:
                missing.append(t["topic"])
        check("must_cover_topics", not missing, "hard", f"{len(missing)} must-cover topic(s) missing",
              "Cover or record a reason in ledger.consensus_skipped: " + "; ".join(missing[:5]))
        med = (gm.get("serp_profile") or {}).get("word_count_median")
        if med:
            check("length_vs_serp", 0.6 * med <= wc <= 1.6 * med, "soft", f"{wc} words vs SERP median {med} (no word count is a ranking factor)",
                  "Length should follow the topic; a big gap usually means missing coverage or padding.")

    # --- JSON-LD ----------------------------------------------------------------------
    if a.jsonld:
        try:
            ld = json.load(open(a.jsonld))
        except (OSError, json.JSONDecodeError) as e:
            check("jsonld_parses", False, "hard", str(e), "Regenerate with scripts/build_jsonld.py.")
            ld = None
        if ld is not None:
            check("jsonld_parses", True, "hard", "valid JSON")
            nodes = ld.get("@graph") if isinstance(ld, dict) and "@graph" in ld else (ld if isinstance(ld, list) else [ld])
            ctx = ld.get("@context", "") if isinstance(ld, dict) else ""
            check("jsonld_context", "schema.org" in str(ctx), "hard", str(ctx), "Use \"@context\": \"https://schema.org\".")
            types = [n.get("@type") for n in nodes if isinstance(n, dict)]
            art = next((n for n in nodes if isinstance(n, dict) and n.get("@type") in ("Article", "BlogPosting", "NewsArticle", "TechArticle")), None)
            check("jsonld_article", art is not None, "hard", ", ".join(map(str, types)), "Add a BlogPosting/Article node.")
            if art:
                check("jsonld_headline", art.get("headline") == title, "hard", f"headline={art.get('headline')!r}", "headline must equal the visible title.")
                check("jsonld_headline_len", len(art.get("headline") or "") <= 110, "soft", f"{len(art.get('headline') or '')} chars", "Keep headline under 110 characters.")
                au = art.get("author")
                au = au if isinstance(au, list) else [au] if au else []
                au_names = {x.get("name") for x in au if isinstance(x, dict)}
                check("jsonld_author", au_names and au_names == {x.get("name") for x in real} and all(x.get("url") for x in au if isinstance(x, dict)),
                      "hard", f"{sorted(n for n in au_names if n)}", "Author Person nodes must match the byline and carry `url`.")
                dp, dm = art.get("datePublished"), art.get("dateModified")
                check("jsonld_dates", bool(dp) and str(dp) == str(fm.get("date_published")) and (not dm or str(dm) >= str(dp)), "hard",
                      f"published={dp} modified={dm}", "datePublished must match frontmatter; dateModified >= datePublished.")
                img = art.get("image")
                check("jsonld_image", bool(img), "soft", f"{len(img) if isinstance(img, list) else (1 if img else 0)} image(s)",
                      "Add images (ideally 16:9, 4:3 and 1:1, at least 50K pixels each).")
            stale = [t for t in types if t in ("FAQPage", "HowTo")]
            check("jsonld_no_retired_types", not stale, "soft", ", ".join(stale) or "none",
                  "FAQPage/HowTo no longer produce rich results; drop them unless the CMS needs them for other reasons.")

    hard_fail = [r for r in results if r["severity"] == "hard" and not r["pass"]]
    soft_fail = [r for r in results if r["severity"] == "soft" and not r["pass"]]
    summary = {"article": a.article, "words": wc, "hard_failed": len(hard_fail), "soft_failed": len(soft_fail),
               "checks": len(results), "info_gain_ratio": ig_score, "verdict": "PASS" if not hard_fail else "FAIL",
               "audited_at": dt.datetime.now().isoformat(timespec="seconds"), "results": results}
    if a.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"# Audit: {summary['verdict']}  ({len(results)} checks, {len(hard_fail)} hard fail, {len(soft_fail)} soft fail, {wc} words)\n")
        print("| | Check | Severity | Detail | Fix |\n|---|---|---|---|---|")
        for r in sorted(results, key=lambda r: (r["pass"], r["severity"] != "hard")):
            print(f"| {'PASS' if r['pass'] else 'FAIL'} | {r['id']} | {r['severity']} | {r['detail'].replace('|', '/')} | {r['fix'].replace('|', '/')} |")
    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    main()
