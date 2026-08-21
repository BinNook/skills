#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, rmSync, cpSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const VERSION = "0.1.0";
const DEFAULT_REF = "main";
// Where skills commonly live inside a repo, tried in order.
const SKILL_ROOTS = ["", "skills", "skills/.curated", "skills/.experimental"];

function help() {
  console.log(`binnook-skills v${VERSION} - install Codex skills from GitHub

Usage:
  npx binnook-skills add <github-url> --skill <name> [options]
  npx binnook-skills list <github-url> [options]
  npx binnook-skills --version
  npx binnook-skills --help

Commands:
  add    Download a skill folder and copy it into the local skills directory.
  list   List available skill folders in a repository.

Options:
  --skill <name>     Skill folder name to install (required for add).
  --ref <ref>         Git ref (branch/tag/commit), default: main
  --path <relpath>    Custom subdirectory holding skills (overrides auto-detect).
  --dest <path>       Destination skills dir, default: $CODEX_HOME/skills
  --name <name>       Install under a different folder name.
  --force             Overwrite if the destination already exists.

Examples:
  npx binnook-skills add https://github.com/BinNook/skills --skill grill-me
  npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --ref dev --force
  npx binnook-skills list https://github.com/BinNook/skills

Skills are looked up at the repo root, under skills/, skills/.curated,
and skills/.experimental (use --path to override). Installed to
$CODEX_HOME/skills/<name> (defaults to ~/.codex/skills). Requires git.`);
}

function fail(msg, code = 1) {
  console.error(`Error: ${msg}`);
  process.exit(code);
}

function codexHome() {
  return process.env.CODEX_HOME || join(process.env.HOME || "~", ".codex");
}

// Parse https://github.com/<owner>/<repo>[/(tree|blob)/<ref>[/<path>]]
// Also accepts bare owner/repo, ssh URLs, file:// paths, and other git URLs.
function parseGithubUrl(url) {
  let m = url.match(/^https:\/\/github\.com\/([^/]+)\/([^/]+?)(?:\.git)?(?:\/(tree|blob)\/([^/]+?)(?:\/(.*))?)?\/?$/);
  if (m) {
    return { owner: m[1], repo: m[2], ref: m[4] || null, subpath: m[5] || null, repoUrl: null };
  }
  m = url.match(/^git@github\.com:([^/]+)\/([^/]+?)(?:\.git)?$/);
  if (m) {
    return { owner: m[1], repo: m[2], ref: null, subpath: null, repoUrl: url };
  }
  m = url.match(/^([^/\s]+)\/([^/\s]+?)(?:\.git)?$/);
  if (m && !url.includes("://")) {
    return { owner: m[1], repo: m[2], ref: null, subpath: null, repoUrl: null };
  }
  if (url.startsWith("file://") || /^[a-z][a-z0-9+.-]*:\/\//.test(url) || url.startsWith("git@")) {
    const base = url.replace(/\.git$/, "");
    const seg = base.split("/").filter(Boolean).pop() || "repo";
    return { owner: "", repo: seg, ref: null, subpath: null, repoUrl: base };
  }
  return null;
}

function gitOk() {
  const r = spawnSync("git", ["--version"], { stdio: "ignore" });
  return r.status === 0;
}

function runGit(args, opts = {}) {
  const r = spawnSync("git", args, { ...opts, encoding: "utf8" });
  if (r.status !== 0) {
    throw new Error((r.stderr || r.stdout || "git command failed").trim());
  }
  return r.stdout;
}

function isSkillDir(p) {
  try {
    return statSync(p).isDirectory() && existsSync(join(p, "SKILL.md"));
  } catch {
    return false;
  }
}

// Candidate roots to look inside for skills.
function candidateRoots(repoRoot, pathOpt, subpath) {
  if (pathOpt) return [join(repoRoot, pathOpt)];
  if (subpath) return [join(repoRoot, subpath)];
  return SKILL_ROOTS.map((r) => (r ? join(repoRoot, r) : repoRoot));
}

// Find a skill folder named <skill> across candidate roots.
function resolveSkillPath(repoRoot, skill, pathOpt, subpath) {
  for (const root of candidateRoots(repoRoot, pathOpt, subpath)) {
    const p = join(root, skill);
    if (isSkillDir(p)) return p;
  }
  return null;
}

// Shallow clone (full tree, depth 1). Tries the requested ref as a branch
// first; falls back to the default branch, then checks out the ref.
function cloneRepo(repoUrl, ref, dest) {
  const tryClone = (extra) => {
    return spawnSync("git", [
      "clone", "--depth", "1", "--no-tags", "--single-branch", ...extra, repoUrl, dest,
    ], { stdio: "pipe", encoding: "utf8" });
  };
  let r = tryClone(["--branch", ref]);
  if (r.status !== 0) {
    r = tryClone([]);
  }
  if (r.status !== 0) {
    throw new Error((r.stderr || "git clone failed").trim());
  }
  if (ref && ref !== DEFAULT_REF) {
    const head = runGit(["-C", dest, "rev-parse", "--abbrev-ref", "HEAD"], { stdio: "pipe" }).trim();
    if (head !== ref) {
      const co = spawnSync("git", ["-C", dest, "checkout", ref], { stdio: "pipe", encoding: "utf8" });
      if (co.status !== 0) {
        throw new Error(`Could not find ref "${ref}". ${(co.stderr || "").trim()}`.trim());
      }
    }
  }
  return dest;
}

