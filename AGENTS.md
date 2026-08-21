# Repository Guidelines

Welcome to **BinNook/skills** — a curated collection of Codex skills, installable via `npx binnook-skills`. Each skill is a self-contained, Markdown-based module that extends Codex with specialized workflows, tool integrations, or domain knowledge. The project is MIT-licensed; see `LICENSE`.

## Project Structure & Module Organization

Each skill is one top-level folder containing a `SKILL.md`:

```
<skill-name>/
├── SKILL.md            # required: YAML frontmatter (name, description) + Markdown body
├── agents/openai.yaml  # optional: UI metadata (display_name, short_description)
├── scripts/            # optional: executable Python/Bash helpers
├── references/         # optional: docs loaded into context on demand
└── assets/             # optional: templates, icons, fonts used in output
```

The CLI lives in `bin/binnook-skills.js` (Node ESM, zero dependencies). Do **not** add `README.md`, `CHANGELOG.md`, or auxiliary docs inside a skill.

## Build, Test, and Development Commands

There is no build step. Validate changes locally (requires `node` ≥18 and `git`):

- `node bin/binnook-skills.js --help` — show CLI usage.
- `node --check bin/binnook-skills.js` — syntax check the CLI.
- `node bin/binnook-skills.js list file://$PWD` — list skills from a local clone.
- `node bin/binnook-skills.js add file://$PWD --skill grill-me --dest /tmp/dest` — install a skill to a temp dir to verify the flow.

Smoke tests need a committed repo: `git commit` before testing so `--depth 1` clones have a ref.

## Installing Skills

```
npx binnook-skills add https://github.com/BinNook/skills --skill <name>
npx binnook-skills list https://github.com/BinNook/skills
```

Installed to `$CODEX_HOME/skills/<name>` (default `~/.codex/skills`). Options: `--ref`, `--path`, `--name`, `--dest`, `--force`.

## Coding Style & Naming Conventions

- Skill folders: lowercase kebab-case (e.g. `grill-me`).
- `SKILL.md` body: keep under 500 lines; move detail to `references/` and link it from the body.
- Frontmatter `description` must state *what* the skill does and *when* to use it.
- CLI: zero-dependency Node, 2-space indent, double quotes, no semicolons required.

## Testing Guidelines

No automated test suite. Before opening a PR:

- Confirm frontmatter parses as valid YAML and `SKILL.md` renders.
- Run the CLI smoke commands above against a local commit.
- Optionally install the skill into a temp `--dest` and confirm it generalizes.

## Commit & Pull Request Guidelines

Use **Conventional Commits**:

- `feat(skill): add grill-me skill`
- `fix(cli): correct ref checkout fallback`
- `docs: clarify install options`

PRs should add or update one skill (or a focused set), include a short description of the skill's purpose, link related issues, and avoid unrelated changes.
