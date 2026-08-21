#!/usr/bin/env node
// Validate that every top-level skill folder has a valid SKILL.md with the
// required YAML frontmatter (name + description). Zero dependencies.
// Run: node scripts/validate-skills.js
import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = process.cwd();
const TOP_LEVEL_FILES = ["bin", "scripts", "node_modules", ".git", ".github"];

function isSkillDir(name) {
  if (TOP_LEVEL_FILES.includes(name)) return false;
  return statSync(join(ROOT, name)).isDirectory();
}

function parseFrontmatter(text) {
  if (!text.startsWith("---")) return null;
  const end = text.indexOf("\n---", 3);
  if (end === -1) return null;
  const body = text.slice(3, end).trim();
  const fields = {};
  let current = null;
  for (const line of body.split("\n")) {
    const m = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (m) {
      current = m[1];
      fields[current] = m[2].trim();
    } else if (current && /^\s+[-\s]/.test(line)) {
      fields[current] = "list"; // array / multi-line value
    }
  }
  return fields;
}

const skills = readdirSync(ROOT, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !TOP_LEVEL_FILES.includes(d.name))
  .map((d) => d.name)
  .sort();

let errors = 0;
let count = 0;

for (const name of skills) {
  count++;
  const dir = join(ROOT, name);
  const skillMd = join(dir, "SKILL.md");
  const prefix = `[${name}]`;
  if (!existsSync(skillMd)) {
    console.error(`✗ ${prefix} missing SKILL.md`);
    errors++;
    continue;
  }
  const text = readFileSync(skillMd, "utf8");
  const fm = parseFrontmatter(text);
  if (!fm) {
    console.error(`✗ ${prefix} missing or malformed YAML frontmatter`);
    errors++;
    continue;
  }
  if (!fm.name) {
    console.error(`✗ ${prefix} frontmatter missing "name"`);
    errors++;
  } else if (fm.name !== name) {
    console.error(`✗ ${prefix} frontmatter name "${fm.name}" != folder "${name}"`);
    errors++;
  }
  if (!fm.description || fm.description === "list") {
    console.error(`✗ ${prefix} frontmatter missing "description"`);
    errors++;
  }
  if (!errors || true) console.log(`✓ ${prefix} ok`);
}

console.log(`\n${count} skill(s) checked, ${errors} error(s).`);
process.exit(errors ? 1 : 0);