function makeTmp() {
  const dir = join(tmpdir(), `binnook-skills-${process.pid}-${Date.now()}`);
  mkdirSync(dir, { recursive: true });
  return dir;
}

// Collect skill names across candidate roots (deduped, sorted).
function listSkills(repoRoot, pathOpt) {
  const names = new Set();
  const roots = pathOpt
    ? [join(repoRoot, pathOpt)]
    : SKILL_ROOTS.map((r) => (r ? join(repoRoot, r) : repoRoot));
  for (const root of roots) {
    if (!existsSync(root)) continue;
    for (const name of readdirSync(root, { withFileTypes: true })) {
      if (!name.isDirectory() || name.name.startsWith(".")) continue;
      if (isSkillDir(join(root, name.name))) names.add(name.name);
    }
  }
  return [...names].sort();
}

function cmdAdd(args) {
  if (args.length < 1) fail("Missing <github-url> for add. See --help.");
  const url = args[0];
  const opts = parseOpts(args.slice(1), { skill: null, ref: DEFAULT_REF, path: null, dest: null, name: null, force: false });
  if (!opts.skill) fail("--skill <name> is required for add.");
  if (!gitOk()) fail("git is required but was not found on PATH.");

  const parsed = parseGithubUrl(url);
  if (!parsed) fail(`Could not parse GitHub URL: ${url}`);
  const ref = parsed.ref || opts.ref || DEFAULT_REF;
  const repoUrl = parsed.repoUrl || `https://github.com/${parsed.owner}/${parsed.repo}.git`;

  const destRoot = resolve(opts.dest || join(codexHome(), "skills"));
  const installName = opts.name || opts.skill;
  const dest = join(destRoot, installName);
  if (existsSync(dest)) {
    if (!opts.force) fail(`Destination already exists: ${dest} (use --force to overwrite)`);
    rmSync(dest, { recursive: true, force: true });
  }

  const tmp = makeTmp();
  try {
    const repoDir = join(tmp, "repo");
    cloneRepo(repoUrl, ref, repoDir);

    const skillSrc = resolveSkillPath(repoDir, opts.skill, opts.path, parsed.subpath);
    if (!skillSrc) {
      fail(`No skill folder "${opts.skill}" (with a SKILL.md) found in the repo. ` +
        `Use 'binnook-skills list <url>' to see available skills.`);
    }
    mkdirSync(destRoot, { recursive: true });
    cpSync(skillSrc, dest, { recursive: true });
    console.log(`Installed "${installName}" to ${dest}`);
    console.log(`It will be available on your next turn.`);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

function cmdList(args) {
  if (args.length < 1) fail("Missing <github-url> for list. See --help.");
  const url = args[0];
  const opts = parseOpts(args.slice(1), { ref: DEFAULT_REF, path: null, dest: null });
  if (!gitOk()) fail("git is required but was not found on PATH.");

  const parsed = parseGithubUrl(url);
  if (!parsed) fail(`Could not parse GitHub URL: ${url}`);
  const ref = parsed.ref || opts.ref || DEFAULT_REF;
  const repoUrl = parsed.repoUrl || `https://github.com/${parsed.owner}/${parsed.repo}.git`;

  const tmp = makeTmp();
  try {
    const repoDir = join(tmp, "repo");
    cloneRepo(repoUrl, ref, repoDir);
    const skills = listSkills(repoDir, opts.path);
    const destRoot = resolve(opts.dest || join(codexHome(), "skills"));
    const installed = new Set(
      existsSync(destRoot)
        ? readdirSync(destRoot, { withFileTypes: true })
            .filter((d) => d.isDirectory())
            .map((d) => d.name)
        : []
    );
    if (skills.length === 0) {
      console.log(`No skills found in ${parsed.owner}/${parsed.repo}.`);
      return;
    }
    const label = parsed.owner ? `${parsed.owner}/${parsed.repo}` : parsed.repo;
    console.log(`Skills from ${label}:`);
    skills.forEach((name, i) => {
      const suffix = installed.has(name) ? " (already installed)" : "";
      console.log(`${i + 1}. ${name}${suffix}`);
    });
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

function parseOpts(args, defaults) {
  const opts = { ...defaults };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case "--skill": opts.skill = args[++i]; break;
      case "--ref": opts.ref = args[++i]; break;
      case "--path": opts.path = args[++i]; break;
      case "--dest": opts.dest = args[++i]; break;
      case "--name": opts.name = args[++i]; break;
      case "--force": opts.force = true; break;
      default: fail(`Unknown option: ${a}`);
    }
  }
  return opts;
}

function main(argv) {
  if (argv.length === 0 || argv.includes("-h") || argv.includes("--help")) {
    help();
    return 0;
  }
  if (argv.includes("-v") || argv.includes("--version")) {
    console.log(`binnook-skills v${VERSION}`);
    return 0;
  }
  const cmd = argv[0];
  const rest = argv.slice(1);
  switch (cmd) {
    case "add": cmdAdd(rest); break;
    case "list": cmdList(rest); break;
    default: fail(`Unknown command "${cmd}". See --help.`);
  }
  return 0;
}

main(process.argv.slice(2));
