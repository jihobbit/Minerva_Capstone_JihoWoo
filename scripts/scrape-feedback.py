#!/usr/bin/env python3
"""
Scrape Minerva assignment feedback via the nested_for_grader API and save as .md.

Usage:
  python3 scripts/scrape-feedback.py URL1 [URL2 URL3 ...]

  Each URL is a Minerva assignment-grader page:
    https://forum.minerva.edu/app/assignment-grader/<assignment_id>

Output:
  .claude/skills/rubric-feedback/references/past-assignments/<title>-feedback.md
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright, Page

SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR   = PROJECT_ROOT / ".claude/skills/rubric-feedback/references/past-assignments"

LOGIN_TIMEOUT_MS = 120_000
LOAD_TIMEOUT_MS  = 20_000


# ── Login ────────────────────────────────────────────────────────────────────

def is_login_page(url: str, page_text: str) -> bool:
    url_signals  = ["accounts.google.com", "/login", "/signin", "/auth", "/sso"]
    text_signals = ["sign in to forum", "continue with google", "use email and password"]
    return (
        any(s in url.lower() for s in url_signals)
        or any(s in page_text.lower() for s in text_signals)
    )


async def ensure_logged_in(page: Page, target_url: str):
    await page.goto(target_url, timeout=30_000)
    await page.wait_for_load_state("domcontentloaded")
    body = await page.evaluate("() => document.body.innerText")

    if is_login_page(page.url, body):
        print("\n[!] Login page detected. Please log in in the browser window.")
        print("    Waiting up to 2 minutes...\n")
        import time
        deadline = time.time() + LOGIN_TIMEOUT_MS / 1000
        while time.time() < deadline:
            await asyncio.sleep(2)
            try:
                txt = await page.evaluate("() => document.body.innerText")
                if not is_login_page(page.url, txt):
                    break
            except Exception:
                pass
        else:
            raise TimeoutError("Login timed out.")
        print("[✓] Login successful!\n")

    if target_url not in page.url:
        await page.goto(target_url, timeout=30_000)


# ── API capture ──────────────────────────────────────────────────────────────

async def fetch_grader_api(page: Page, assignment_id: str) -> dict:
    """Navigate to the assignment page and capture the nested_for_grader API response."""
    api_key = f"/api/v1/assignments/{assignment_id}/nested_for_grader"
    captured = {}

    async def on_response(response):
        if api_key in response.url:
            try:
                captured["data"] = await response.json()
            except Exception:
                pass

    page.on("response", on_response)
    url = f"https://forum.minerva.edu/app/assignment-grader/{assignment_id}"
    await page.goto(url, timeout=30_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=LOAD_TIMEOUT_MS)
    except Exception:
        pass
    await asyncio.sleep(2)
    page.remove_listener("response", on_response)

    if "data" not in captured:
        raise RuntimeError(f"API response not captured for assignment {assignment_id}. "
                           "Make sure you are logged in and the URL is correct.")
    return captured["data"]


# ── Parsing ──────────────────────────────────────────────────────────────────

def parse_feedback(api_data: dict) -> dict:
    """Extract structured feedback from the nested_for_grader API response."""

    title = api_data.get("title", "Unknown Assignment")

    # Build LO id → description map from focused-outcomes
    lo_map: dict[int, str] = {}
    for fo in api_data.get("focused-outcomes", []):
        lo = fo.get("learning-outcome")
        if lo and lo.get("id"):
            lo_map[lo["id"]] = lo.get("description", "")

    assessments = api_data.get("outcome-assessments", [])

    # Graded HC assessments (have a score)
    hc_assessments = []
    for item in assessments:
        if item.get("score") is not None:
            lo_id  = item.get("learning-outcome")
            lo_desc = lo_map.get(lo_id, f"LO {lo_id}") if lo_id else "Unknown LO"
            hc_assessments.append({
                "id":      item["id"],
                "lo_id":   lo_id,
                "lo_name": lo_desc,
                "score":   item["score"],
                "comment": (item.get("comment") or "").strip(),
            })

    # Unscored items — find general feedback (bold **Name pattern) and inline annotations
    unscored = [x for x in assessments if x.get("score") is None]
    general_feedback = ""
    inline_annotations = []

    for item in unscored:
        comment = (item.get("comment") or "").strip()
        if not comment:
            continue
        # General feedback: bold opening (starts with **) or longest comment
        if comment.startswith("**"):
            general_feedback = comment
        else:
            inline_annotations.append(comment)

    # Fallback: if no bold comment, use the longest unscored comment
    if not general_feedback and unscored:
        longest = max(unscored, key=lambda x: len(x.get("comment") or ""), default=None)
        if longest:
            general_feedback = (longest.get("comment") or "").strip()
            inline_annotations = [
                (x.get("comment") or "").strip()
                for x in unscored
                if x is not longest and x.get("comment")
            ]

    return {
        "title":               title,
        "hc_assessments":      hc_assessments,
        "general_feedback":    general_feedback,
        "inline_annotations":  inline_annotations,
    }


def build_md(parsed: dict, url: str) -> str:
    lines = [
        f"# Minerva Feedback — {parsed['title']}",
        "",
        "## Source URL",
        url,
        "",
        "## General Feedback",
        "",
        parsed["general_feedback"] or "*(not found)*",
        "",
        "## HC / LO Assessments",
        "",
    ]

    if parsed["hc_assessments"]:
        for hc in parsed["hc_assessments"]:
            lines += [
                f"### {hc['lo_name']}",
                f"**Score:** {hc['score']}",
                "",
                hc["comment"] or "*(no comment)*",
                "",
            ]
    else:
        lines += ["*(no graded HC assessments found)*", ""]

    if parsed["inline_annotations"]:
        lines += ["## Inline Annotations", ""]
        for ann in parsed["inline_annotations"]:
            lines += [f"- {ann}", ""]

    return "\n".join(lines)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", text).strip("-")[:60]


# ── Main ─────────────────────────────────────────────────────────────────────

async def scrape_one(page: Page, url: str, first: bool) -> Path:
    m = re.search(r"/assignment-grader/(\d+)", url)
    if not m:
        raise ValueError(f"Cannot extract assignment ID from URL: {url}")
    assignment_id = m.group(1)

    print(f"[→] assignment {assignment_id}")

    if first:
        await ensure_logged_in(page, url)
        pages = page.context.pages
        page = pages[-1] if pages else page
    else:
        await page.goto(url, timeout=30_000)

    api_data = await fetch_grader_api(page, assignment_id)

    parsed = parse_feedback(api_data)
    slug   = slugify(parsed["title"]) or f"assignment-{assignment_id}"
    out    = OUTPUT_DIR / f"{slug}-feedback.md"

    out.write_text(build_md(parsed, url), encoding="utf-8")
    print(f"    Saved: {out.name}  ({len(parsed['hc_assessments'])} HC assessments)")
    return out


async def main(urls: list[str]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, slow_mo=80)
        context = await browser.new_context()
        page    = await context.new_page()

        saved = []
        for i, url in enumerate(urls):
            path = await scrape_one(page, url, first=(i == 0))
            saved.append(path)

        await browser.close()

    print(f"\n[✓] Done. {len(saved)} file(s):")
    for p in saved:
        print(f"    {p}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    urls = [a for a in sys.argv[1:] if a.startswith("https://")]
    if not urls:
        print("Error: no https:// URLs found.")
        sys.exit(1)

    asyncio.run(main(urls))
