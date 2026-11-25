# Data providers and fallbacks

Use whatever the user already has before anything paid. Make one lookup at a time, never in bulk. Save every raw response in the run folder so a retry never pays twice. Name the provider you used in the status line.

**Credentials stay in the environment.** Reference keys only as shell variables (`"$SERPAPI_KEY"`, `"$DATAFORSEO_LOGIN"`) inside the command, so the shell expands them at run time. Never read, print or echo a key's value, and never paste one into a URL, tool argument, saved file or status line. If a variable isn't set, skip that provider; don't ask the user to paste the key into chat.

## Keyword volume (Gate 1)

Try these in order and stop at the first that answers:

1. **A connected keyword MCP or tool**, such as OpenSEO (`get_keyword_metrics`), Ahrefs, Semrush, SE Ranking, Moz, or a Letter/Letterstory-type `research_keywords`. Request the single keyword plus related keywords in one call.
2. **The DataForSEO API**, if `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` are in the environment. Run `curl -s -u "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" -H 'Content-Type: application/json' -d '[{"keywords": ["<kw>"], "location_code": <code>, "language_code": "<lang>"}]' https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live`. It costs cents per call. For related terms, use `dataforseo_labs/google/related_keywords/live` with `limit: 20`.
3. **A number from the user.** Ask once if they have Search Console, Keyword Planner or a tool export.
4. **Demand evidence**, when there is no number. This step is free:
   - Google autocomplete (`https://suggestqueries.google.com/complete/search?client=firefox&q=<kw>`)
   - People Also Ask, from a SERP fetch
   - Reddit, Quora or forum threads (a web search for the keyword with `site:reddit.com`)
   - Google Trends, if reachable

   Put what you find in `metrics.json` under `demand_evidence`.

Never estimate volume yourself.

## SERP top 10 (step 2)

1. A connected SERP tool, such as OpenSEO `get_serp_results` or a SerpApi or DataForSEO MCP.
2. DataForSEO `serp/google/organic/live/advanced` (depth 10). It returns organic results, People Also Ask, related searches and AI Overview items in one call.
3. SerpApi, if `SERPAPI_KEY` is set. Let the shell supply the key: `curl -s -G https://serpapi.com/search.json --data-urlencode "q=<kw>" -d engine=google -d gl=<cc> -d hl=<lang> --data-urlencode "api_key=$SERPAPI_KEY" > serp/raw.json`. Keep the literal `$SERPAPI_KEY` in the command; never substitute the value.
4. A web search tool's top results. This is not a true Google SERP, so label it `approximate SERP` in the brief and in the audit report.

Some SERP tools return Google redirect links (`https://www.google.com/url?q=<target>&...`). Unwrap the `q` (or `url`) parameter before fetching. If every result is a redirect with no target, the SERP call failed. Fall back to the next provider rather than reading the redirect pages.

Google's Custom Search JSON API is closed to new users and shuts down on 2027-01-01. Don't build on it.

## Page fetch (step 3)

Use a fetcher that renders JavaScript when one is available: Firecrawl, TinyFish `fetch_content`, expand.ai, or a browser tool. Next best is a plain web-fetch tool, then `serp_extract.py --fetch <url>`, which is a stdlib fallback and is often blocked.

Save the raw HTML when you can get it. Markdown loses the JSON-LD, dates and meta tags.

## Site authority (optional, step 2 notes)

Use domain rating or authority from whichever SEO tool is connected. If you have none, leave it `null`. The SERP notes will then say that winnability isn't scored.

## Validation

- **JSON-LD:** `audit_draft.py` checks structure, matching values and dates offline. For a final check, open Google's Rich Results Test (`https://search.google.com/test/rich-results`) with the code, or the schema.org validator (`https://validator.schema.org`), in a browser tool if one is available. There is no public API for the Rich Results Test.
- **Links:** before delivery, send a `HEAD` request (or a `GET`) to every external and internal URL. Anything that doesn't return 2xx or 3xx gets fixed or removed.
