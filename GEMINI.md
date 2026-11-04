# GEMINI.md — minerva-capstone-jihowoo

## Context Usage Monitoring

When you estimate the context window is approximately 75% full, proactively say:
> "Context is around 75% full. Run `/compress` to compress before continuing."

Do not wait until the context is nearly exhausted — compact early to preserve quality.

## Compact Instructions

When compressing context, follow these rules:

### Keep verbatim — last 3 turns
Preserve the most recent 3 conversation turns exactly as-is. Do not summarize or paraphrase them.

### Always preserve after compaction
Regardless of what else is summarized, the compressed context MUST include:

1. **Active rubrics** — the list of rubric tags (`#audience`, `#thesis`, etc.) being evaluated, and which ones have already been evaluated vs. are still pending.

2. **Assignment summary** — a 3–5 sentence summary of the current assignment's argument, structure, and discipline. Do not discard which file or Google Doc is being reviewed.

3. **Professor feedback highlights** — for each rubric being evaluated, any specific issues the professor flagged in past assignments. Keep the exact wording of each flag, not a paraphrase.

4. **Evaluation state** — which dimensions (a/b/c) have been completed per rubric, and any partial findings already written.

### Can be summarized or dropped
- Tool call details (file path lookups, scraper output logs)
- Repeated rubric definition text already loaded from reference files
- Early exploration steps (finding the PDF, confirming file names)
- Grammar/spelling agent raw output (keep only the flagged items, not the full output)

---

## Rubric Feedback Skill

Give actionable, specific feedback on how well a student applied and contextualized a Minerva rubric (HC / LO) in an assignment.

### Invocation

```
rubric-feedback
rubric-feedback audience
rubric-feedback audience,thesis
rubric-feedback https://forum.minerva.edu/.../assessments/123
rubric-feedback https://docs.google.com/document/d/<id>/edit
rubric-feedback https://docs.google.com/document/d/<id>/edit audience
rubric-feedback "My Assignment Title"
rubric-feedback "My Assignment Title" audience,thesis
```

Parse arguments:
- `https://docs.google.com/document/d/...` → Google Docs URL
- `https://forum.minerva.edu/...` → past-assignment URL to scrape
- Double-quoted string → Drive title search
- All other tokens → rubric filter
- Empty → local PDF, evaluate every HC tag found

### Workflow

**Step 1 — Parse arguments** (classify tokens as above)

**Step 2 — Scrape past-assignment URLs (if any)**
```bash
python3 scripts/scrape-feedback.py URL1 URL2 ...
```
Saves `*-feedback.md` per URL into `references/past-assignments/`. Stop on error.

**Step 3 — Find the current assignment**
- Google Docs URL → extract file ID, read via Google Drive MCP
- Drive title search → search Drive, disambiguate if multiple results
- Local PDF → Glob `assignment/*.pdf`

**Step 4 — Read assignment content**
Preserve footnote markers. Stop if garbled or unsupported format.

**Step 5 — Detect rubrics**
Scan for `#rubric` hashtags, or use `rubric_filter` if set.

**Step 6 — Load rubric definitions and professor feedback**
- Read `references/rubrics/<name>.md` per rubric
- Read all `references/past-assignments/*-feedback.md`

**Step 7 — Dispatch 6 parallel agents**

| Agent | Model | Input |
|-------|-------|-------|
| Social Science | Gemini 2.5 Pro | Assignment + `hc_social_science.md` + past feedback |
| Art & History | Gemini 2.5 Pro | Assignment + `hc_art_history.md` + past feedback |
| Computer Science | Gemini 2.5 Pro | Assignment + `hc_computer_science.md` + past feedback |
| Natural Science | Gemini 2.5 Pro | Assignment + `hc_natural_science.md` + past feedback |
| Grammar Check | Gemini 2.5 Flash | Assignment text only |
| Typo & Spelling | Gemini 2.5 Flash | Assignment text only |

Each discipline agent follows `agents/discipline-agent.md`. Skip agents whose discipline has no matching rubrics in `rubric_filter`. If an agent fails, log a warning and continue.

**Step 8 — Coordinator synthesis**
Spawn one coordinator agent (Gemini 2.5 Pro) following `agents/coordinator-agent.md`. Merges, deduplicates, orders by page/section, appends grammar/typo findings, writes one Overall verdict.

**Step 9 — Deliver feedback**
Output coordinator's report. English only. No preamble. 8–15 lines per HC.

### Anti-patterns
- Generic praise without evidence
- Validating weak footnotes as "adequate" — call Weak
- Vague action items — name exactly what to add/change
- Body–footnote mismatch — flag every time
- Hedging language — state judgments directly
