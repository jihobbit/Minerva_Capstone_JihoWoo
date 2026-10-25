# CLAUDE.md — minerva-capstone-jihowoo

## Context Usage Monitoring

When you estimate the context window is approximately 75% full, proactively say:
> "Context is around 75% full. Run `/compact` to compress before continuing."

Do not wait until the context is nearly exhausted — compact early to preserve quality.

## Compact Instructions

When compacting (via `/compact` or auto-compaction), follow these rules:

### Keep verbatim — last 3 turns
Preserve the most recent 3 conversation turns exactly as-is. Do not summarize or paraphrase them.

### Always preserve after compaction
Regardless of what else is summarized, the compacted context MUST include:

1. **Active rubrics** — the list of rubric tags (`#audience`, `#thesis`, etc.) being evaluated in the current session, and which ones have already been evaluated vs. are still pending.

2. **Assignment summary** — a 3–5 sentence summary of the current assignment's argument, structure, and discipline. Do not discard which assignment file or Google Doc is being reviewed.

3. **Professor feedback highlights** — for each rubric being evaluated, any specific issues the professor flagged in past assignments. Keep the exact wording of each flag, not a paraphrase.

4. **Evaluation state** — which dimensions (a/b/c) have been completed per rubric, and any partial findings already written.

### Can be summarized or dropped
- Tool call details (Glob results, file path lookups, scraper output logs)
- Repeated rubric definition text already loaded from reference files
- Early exploration steps (finding the PDF, confirming file names)
- Grammar/spelling subagent raw output (keep only the flagged items, not the full output)
