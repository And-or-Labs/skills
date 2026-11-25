# rank-and-cite

One long-form article per run, built to rank in Google and get cited by AI answer engines, in your own voice. Kill gates stop the run before you spend an afternoon on a page nobody needs.

```
/rank-and-cite:rank-and-cite saas free trial length
```

Or just ask: "write an SEO article for 'saas free trial length' using our trial data".

## What it does

| Stage | What happens | Can it stop the run? |
|---|---|---|
| 0. Profile | First run only: site, author, brand style, 2 to 5 of your writing samples. Saved to `.rank-and-cite/` and reused. | No |
| 1. Demand | One keyword lookup. Kills only if nobody searches: volume is 0 and there's no autocomplete, People Also Ask or forum evidence. | **Yes** |
| 2. SERP read | Top 10, People Also Ask, AI Overview. Format, difficulty and intent shape the brief; they never kill it. | No |
| 3. Gap map | Fetches and parses the top 10, then counts which subtopics are consensus, must-cover or missing. | No |
| 4. Information gain | Shows you the gaps and asks for **one** first-party input to fill them: your data, a short expert interview, customer evidence or a test. Each comes with a scope cap. Nothing net-new means no article. | **Yes** |
| 5. Outline | One approval of a one-screen brief. | You decide |
| 6. Draft | Answer-first, self-contained sections, every figure sourced in its sentence, grounded in your samples. | No |
| 7. Humanize | Always runs: the `humanizer` skill (or the built-in fallback), pointed at your voice, then a fact diff and a voice check. | No |
| 8. Audit | 40+ checks in code covering sourcing, E-E-A-T, answer-first structure, AI tells, links, consensus coverage, info-gain ledger and JSON-LD. Hard fails get fixed before delivery. | Fix loop |
| 9. Deliver | `article.md`, `article.jsonld`, meta, sources, ledger, audit, post-publish plan, plus a CMS **draft** if one is connected. Never publishes. | No |

## The point of view

- **No consensus rehash.** If the article can't add something the top 10 lack, it doesn't get written.
- **Written for the reader's task**, not for a keyword checklist. The mechanical checks run in code so the writing can focus on the reader.
- **No AI slop.** Your samples are the grounding and the humanizer pass is mandatory.
- **Evidence over folklore.** Word count isn't a target, FAQ and HowTo schema are retired, and llms.txt isn't needed. `references/quality-signals.md` tags every claim as Google guidance, a study, or practitioner lore.

## Requirements

- Python 3.9+, stdlib only.
- Web search and page fetch. A fetcher that renders JavaScript (Firecrawl, TinyFish, a browser tool) works best.
- A keyword data source is recommended: DataForSEO, OpenSEO, Ahrefs, Semrush or SerpApi. Without one, the demand gate falls back to free evidence (autocomplete, People Also Ask, forums).
- The [`humanizer`](https://github.com/blader/humanizer) skill is recommended. A fallback checklist is built in.

## Scripts

| Script | Purpose |
|---|---|
| `keyword_gate.py` | Demand verdict and SERP notes, computed in code |
| `serp_extract.py` | Parses a competitor page into headings, word count, schema, dates, author, stats and links |
| `gap_map.py` | Consensus, must-cover and gap bands across the top 10, plus the SERP profile |
| `build_jsonld.py` | BlogPosting, Person, Organization, WebPage and BreadcrumbList `@graph` from frontmatter |
| `audit_draft.py` | The audit gate: hard and soft checks, a scorecard, and a non-zero exit on hard fails |

## Install

```
/plugin marketplace add And-or-Labs/skills
/plugin install rank-and-cite@andorlabs
```

```bash
npx skills add And-or-Labs/skills --skill rank-and-cite
```

## License

MIT. Built by [And/or Labs](https://andorlabs.ca).
