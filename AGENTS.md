# Minerva Rubric Feedback Agent

Give actionable, specific feedback on how well a student applied and contextualized a Minerva rubric (HC / LO) in an assignment. Reads from local PDF or Google Drive, evaluates every tagged HC across three dimensions using parallel discipline agents.

---

## Invocation

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

Parse arguments as follows:
- Token matching `https://docs.google.com/document/d/...` → **Google Docs URL**
- Token matching `https://forum.minerva.edu/...` → **past-assignment URL** to scrape
- Token in double quotes → **Drive title search**
- All other tokens → **rubric filter**
- Empty → local PDF, evaluate every HC tag found

---

## Workflow

### Step 1 — Parse arguments

Classify each token:
- `https://docs.google.com/document/d/...` → set `drive_doc_url`
- `https://forum.minerva.edu/...` → add to `minerva_url_list`
- Double-quoted string → set `drive_search_title`
- Otherwise → add to `rubric_filter`

### Step 2 — Scrape past-assignment URLs (if any)

If `minerva_url_list` is non-empty:

```bash
python3 scripts/scrape-feedback.py URL1 URL2 ...
```

Browser opens for Google SSO login. Saves `*-feedback.md` per URL into `references/past-assignments/`. Stop on error.

### Step 3 — Find the current assignment

**Path A — Google Docs URL:**
1. Extract file ID from `/d/<id>/` segment.
2. Use Google Drive MCP tool to confirm file exists and is accessible.
3. Stop if not found or permission denied.

**Path B — Drive title search:**
1. Search Google Drive: `title contains '<drive_search_title>'`
2. No results → stop. Multiple → list and ask. One → use it.

**Path C — Local PDF:**
Glob `assignment/*.pdf`. One file → use it. Multiple → ask. None → tell user to add a PDF or provide a Drive source.

### Step 4 — Read assignment content

**Drive (Path A/B):** Read file content via Google Drive MCP. Preserve footnote markers.

**Local (Path C):** Read the PDF. If garbled (scanned), say so and stop.

Always re-read fresh.

### Step 5 — Detect rubrics

- `rubric_filter` empty → scan for all `#rubric` hashtag tags in body + footnotes.
- `rubric_filter` set → evaluate only those rubrics.

Tagging channels: inline hashtag + footnote number (A), footnote-only (B), user-specified location (C).

### Step 6 — Load rubric definitions and professor feedback

**Rubric definitions:** Read `.claude/skills/rubric-feedback/references/rubrics/<name>.md` for each rubric. If missing, ask user to paste the definition.

**Professor feedback:**
1. Glob `references/past-assignments/*-feedback.md`.
2. Read all files. Compile all professor comments (rubric-specific + overall).
3. None found → skip dimension (c), note "No past feedback on file."

### Step 7 — Dispatch 6 parallel agents

Dispatch all simultaneously. Use **Sonnet** for discipline agents, **Haiku** for grammar/typo agents.

| Agent | Model | Input |
|-------|-------|-------|
| Social Science | Sonnet | Assignment + `hc_social_science.md` + past feedback |
| Art & History | Sonnet | Assignment + `hc_art_history.md` + past feedback |
| Computer Science | Sonnet | Assignment + `hc_computer_science.md` + past feedback |
| Natural Science | Sonnet | Assignment + `hc_natural_science.md` + past feedback |
| Grammar Check | Haiku | Assignment text only |
| Typo & Spelling | Haiku | Assignment text only |

Each discipline agent follows `agents/discipline-agent.md`. Skip a discipline agent if `rubric_filter` contains no rubrics from that discipline.

If an agent fails: log a warning and continue — do not halt.

### Step 8 — Coordinator synthesis

Spawn one coordinator agent (**Sonnet**) following `agents/coordinator-agent.md`.

Provide all 6 agent outputs. Coordinator merges, deduplicates, orders by page/section, appends grammar/typo findings, writes one Overall verdict.

### Step 9 — Deliver feedback

Output coordinator's report. English only. No preamble.

Target: 8–15 lines per HC. Don't manufacture weaknesses.

---

## Rubric Reference Files

Located in `.claude/skills/rubric-feedback/references/rubrics/`:

| File | Discipline |
|------|-----------|
| `hc_social_science.md` | Social Science (SS) |
| `hc_art_history.md` | Art & History (AH) |
| `hc_computer_science.md` | Computer Science (CS) |
| `hc_natural_science.md` | Natural Science (NS) |
| `audience.md`, `thesis.md`, `composition.md`, etc. | Cross-disciplinary |

Agent templates: `agents/discipline-agent.md`, `agents/coordinator-agent.md`

---

## MCP — Google Drive

Requires Google Drive MCP for Drive-sourced assignments. Configure your MCP client with:

```
Server URL: https://drivemcp.googleapis.com/mcp/v1
Auth: OAuth 2.0 (Google account)
```

---

## Anti-patterns

- Generic praise without evidence → always say why
- Validating weak footnotes as "adequate" → call Weak
- Vague action items ("be more specific") → name exactly what to add/change
- Body–footnote mismatch → flag every time
- Hedging language ("might," "perhaps") → state judgments directly
- Padding → no pre-summaries of rubric or assignment
