# Voice: capture, persist, ground, humanize

An article without a voice reads like every other generated page, even when the facts are new. The user's own writing is the cure, so it is collected once and reused on every run.

## Where it lives

```
.rank-and-cite/                     # in the project; else ~/.rank-and-cite/brands/<brand>/
├── profile.md                      # site, CMS, author(s), locale, house rules
├── voice.md                        # distilled voice notes (below), editable by the user
└── samples/                        # the user's writing, verbatim, one file each
    ├── 01-<slug>.md
    └── ...
```

Copy each sample into `samples/` verbatim when you collect it, whether it arrived as a URL, a file or pasted text, because URLs rot. Add `.rank-and-cite/runs/` to `.gitignore` when the project is a git repo. The profile and samples may be committed if the user wants that.

`profile.md` template:

```markdown
# <Brand> profile
- site: example.com
- cms: sanity (project abc123, dataset production, type post) | wordpress | none
- locale: us-en
- authors:
  - name: Jane Doe
    url: https://example.com/about/jane
    jobTitle: Head of Lifecycle, 12 years in B2B email
- house rules: no em dashes; no exclamation marks; British spelling; never say "leverage"
- style guide: <path or URL, or "see voice.md">
```

## Distilling voice.md

Read every sample in full. Then write `voice.md` with the sections below. Each observation needs a short quoted example from a sample, because a voice note without an example is a guess.

- **Stance:** who the writer is to the reader, such as a peer, a teacher or a skeptic. How sure they sound.
- **Rhythm:** typical sentence length and how it varies. Paragraph length. Whether they use fragments.
- **Diction:** words and phrases they actually use. Jargon they keep, and jargon they translate. Spelling conventions.
- **Moves:** how they open, how they make a point land, how they use examples, numbers, humour and asides.
- **Never:** constructions and words absent from every sample, plus the house rules.
- **Format habits:** headings, lists, bold, tables, link style.

Show the user a 5-line summary of `voice.md` on the first run so they can correct it. Edit the file when they do.

## Grounding the draft

Before drafting, load `voice.md` and at least two full samples into context. When unsure of a phrasing, ask how the samples would put it. Never copy sentences from the samples into the article.

## Humanizer pass

Use the `humanizer` skill when it's installed. Give it the draft and say: "Voice reference: `voice.md` and the samples in `samples/`. Keep every number, quote, link and proper noun unchanged."

After it runs:

- diff the facts against the pre-humanizer draft
- do the voice check from SKILL.md step 7

### Humanizer fallback

If the `humanizer` skill isn't installed, do the pass yourself. Read each paragraph and fix the patterns below, strongest first. The general rule is that every sentence must add something the reader didn't already have.

1. **"Not X but Y" contrasts** that add only emphasis. State Y.
2. **One-line closers and dramatic fragments** that repeat the point. Delete them.
3. **Staged run-ups** ("Here's the thing:", "The truth is"). Start at the point.
4. **Forced triads.** Use two items, or four, whatever is true.
5. **Inflated significance** ("pivotal", "testament to", "plays a crucial role"). Replace it with the fact.
6. **Stock AI vocabulary:** delve, landscape, leverage, robust, seamless, unlock, navigate, realm, tapestry, foster, showcase. Use the plain word or the specific noun.
7. **Vague attribution** ("experts say", "studies show"). Name them and link them, or cut the claim.
8. **Dashes as the universal connector.** Use commas, colons, parentheses or full stops.
9. **Bold as decoration, and title-case headings.** Use bold only where a skimmer needs it, and sentence-case headings.
10. **Chatbot residue** ("I hope this helps", "In this article we will"). Delete it.
11. **Uniform rhythm.** Vary sentence length the way the samples do.
12. **Generic examples.** Swap each for a named, dated, specific one from the research or the first-party material.

Don't over-correct. If a pattern appears in the user's own samples, it's their voice, so keep it.
