# Output formats

## article.md frontmatter

`build_jsonld.py` and `audit_draft.py` read this frontmatter. It's a YAML subset (scalars, one level of nesting, lists). Alternatively, the block between the `---` lines can be plain JSON.

```yaml
---
title: How long does SOC 2 Type II take? Timelines from 41 audits
meta_description: Most SOC 2 Type II audits take 6 to 9 months end to end. Here is where the time goes, from 41 audits we ran in 2025 and 2026.
slug: soc-2-type-ii-timeline
canonical_url: https://example.com/blog/soc-2-type-ii-timeline
site: example.com
primary_keyword: soc 2 type ii timeline
secondary_keywords: [soc 2 audit duration, soc 2 observation period]
language: en
schema_type: BlogPosting
date_published: 2026-11-25
date_modified: 2026-11-25
author:
  - name: Jane Doe
    url: https://example.com/about/jane
    jobTitle: Compliance lead, 40+ SOC 2 audits
    sameAs: https://www.linkedin.com/in/janedoe
publisher:
  name: Example Inc
  url: https://example.com
  logo: https://example.com/logo.png
images: [https://example.com/img/soc2-16x9.png, https://example.com/img/soc2-4x3.png, https://example.com/img/soc2-1x1.png]
---
```

The body starts with exactly one `# ` heading, the title. Put footnotes (`[^1]`) or inline links in the same sentence as every figure.

## ledger.json

```json
{
  "info_gain": [
    {
      "claim": "Median Type II observation window across 41 audits was 6 months",
      "type": "first_party_data",
      "source": "analysis.py over audits.csv (n=41, Jan 2025 to Oct 2026)",
      "evidence": "median observation window was 6 months",
      "section": "How long is the observation period?"
    }
  ],
  "claims": [
    {"text": "Type II requires an observation period", "class": "consensus", "source": "https://www.aicpa-cima.com/..."},
    {"text": "Median window was 6 months (n=41)", "class": "net_new", "source": "analysis.py"}
  ],
  "consensus_skipped": [{"topic": "history of SOC 2", "reason": "reader task is planning a timeline; history doesn't help"}]
}
```

Field rules:

- `type` is one of `first_party_data`, `experience`, `expert_quote`, `original_analysis`, `public_primary`, `contradiction_with_evidence`.
- `evidence` is a short phrase that appears verbatim in the article. The audit matches it after normalizing case and punctuation.
- `claims[].class` is one of `consensus`, `net_new`, `contradiction` or `unsupported`.
  - List the article's substantive claims here.
  - A `net_new` or `contradiction` claim without a `source` fails the audit.
  - The IG ratio is supported net-new claims divided by all claims. The target is at least 0.15, with at least 3 net-new claims.

## sources.md

List every source fetched this run, one per line, with its URL, title, publisher, the date it was fetched, and the claim it supports. First-party sources list the script or file that produced them.

## post-publish.md

```markdown
# Post-publish plan: <title>

## Day 0
- [ ] Publish from the CMS draft after human review; confirm the live URL returns 200 and renders the JSON-LD (view source).
- [ ] Request indexing (Search Console URL Inspection) and submit to IndexNow if the site uses it.
- [ ] Add links from these existing pages, with the anchor text shown: <page> → "<anchor>" (3 to 5, picked from pages that already rank or get traffic for related terms).

## Track
- Primary keyword position: <tool or Search Console query filter>, check at day 14, 30, 60.
- AI citations: ask these prompts in ChatGPT, Perplexity, Gemini and Google AI Mode at day 30 and 60, and log whether the page is cited:
  1. <the query as a question>
  2. <2 or 3 fan-out sub-questions from PAA>
- Engagement: <analytics> scroll depth or time on page for this URL vs the blog median.

## Refresh
- Refresh date: <date 6 to 12 months out, sooner if the first-party data has a natural update cycle>.
- What to refresh: rerun <analysis.py> on new data; recheck must-cover topics against the then-current top 10.
- Update `dateModified` only when the content materially changes.

## Distribution
- Pull 2 to 3 standalone findings (the info-gain items) as social or newsletter snippets, each linking back.
```
