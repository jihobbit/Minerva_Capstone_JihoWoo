# Minerva Capstone — Rubric Feedback Agent

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/platform-Claude%20Code-blue.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Cursor](https://img.shields.io/badge/platform-Cursor-purple.svg)](https://cursor.so)
[![Codex](https://img.shields.io/badge/platform-Codex-black.svg)](https://openai.com/codex)
[![Gemini CLI](https://img.shields.io/badge/platform-Gemini%20CLI-orange.svg)](https://github.com/google-gemini/gemini-cli)

An AI agent skill that gives structured, actionable feedback on how well a student applied Minerva rubrics (HCs / LOs, e.g. `#audience`, `#thesis`) in an assignment, **before** the assignment is submitted.

**Contents:** [Overview](#overview) · [Features and status](#features-and-status) · [Architecture](#architecture) · [Quick start](#quick-start) · [Usage](#usage) · [Supported rubrics](#supported-rubrics) · [Repository map](#repository-map) · [Known limitations](#known-limitations) · [Requirements](#requirements)

---

## Overview

**Problem.** Minerva students tag their work with rubrics (HCs / LOs) and justify each tag in a footnote. Professors then grade whether the tag is truly demonstrated or merely performative, and repeated feedback from earlier assignments is easy to overlook.

**Solution.** The agent reads an assignment, finds every rubric tag, and evaluates each one on three dimensions:

| Dimension | Question it answers |
|-----------|---------------------|
| **(a) Body** | Does the body text actually demonstrate the rubric, or is the tag performative? |
| **(b) Footnote** | Is the justification Strong / Adequate / Weak, and why? |
| **(c) Past professor feedback** | Did the student address what professors flagged in earlier assignments? |

It also runs a grammar check and a typo/spelling check in parallel and attaches the results to the main feedback.

---

## Features and status

| Feature | Status |
|---------|--------|
| Rubric feedback skill (`/rubric-feedback`) with a, b, c evaluation | Implemented |
| Rubric definitions for 7 rubrics (`references/rubrics/`) | Implemented |
| Scraper for past professor feedback (Playwright, Google SSO) | Implemented |
| Grammar + typo/spell check via two parallel Haiku hook agents | Implemented |
| Google Drive input: read an assignment by Docs URL or title | Implemented |
| Discipline-aware evaluation (AH / CS / NS / SS) run by 4 parallel agents on Sonnet | Specified in `SKILL.md`; agent template and per-discipline rubric files not in the repo yet (see [Known limitations](#known-limitations)) |
| Cross-platform instructions: Cursor, Codex, Gemini CLI | Implemented as instruction files (`.cursor/`, `AGENTS.md`, `GEMINI.md`) |
| Context-compaction rules for long sessions (`CLAUDE.md`, `GEMINI.md`) | Implemented |

---

## Architecture

```
 User prompt:  /rubric-feedback [URLs] [rubrics]
        │
        ▼
 ┌──────────────────────┐   PreToolUse hook (async, 2 × Haiku)
 │ 1. Parse arguments   │──────────────► grammar check ┐
 └──────────┬───────────┘                typo check    ├─► extra context
            ▼                                           ┘   for the feedback
 ┌──────────────────────┐
 │ 2. Scrape past       │  scripts/scrape-feedback.py (Playwright)
 │    feedback (opt.)   │  → references/past-assignments/*-feedback.md
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐   local PDF (./assignment/)
 │ 3. Load assignment   │ ◄─ or Google Drive (Docs URL / title search)
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐
 │ 4. Find #rubric tags │  body + footnotes
 │    load definitions  │  references/rubrics/<name>.md
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐
 │ 5. Evaluate a / b / c│  per rubric application
 └──────────┬───────────┘
            ▼
     Concise, actionable feedback (English)
```

**Design choices**
- **Skill instead of an app:** the agent runs inside tools students already use (Claude Code, Cursor, Codex, Gemini CLI), so there is nothing to host.
- **Cheap parallel checks:** grammar and typos go to small Haiku agents so the main model's context stays focused on rubric reasoning.
- **Fail loudly:** if scraping or reading the assignment fails, the skill stops and reports the error instead of evaluating on missing data.
- **Rubrics as plain Markdown:** adding a rubric means adding one file and one index row.

---

## Quick start

### 1. Install into your project

```bash
cd your-project
npx github:jihobbit/Minerva_Capstone_JihoWoo
```

This copies the skill, the scraper, and an `assignment/` folder into your project.

### 2. Install the scraper dependency (only needed for past feedback)

```bash
pip install playwright && playwright install chromium
```

### 3. Run

```bash
cp my-assignment.pdf assignment/
claude
```

```
/rubric-feedback
```

### Other platforms

| Platform | Setup |
|----------|-------|
| Cursor | Copy `.cursor/rules/rubric-feedback.mdc` to your project's `.cursor/rules/` |
| Codex | `AGENTS.md` at the repo root defines the agent |
| Gemini CLI | `GEMINI.md` at the repo root defines the agent |

---

## Usage

| Command | What it does |
|---------|--------------|
| `/rubric-feedback` | Evaluate every rubric tag found in the PDF in `./assignment/` |
| `/rubric-feedback audience` | Evaluate only `#audience` |
| `/rubric-feedback audience,thesis` | Evaluate several rubrics |
| `/rubric-feedback <minerva-url>` | Scrape past feedback from that assignment first, then evaluate |
| `/rubric-feedback <url1> <url2> audience` | Scrape several past assignments, focus on `#audience` |
| `/rubric-feedback <google-docs-url>` | Read the assignment from Google Drive |
| `/rubric-feedback "My Assignment Title"` | Find the assignment in Drive by title |

Arguments are classified automatically: a Docs URL, a Minerva forum URL, a quoted title, or a rubric name.

---

## Supported rubrics

| Tag | Description |
|-----|-------------|
| `#audience` | Tailor work to the situation and perspective of the receiver |
| `#thesis` | Formulate a well-defined, arguable, and specific thesis |
| `#composition` | Communicate with a clear, precise, parsimonious style |
| `#connotation` | Understand and deliberately use connotations and tone |
| `#constraints` | Identify and apply constraint satisfaction to solve problems |
| `#levelsofanalysis` | Analyze a complex system across multiple levels and interactions |
| `#purpose` | Articulate a mission that connects values, goals, and procedures |

To add a rubric, copy `references/rubrics/audience.md` as a template and add a row to `INDEX.md`.

---

## Repository map

```
.
├── .claude/
│   ├── settings.json                     # Haiku grammar + typo hooks
│   └── skills/rubric-feedback/
│       ├── SKILL.md                      # skill definition and workflow
│       └── references/
│           ├── rubrics/                  # rubric definitions + INDEX.md
│           └── past-assignments/         # written by the scraper
├── .cursor/rules/rubric-feedback.mdc     # Cursor version
├── AGENTS.md                             # Codex version
├── GEMINI.md                             # Gemini CLI version
├── CLAUDE.md                             # compaction rules for long sessions
├── bin/install.js                        # npx installer
├── scripts/
│   ├── scrape-feedback.py                # Playwright scraper
│   └── requirements.txt
├── assignment/                           # drop the PDF here
├── CONTRIBUTING.md
└── LICENSE
```

---

## Known limitations

- **Discipline agents are incomplete.** `SKILL.md` Step 7 dispatches four discipline agents and reads `agents/discipline-agent.md` plus per-discipline HC files. Those files are not in this repository yet, so that step cannot run as written.
- **Not published to npm.** Install with `npx github:...` as shown above.
- **Scraper needs a manual login.** Minerva uses Google SSO, so a browser window opens the first time.
- **Scanned PDFs are unsupported.** If the text layer is garbled, the skill stops and says so.
- **No automated tests.** Behavior has been checked by running the skill manually.

---

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) (or Cursor / Codex / Gemini CLI)
- Node.js ≥ 14 (for `npx`)
- Python 3 + Playwright (only for scraping past feedback)
- Google Drive connector (only for Drive input)

## License

MIT — see [LICENSE](LICENSE).
