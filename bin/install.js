#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const PKG_ROOT = path.join(__dirname, '..');
const CWD = process.cwd();

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.name === '.gitkeep') continue;
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

console.log('Installing minerva-capstone-jihowoo...\n');

// 1. Skill files (.claude/skills/rubric-feedback/)
const skillSrc = path.join(PKG_ROOT, '.claude', 'skills', 'rubric-feedback');
const skillDest = path.join(CWD, '.claude', 'skills', 'rubric-feedback');
copyDir(skillSrc, skillDest);
console.log('✓  .claude/skills/rubric-feedback/');

// 2. Scrape script
const scriptSrc = path.join(PKG_ROOT, 'scripts', 'scrape-feedback.py');
const scriptsDest = path.join(CWD, 'scripts');
fs.mkdirSync(scriptsDest, { recursive: true });
fs.copyFileSync(scriptSrc, path.join(scriptsDest, 'scrape-feedback.py'));
console.log('✓  scripts/scrape-feedback.py');

// 3. assignment/ directory (user drops PDFs here)
const assignmentDir = path.join(CWD, 'assignment');
if (!fs.existsSync(assignmentDir)) {
  fs.mkdirSync(assignmentDir);
  console.log('✓  assignment/');
} else {
  console.log('·  assignment/ already exists — skipped');
}

console.log(`
Done. Next steps:

  1. Install Playwright (needed to scrape past assignment feedback):

       pip install playwright && playwright install chromium

  2. Open Claude Code in this directory:

       claude

  3. Drop your assignment PDF into ./assignment/

  4. In Claude Code, run:

       /rubric-feedback
         — evaluates every rubric tag found in the PDF

       /rubric-feedback https://forum.minerva.edu/app/assignment-grader/<id>
         — scrapes past assignment feedback first, then evaluates

       /rubric-feedback https://url1 https://url2 audience
         — scrape multiple past assignments, focus only on #audience
`);
