# BinNook Skills

[English](README.md) | [简体中文](README.zh-CN.md)

一个精选的 [Codex](https://github.com/openai/codex) skills 集合，支持按需安装。每个 skill 是一个独立、基于 Markdown 的模块，为 Codex 扩展专用工作流、工具集成或领域知识——在需要之前不会占用你的上下文窗口。

用一条命令即可从任意 GitHub 仓库安装单个 skill：

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me
```

## 特性

- **按名称安装** —— 从 GitHub 仓库拉取单个 skill 文件夹，而非整个集合。
- **零依赖 CLI** —— 纯 Node.js（ESM）加 `git`，无需提前安装任何依赖。
- **灵活查找** —— 在仓库根目录或常见 skill 子目录下查找 skill。
- **MIT 许可** —— 见 [`LICENSE`](LICENSE)。

## 环境要求

- **Node.js** ≥ 18
- `PATH` 中有 **git**

> 包发布到 npm 后，`npx binnook-skills ...` 可按需运行 CLI，无需全局安装。在此之前，克隆本仓库并直接运行 `node bin/binnook-skills.js ...`。

## 安装 skill

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill <skill-name>
```

这会下载 skill 并复制到 `$CODEX_HOME/skills/<skill-name>`（默认 `~/.codex/skills`），在下一轮对话即可生效。

从指定分支、标签或提交安装：

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --ref dev
```

覆盖已有安装，或以不同名称安装：

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --force
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --name grill-me-local
```

安装到自定义目录：

```bash
npx binnook-skills add https://github.com/BinNook/skills --skill grill-me --dest ~/my-skills
```

## 列出可用 skill

```bash
npx binnook-skills list https://github.com/BinNook/skills
```

本地已安装的 skill 会标注 `(already installed)`。

## 命令参考

### `add`

```bash
npx binnook-skills add <github-url> --skill <name> [options]
```

| 选项 | 说明 |
| --- | --- |
| `--skill <name>` | 要安装的 skill 文件夹（**必填**）。 |
| `--ref <ref>` | Git 分支/标签/提交（默认 `main`）。 |
| `--path <relpath>` | 存放 skill 的子目录（覆盖自动检测）。 |
| `--dest <path>` | 目标 skills 目录（默认 `$CODEX_HOME/skills`）。 |
| `--name <name>` | 以不同文件夹名安装。 |
| `--force` | 目标已存在时强制覆盖。 |

### `list`

```bash
npx binnook-skills list <github-url> [options]
```

支持同样的 `--ref`、`--path`、`--dest` 选项。

### 支持的仓库 URL

- `https://github.com/<owner>/<repo>`
- `https://github.com/<owner>/<repo>/tree/<ref>/<path>`
- `git@github.com:<owner>/<repo>.git`
- `<owner>/<repo>`（简写）

## skill 查找位置

CLI 会按以下顺序查找包含 `SKILL.md` 的 skill 文件夹：

1. 仓库根目录
2. `skills/`
3. `skills/.curated`
4. `skills/.experimental`

用 `--path <relpath>` 可改为在自定义子目录中查找。

## skill 结构

每个 skill 是一个文件夹，必须包含 `SKILL.md`：

```
<skill-name>/
├── SKILL.md            # 必填：YAML frontmatter（name, description）+ Markdown 正文
├── agents/openai.yaml  # 可选：UI 元数据（display_name, short_description）
├── scripts/            # 可选：可执行辅助脚本
├── references/         # 可选：按需加载到上下文的文档
└── assets/             # 可选：用于输出的模板、图标、字体
```

示例 —— `grill-me/SKILL.md`：

```markdown
---
name: grill-me
description: Grills the user with quick-fire questions. Use when the user wants rapid-fire question practice.
---

# Grill Me

Ask one question at a time, wait for the answer, then follow up immediately.
```

请将 `SKILL.md` 控制在 500 行以内；详细内容移入 `references/` 并在正文中链接。

## 创建你的 skill

1. 创建一个 lowercase kebab-case 命名的文件夹，如 `my-skill/`。
2. 添加 `SKILL.md`，包含 frontmatter `name` 和 `description`（`description` 决定 Codex 何时触发该 skill，请写具体）。
3. 可选添加 `agents/openai.yaml`、`scripts/`、`references/` 或 `assets/`。
4. 提交到你的仓库，用 `npx binnook-skills add <your-repo-url> --skill my-skill` 安装。

## 贡献

结构约定、代码风格、测试和提交/PR 规范见 [`AGENTS.md`](AGENTS.md)。使用 [Conventional Commits](https://www.conventionalcommits.org/)（如 `feat(skill): add my-skill`）。

## 许可

[MIT](LICENSE) © BinNook
