# BinNook Skills

[English](README.md) | [简体中文](README.zh-CN.md)

A curated collection of [Codex](https://github.com/openai/codex) skills, installable on demand. Each skill is a self-contained, Markdown-based module that extends Codex with specialized workflows, tool integrations, or domain knowledge — without bloating your context window until it is needed.

Install a single skill from any GitHub repository with one command:

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me
```

## Features

- **Install by name** — fetch one skill folder from a GitHub repo, not the whole collection.
- **Zero-dependency CLI** — plain Node.js (ESM) plus `git`; nothing to install up front.
- **Flexible lookup** — finds skills at the repo root or under common skill directories.
- **MIT licensed** — see [`LICENSE`](LICENSE).

## Requirements

- **Node.js** ≥ 18
- **git** on your `PATH`

> Once published to npm, `npx binnook-skills ...` runs the CLI on demand with no global install. Until then, clone this repo and run `node bin/binnook-skills.js ...` directly.

## Install a skill

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill <skill-name>
```

This downloads the skill and copies it into `$CODEX_HOME/skills/<skill-name>` (default `~/.codex/skills`). The skill becomes available on your next turn.

Install from a specific branch, tag, or commit:

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --ref dev
```

Overwrite an existing install, or install under a different name:

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --force
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --name grill-me-local
```

Install into a custom directory:

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --dest ~/my-skills
```

## List available skills

```bash
npx binnook-skills list https://github.com/BinNook/skills
```

Skills already installed locally are marked `(already installed)`.

## Command reference

### `add`

```bash
npx binnook-skills add <github-url> --skill <name> [options]
```

| Option | Description |
| --- | --- |
| `--skill <name>` | Skill folder to install (**required**). |
| `--ref <ref>` | Git branch, tag, or commit (default: `main`). |
| `--path <relpath>` | Subdirectory holding skills (overrides auto-detect). |
| `--dest <path>` | Destination skills directory (default: `$CODEX_HOME/skills`). |
| `--name <name>` | Install under a different folder name. |
| `--force` | Overwrite if the destination already exists. |

### `list`

```bash
npx binnook-skills list <github-url> [options]
```

Supports the same `--ref`, `--path`, and `--dest` options.

### Accepted repository URLs

- `https://github.com/<owner>/<repo>`
- `https://github.com/<owner>/<repo>/tree/<ref>/<path>`
- `git@github.com:<owner>/<repo>.git`
- `<owner>/<repo>` (shorthand)

## Where skills are found

The CLI looks for a skill folder (containing a `SKILL.md`) in, in order:

1. The repository root
2. `skills/`
3. `skills/.curated`
4. `skills/.experimental`

Pass `--path <relpath>` to search a custom subdirectory instead.

## Skill structure

Each skill is one folder with a required `SKILL.md`:

```
<skill-name>/
├── SKILL.md            # required: YAML frontmatter (name, description) + Markdown body
├── agents/openai.yaml  # optional: UI metadata (display_name, short_description)
├── scripts/            # optional: executable helpers
├── references/         # optional: docs loaded into context on demand
└── assets/             # optional: templates, icons, fonts used in output
```

Example — `grill-me/SKILL.md`:

```markdown
---
name: grill-me
description: Grills the user with quick-fire questions. Use when the user wants rapid-fire question practice.
---

# Grill Me

Ask one question at a time, wait for the answer, then follow up immediately.
```

Keep `SKILL.md` under 500 lines; move detail into `references/` and link to it from the body.

## Creating your own skill

1. Create a folder named in lowercase kebab-case, e.g. `my-skill/`.
2. Add a `SKILL.md` with frontmatter `name` and `description` (the `description` decides when Codex triggers the skill, so make it specific).
3. Optionally add `agents/openai.yaml`, `scripts/`, `references/`, or `assets/`.
4. Commit it to your repo and install it with `npx binnook-skills add <your-repo-url> --skill my-skill`.

## Contributing

See [`AGENTS.md`](AGENTS.md) for structure conventions, coding style, testing, and commit/PR guidelines. Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat(skill): add my-skill`).

## License

[MIT](LICENSE) © BinNook
