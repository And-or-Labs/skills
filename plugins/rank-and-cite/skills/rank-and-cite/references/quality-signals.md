# Quality signals: what matters, what doesn't, and the evidence

Read this once before the first draft. Tags: **[G]** Google first-party guidance. **[S]** a study. **[P]** a practitioner or vendor claim. Where the evidence is thin, it says so. Don't present a [P] item to the user as a rule.

## Google's position in brief

- **E-E-A-T is not a ranking factor in itself; trust is the core of it.** Show who wrote the page (a byline linking to a real bio), how it was made, and why it exists (to help, not to attract visits). Fabricated authors or credentials are deceptive. [G] https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- **AI-written text is not penalized in itself.** Scaled, low-value pages are, "no matter how it's created". Facts, titles, meta descriptions, alt text and structured data must be human-reviewed. [G] https://developers.google.com/search/docs/fundamentals/using-gen-ai-content and https://developers.google.com/search/docs/essentials/spam-policies
- **Google's AI search guidance asks for "non-commodity" content:** a unique point of view and first-hand experience. It says there is no ideal length and no need to chunk content, and that llms.txt and special AI markup are not needed. [G] https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- **Word count is not a ranking factor.** "There's no magical word count." Length follows the topic. [G] SEO starter guide.
- **Information gain** comes from Google patent US11354342B2: a score for how much a document adds beyond what the user has already seen. A patent doesn't prove it is used in production, but it matches the "non-commodity" guidance. The scoring in `output.md` (ledger, IG ratio) is a heuristic, not Google's formula. [G-patent] https://patents.google.com/patent/US11354342B2/en

## What gets cited in AI answers

- **[S] Princeton GEO** (Aggarwal et al., KDD 2024, https://arxiv.org/abs/2311.09735): adding cited sources, quotations and statistics raised visibility in generative answers by roughly 30 to 40%, and keyword stuffing underperformed. The gain was largest for pages that didn't already rank first. The caveats are older models and a synthetic benchmark.
- **[S] Chen and Koudas** (2026 preprint, https://arxiv.org/abs/2610.15033): within a site, pages whose titles and paragraphs match the questions people ask get cited more. FAQ blocks, schema and summary boxes mattered only between sites. Single study.
- **[G] Generative features retrieve from the normal index using sub-queries (fan-out).** Covering the sub-questions is the core job: People Also Ask and related searches are the proxy.
- **[P] Answers sit early.** One analysis found 44% of ChatGPT citations came from the first 30% of a page.
- **Not supported:** llms.txt as a citation driver, and chunking for its own sake.

## Structured data (2026 status)

- **Article / BlogPosting has no required properties.** Recommended: `headline`, `image` (several, 16:9, 4:3 and 1:1, at least 50K pixels), `datePublished`, `dateModified` (ISO 8601 with timezone where possible), and `author` as a Person with `name` and `url`. [G] https://developers.google.com/search/docs/appearance/structured-data/article
- **FAQ rich results were retired in 2026, and HowTo was retired earlier.** The markup is harmless but earns nothing, so `build_jsonld.py` doesn't emit either.
- **BreadcrumbList** shows on desktop only. **Speakable** is a news-only beta. Person and Organization markup support the authorship and publisher signals.
- **The markup must match the visible page.** The headline matches the H1, and the author matches the byline.

## On-page basics

- Use one H1. Give the page a descriptive title, about 60 characters by practitioner convention (Google truncates by pixel width, not a character limit).
- Write a unique meta description of about 70 to 160 characters. Google often rewrites it anyway.
- Give every image descriptive alt text. Use a readable slug.
- Use descriptive anchor text. Link to trustworthy primary sources, and to at least 2 or 3 of the site's own relevant pages.
- Keep main content in server-rendered HTML. Some AI crawlers don't run JavaScript [P].

## AI-writing tells

Wikipedia's "Signs of AI writing" (https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) and the humanizer skill catalogue the patterns:

- inflated significance
- stock vocabulary
- not-X-but-Y constructions
- triads
- vague attribution
- generic conclusions
- decorative bold
- chatbot residue

The root cause is generic claims standing in for specific facts, so the fix is specificity, not synonym swapping. The aim is writing that reads like a person who knows the subject, not evading a detector.

## Judgment review

Answer each question pass or fail, with one line of evidence. Most are adapted from Google's people-first self-assessment.

1. **Reader's task:** would the searcher finish what they came to do without searching again?
2. **Original value:** does it contain original information, analysis or experience? Name the info-gain items.
3. **Beyond the obvious:** is there at least one insight a practitioner would bookmark?
4. **Adds value over its sources:** where it draws on other pages, does it add something rather than rephrase?
5. **Honest title:** is the title descriptive, with no exaggeration or clickbait?
6. **Accuracy:** has every factual claim been checked against its fetched source? Do all quotes match their originals?
7. **Who/How/Why:** is there a real byline with a bio, a process note, and a purpose that serves the reader?
8. **Not written to a word count:** is anything padding? Cut it.
9. **Consensus covered:** are the must-cover topics handled, or skipped with a reason?
10. **Voice:** does it read like the samples rather than like a model?
11. **Business bridge (light touch):** where it naturally helps the reader, is there a pointer to the brand's relevant page or product? A bridge is optional. The article educates first.
12. **Nothing invented:** are there zero fabricated people, quotes, customers, numbers or links?
