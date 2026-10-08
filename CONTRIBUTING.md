# Contributing

## Adding a new rubric

1. Copy `.claude/skills/rubric-feedback/references/rubrics/audience.md` as a template.
2. Fill in each section:
   - **Rubric definition** — exact wording the school uses (cite the source).
   - **Strong example — body application** — a concrete passage that demonstrates the rubric.
   - **Strong example — contextualization footnote** — the footnote for that passage.
   - **Why this pair works** — explain why the example is strong.
   - **Evaluation criteria** — bullet-level criteria for body and footnote separately.
   - **Common weaknesses** — table with weakness / what-it-looks-like / stronger-version.
3. Add a row to `.claude/skills/rubric-feedback/references/rubrics/INDEX.md` under the correct discipline section.
4. Open a PR. Every rubric definition must include a citation to its official Minerva source.

## Adding a new discipline subagent

1. Open `.claude/settings.json`.
2. Copy one of the existing discipline agent blocks under `hooks.PreToolUse[0].hooks`.
3. Update `prompt`, `statusMessage`, and discipline-specific evaluation criteria.
4. Test with a sample PDF containing rubric tags from that discipline.
5. Add partial-failure handling note if the subagent has unique failure modes.

## PR review criteria

- Rubric definition must cite its official source (Minerva course doc or LO registry).
- Strong examples must be original or anonymized — no real student work without consent.
- Cross-platform changes (Cursor rules, AGENTS.md) must mirror the SKILL.md workflow step-for-step.
- No placeholders (`TODO`, `TBD`) in merged rubric files — placeholder files (NS/SS) are exempt until content is available.
