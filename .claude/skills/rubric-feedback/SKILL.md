---
name: rubric-feedback
description: Give actionable feedback on how well a Minerva-style rubric (HC / LO, tagged like #audience, #thesis, #communication) is applied and contextualized in an assignment PDF. Reads the current PDF from ./assignment/ and past assignments + professor feedback from ./references/past-assignments/. Use for checking rubric applications, contextualization footnotes, and learning-outcome quality before submission.
disable-model-invocation: true
allowed-tools: Read Glob Bash(ls:*) Bash(find:*) Bash(python3:*) mcp__claude_ai_Google_Drive__search_files mcp__claude_ai_Google_Drive__read_file_content mcp__claude_ai_Google_Drive__get_file_metadata
---

# Rubric Feedback

Give actionable, specific feedback on how well a student applied and contextualized a rubric (HC / LO) in a PDF assignment.

## Invocation

```
/rubric-feedback
/rubric-feedback audience
/rubric-feedback audience,thesis
/rubric-feedback https://forum.minerva.edu/.../assessments/123
/rubric-feedback https://url1 https://url2
/rubric-feedback https://url1 https://url2 audience
/rubric-feedback https://docs.google.com/document/d/<id>/edit
/rubric-feedback https://docs.google.com/document/d/<id>/edit audience
/rubric-feedback "My Assignment Title"
/rubric-feedback "My Assignment Title" audience,thesis
```

`$ARGUMENTS` is parsed as follows:
- Token matching `https://docs.google.com/document/d/...` → **Google Docs URL** (read assignment from Drive)
- Token matching `https://forum.minerva.edu/...` → **past-assignment URL** to scrape before evaluating
- Token wrapped in double quotes (e.g. `"Essay Title"`) → **Drive title search** (search Drive for that filename)
- All other tokens → **rubric filter** (comma-separated or space-separated rubric names)
- Empty → use local PDF from `./assignment/`, evaluate every HC tag found

---

## Workflow

### Step 1 — Parse $ARGUMENTS

Split `$ARGUMENTS` by whitespace (respecting quoted strings). Classify each token:
- Matches `https://docs.google.com/document/d/<id>...` → set **drive_doc_url** (extract file ID from path)
- Matches `https://forum.minerva.edu/...` → add to **minerva_url_list**
- Wrapped in double quotes → set **drive_search_title** (strip quotes)
- Otherwise → add to **rubric_filter** (comma-separated rubric names)

### Step 2 — Scrape past-assignment URLs (if any)

If `minerva_url_list` is non-empty, run the scrape script once with all URLs:

```bash
python3 scripts/scrape-feedback.py URL1 URL2 ...
```

The script opens a browser window. If the user is not yet logged in, Google SSO will appear — wait for them to log in. The script saves one `*-feedback.md` per URL into `references/past-assignments/` automatically.

If the script exits with an error, report the error and stop — do not proceed on missing data.

### Step 3 — Find the current assignment

**Path A — Google Docs URL** (`drive_doc_url` is set):
1. Extract the file ID from the URL: the segment between `/d/` and the next `/` or `?`.
2. Call `mcp__claude_ai_Google_Drive__get_file_metadata` with that file ID to confirm the file exists and is accessible.
3. If not found or permission denied: report the error and stop.

**Path B — Drive title search** (`drive_search_title` is set):
1. Call `mcp__claude_ai_Google_Drive__search_files` with query: `title contains '<drive_search_title>'`
2. If no results: tell the user no file with that title was found in Drive and stop.
3. If multiple results: list titles + last-modified dates and ask the user which one. Don't guess.
4. If exactly one result: use it.

**Path C — Local PDF** (neither Drive option set):
Look in `./assignment/` (Glob: `assignment/*.pdf` or `ls assignment/`).
- Exactly one PDF: use it.
- Multiple PDFs: list filenames and ask which one. Don't guess.
- No PDFs: tell the user to drop a PDF into `./assignment/` or provide a Google Docs URL / title.

### Step 4 — Read the current assignment content

**Path A or B (Drive):**
Call `mcp__claude_ai_Google_Drive__read_file_content` with the resolved file ID.
- If content is empty or the file type is unsupported: report the error and stop.
- Treat the returned text as the assignment body. Footnote markers may appear as numbered references — preserve them.

**Path C (Local PDF):**
Use the Read tool on the PDF path. Preserve footnote markers — losing them breaks evaluation. If text looks garbled (scanned PDF), say so and stop.

Always re-read fresh even if the same file appeared in earlier messages.

### Step 5 — Determine which rubric(s) to evaluate

- **rubric_filter is empty**: scan body and footnotes for hashtag tags (`#audience`, `#thesis`, etc.). Evaluate every application found.
- **rubric_filter is set**: evaluate only those rubrics. If a named rubric isn't tagged anywhere in the PDF, say so.

Tagging channels — handle any combination:
- **Channel A** — inline hashtag + linked footnote number.
- **Channel B** — footnote only. Rubric named inside the footnote; body is the attached paragraph.
- **Channel C** — user pointed to a location explicitly in chat.

### Step 6 — Load rubric definitions and past professor feedback

**Rubric definitions:** For each rubric, read `.claude/skills/rubric-feedback/references/rubrics/<rubric-name>.md`. See `references/rubrics/INDEX.md` for the list.

If no reference file exists: "I don't have a reference file for `#<rubric>` yet — paste the rubric definition and a strong example and I can evaluate against that standard."

**Past professor feedback:**
1. Glob `references/past-assignments/*-feedback.md` to find all feedback files.
2. Read every feedback `.md` file. Collect all professor comments that apply to the rubric(s) being evaluated.
3. If no feedback files exist: skip dimension (c) and note "No past feedback on file."

### Step 7 — Evaluate three dimensions per HC application

Each dimension is independent — they fail and pass separately.

**Dimension (a) — Body HC Contextualization**

Does the body text actually demonstrate and contextualize the HC, or is the tag performative?

- Is there a specific, visible choice that embodies the HC — something a reader without the tag would still recognize?
- Is the move deliberate (not just incidental to how the piece would have been written anyway)?
- Does it resemble the strong body example in the rubric reference?

**Dimension (b) — Footnote: How Strong**

Rate: **Strong / Adequate / Weak**

- Does it name the *specific choice* made? ("I adjusted it" ≠ "I removed the jargon and replaced it with a cooking analogy.")
- Does it tie the choice to the rubric criteria with a visible "because" link?
- Does it go beyond paraphrasing the rubric definition?
- Could someone reading only the footnote understand exactly what move was made and why?

**Dimension (c) — Prof. Feedback Reflection**

For each issue the professor flagged in any past feedback file for this rubric:
- State the issue and which past assignment it came from.
- State whether the current draft: **addressed / partially addressed / not addressed**.
- Give one-line evidence.

If no past feedback exists for this rubric: write "No past feedback on file for #<rubric>."

### Step 8 — Deliver feedback

Use this format for each HC application. Write in **English**. No preamble, no restating what the student knows.

```
**#<rubric>** — <page or section>

**(a) Body (HC Contextualization)**
<One-line evaluation: what the move is and whether it actually demonstrates the HC.>
Action items:
- <specific, concrete action — not "be more specific" but exactly what to add/change>
- <second item if needed>

**(b) Footnote** — <Strong / Adequate / Weak>
<One-line reason for the rating.>
Action items:
- <if Weak or Adequate: concrete rewrite suggestion or what's missing>

**(c) Prof. Feedback Reflection**
- [<past assignment name>] Professor flagged: <issue>. Current draft: <addressed / partially / not addressed> — <evidence>.
- (repeat per past issue)
Action items:
- <only if something is unaddressed: what exactly to fix>
```

Target: 8–15 lines per HC application. If all three dimensions are strong, say so in one line each and stop. Don't manufacture weaknesses.

Separate multiple HC applications with a blank line. Add a one-line overall verdict at the end only if it adds something new.

---

## Failure modes — check every run

1. **Generic praise.** "Nice application!" → say *why* it works or what's weak.
2. **Validating weak work.** Footnote paraphrases the rubric? Call it Weak, not "adequate."
3. **Vague action items.** "Be more specific" ❌ → "Add one sentence naming [audience] and [move] and [why]: 'Shortened to 5 min for directors because they care about ROI, not specs.'" ✅
4. **Body–footnote mismatch.** Footnote claims a move the body doesn't show — flag it every time.
5. **Hedging.** Drop "might be," "perhaps," "could be argued." State judgments directly.
6. **Padding.** No pre-summaries of the rubric, the assignment, or your upcoming critique.
