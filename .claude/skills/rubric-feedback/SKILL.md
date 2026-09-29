---
name: rubric-feedback
description: Give actionable feedback on how well a Minerva-style rubric (HC / LO, tagged like #audience, #thesis, #communication) is applied and contextualized in an assignment PDF. Reads the current PDF from ./assignment/ and past assignments + professor feedback from ./references/past-assignments/. Use for checking rubric applications, contextualization footnotes, and learning-outcome quality before submission.
disable-model-invocation: true
allowed-tools: Read Glob Bash(ls:*) Bash(find:*) Bash(python3:*)
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
```

`$ARGUMENTS` is parsed as follows:
- Tokens starting with `https://` → **past-assignment URLs** to scrape before evaluating
- All other tokens → **rubric filter** (comma-separated or space-separated rubric names)
- Empty → scrape nothing, evaluate every HC tag found in the current assignment

---

## Workflow

### Step 1 — Parse $ARGUMENTS

Split `$ARGUMENTS` by whitespace. Classify each token:
- Starts with `https://` → add to **url_list**
- Otherwise → add to **rubric_filter** (treat the whole non-URL portion as comma-separated rubric names)

### Step 2 — Scrape past-assignment URLs (if any)

If `url_list` is non-empty, run the scrape script once with all URLs:

```bash
python3 scripts/scrape-feedback.py URL1 URL2 ...
```

The script opens a browser window. If the user is not yet logged in, Google SSO will appear — wait for them to log in. The script saves one `*-feedback.md` per URL into `references/past-assignments/` automatically.

If the script exits with an error, report the error and stop — do not proceed on missing data.

### Step 3 — Find the current assignment PDF

Look in `./assignment/` (Glob: `assignment/*.pdf` or `ls assignment/`).

- **Exactly one PDF**: use it.
- **Multiple PDFs**: list filenames and ask which one. Don't guess.
- **No PDFs**: tell the user to drop a PDF into `./assignment/` and retry.

### Step 4 — Read the current PDF

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
