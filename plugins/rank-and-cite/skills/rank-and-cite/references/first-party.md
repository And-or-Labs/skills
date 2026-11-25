# First-party material (Gate 4)

First-party material is what makes this article different from the ten it competes with: something only the user or their company has. Each method below fills one kind of gap. Pick the method that fills the **top** gap, and keep it inside its scope cap. The article needs three to five net-new items, not a research programme.

Before asking the user for anything, look for the data yourself:

- MCP connectors already attached, such as a database, warehouse, product analytics, CRM, support desk, or call notes
- data files in the project
- the brand's existing case studies

Propose what you find: "Your PostHog project has 90 days of onboarding funnel data; I can pull the drop-off by step."

## 1. Query their data

**Fills:** figures the SERP quotes without a primary source, "how common is X" questions, benchmarks.

**Ask for:** one connection or export, and the exact metric, filter and time window. Make the ask specific: "median days from signup to first invoice, accounts created Jan to Sep 2026". Don't ask for "your data".

**Scope cap:** at most 3 queries. Produce 1 table and up to 5 figures.

**Process:**
- Read-only queries only.
- Compute in a saved script (`analysis.py` or `.sql` plus its output) so every figure is reproducible.
- State the sample size, the window and the definitions next to each figure in the article.
- Round to a precision the sample supports.
- If the sample is under about 30, say so, or use the figure as an illustration rather than a statistic.
- Never publish personal data or customer names unless the user confirms they're public.

## 2. Expert interview

**Fills:** "how do practitioners actually do this", judgment calls, failure modes, opinions with reasons.

**Ask for:** answers from the user or a named expert, in text, a voice memo transcript or a call transcript.

**Scope cap:** 5 to 8 questions. Expect 15 minutes of the expert's time.

**Write the questions from the gaps, not from a template.** Each one should be unanswerable from the top 10. Patterns that work:

- "Most guides say <consensus claim>. Where does that break in your experience?"
- "Walk me through the last time you <did the task>. What went wrong first?"
- "What number do you watch to know <outcome> is working, and what's a bad value?"
- "What would you tell someone in <reader's role> to stop doing?"
- "What's a tool or step everyone recommends that you skip, and why?"

**Process:**
- Quote verbatim with attribution: name, role, and how they know.
- Keep the expert's own phrasing. It is the most human text in the article, so the humanizer pass must leave it alone.

## 3. Customer evidence

**Fills:** real objections, real outcomes, the words buyers use.

**Ask for:** 5 to 20 items, such as support tickets, sales call notes, reviews, or case results tied to the topic.

**Scope cap:** one pass over at most 20 items.

**Process:**
- Code the items into themes and count them in code ("7 of 15 tickets asked about X").
- Quote short phrases only after stripping identifiers.
- Use outcomes only when the user confirms they can be published.

## 4. Original test or teardown

**Fills:** "does X actually work", comparisons, claims nobody has checked.

**Ask for:** a go-ahead, and any account or access the test needs.

**Scope cap:** one test you can finish in this session against public tools, pages or the user's own product, with no paid sign-ups unless the user offers.

**Process:**
- Write down the method before running it.
- Save the raw results and screenshots in the run folder.
- Report what happened, including a null result. "We expected X and got Y" is information gain.

## Public primary sources (the only non-first-party route past the gate)

If the user has nothing, the gate can still pass, but only on primary public material you actually fetch this run:

- official statistics or regulator data
- vendor documentation that contradicts the SERP consensus
- peer-reviewed papers
- your own fresh analysis of a public dataset, computed in code

Repeating a secondary blog statistic doesn't count. If none of these routes fills a real gap, kill the run.

## Ledger entry

Every item goes into `ledger.json` as described in `output.md`. The audit checks that each `evidence` phrase appears verbatim in the article and has a `source`.
