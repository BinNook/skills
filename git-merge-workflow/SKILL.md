---
name: git-merge-workflow
description: "Git 分支合入规范流程：分支对比分析、团队讨论规划、merge --no-commit 合入、逐文件用户驱动冲突解决、逐提交追溯验证、commit message 审核后提交。当用户提到合并分支、合入代码、merge 分支、将某分支合到另一个分支、分支集成、代码集成、hotfix 合入主线、release 合回 dev 等场景时，都应使用此技能。即使用户只是简单说'把 A 合到 B'，也应触发此技能。"
---

# Git Merge Workflow

将一个分支的修改合入到另一个分支的规范流程。全程用户驱动决策，产出单次 merge commit 并保留完整 git 双 parent 血缘关系。

## Usage

```
/git-merge-workflow <source_branch> [target_branch]
```

- `source_branch`（必填）：源分支
- `target_branch`（可选）：目标分支，默认为当前分支

**Example 1:**
```
/git-merge-workflow hotfix/2.1.1
```
将 hotfix/2.1.1 合入当前分支。

**Example 2:**
```
/git-merge-workflow feature/auth dev
```
将 feature/auth 合入 dev 分支。

## Workflow Overview

共 6 个 Phase（0-5），每个 Phase 完成后向用户确认再进入下一步。遇到需要决策的地方，整理选项后交给用户选择，而非自行假设。

---

## Phase 0: 分析与规划

合入前充分了解两个分支的差异，是避免后续返工的关键。

### 0.1 分支对比分析

收集以下信息并以表格呈现：

```bash
# 源分支独有提交
git log --oneline <source> --not <target> --no-merges

# 变更文件统计
git diff --stat <source>...<target>

# 冲突预检（dry-run）
git merge --no-commit --no-ff <source> 2>&1; git merge --abort
```

输出：
- 源分支独有提交数量及列表
- 变更文件按目录分组汇总
- 预计冲突文件列表（如有）

### 0.2 团队讨论

以三个视角分析合入方案，识别风险和需要用户确认的问题：

| 角色 | 关注点 |
|---|---|
| **架构师** | 影响范围、兼容性、目录结构策略 |
| **开发者** | 具体文件变更、冲突方案、数据一致性 |
| **质疑者** | 挑战假设、识别遗漏、边界场景 |

讨论后将不确定的问题整理为编号列表，一次性向用户确认。

### 0.3 方案文档化

将实施方案写入 `doc/merge-<source_safe_name>-to-<target>.md`：
- 分支对比摘要
- 冲突文件列表及预期解决策略
- 用户确认的问答记录
- 各 Phase 执行计划

后续所有操作以此文档为准，变更时同步更新文档。

---

## Phase 1: 合入执行

```bash
git checkout <target_branch>
git merge --no-commit <source_branch>
```

使用 `--no-commit` 而非直接 merge 的原因：
- 暂停在提交前，允许在暂存区中做任何修改（冲突解决、内容调整）
- 隐含 `--no-ff` 行为，最终产生有两个 parent 的 merge commit
- 保留源分支完整 git 血缘，`git log --graph` 可追溯到源分支的所有提交

如果存在冲突 → Phase 2。无冲突 → Phase 3。

---

## Phase 2: 冲突解决

冲突解决是用户驱动的，因为只有用户了解业务上下文和每处冲突的正确取舍。工具的职责是清晰呈现差异、提供策略选项、执行用户的决定。

### 2.1 冲突分组

列出冲突文件，按目录自动分组：

```
发现 5 个冲突文件：
  configs/ (3个): app.toml, web.conf, nginx.conf
  sql/     (2个): schema.sql, data.sql
```

### 2.2 组级默认策略

使用 AskUserQuestion 为每个组询问默认策略：

- **逐文件决定**（推荐）— 每个文件单独选择
- **保留目标分支 (ours)** — 该组所有文件丢弃源分支修改
- **保留源分支 (theirs)** — 该组所有文件用源分支覆盖
- **两边保留** — 该组所有文件合并双方内容

选择"逐文件决定"后进入 2.3 逐文件处理。选择其他策略的文件批量处理后跳过 2.3。

### 2.3 逐文件处理

对每个冲突文件，按 4 步处理：

**Step 1 — 冲突预览**

展示冲突块数量，以及每个冲突块的双方差异（标注 `<<<< TARGET` / `>>>> SOURCE`），让用户在选择策略前看清双方改了什么。

**Step 2 — 策略选择**

使用 AskUserQuestion 提供选项：

| 策略 | 说明 |
|---|---|
| 保留目标分支 (ours) | 丢弃源分支在该文件的修改 |
| 保留源分支 (theirs) | 用源分支版本覆盖 |
| 两边保留 | 合并双方内容 |
| 逐块选择 (per-hunk) | 对每个冲突块分别展示并选择 |
| 手动编辑 | 用户自行编辑后标记完成 |

"逐块选择"时，逐个展示冲突块的双方内容，每块单独让用户选择保留哪边或两边都保留。

**Step 3 — 格式校验**

解决冲突后按文件类型自动校验，防止合并引入语法错误。详细校验方法参见 `references/conflict-resolution.md`。校验失败时提示用户重新处理。

**Step 4 — 暂存并记录**

```bash
git add <resolved_file>
```

将该文件的冲突块数、选择的策略、备注记录到方案文档的"冲突解决记录"表格中。

---

## Phase 3: 暂存区修改

merge 自动合并后，可能还需要额外的适配修改（不属于冲突，但属于合入必要工作）。常见场景：

- **目录结构调整** — 如删除不需要的目录，统一目录规范
- **数据融合** — 如将增量 DDL/DML 融入全量 SQL 文件
- **ID 冲突检测** — 如检查自增 ID 是否冲突，优先复用原 ID
- **关联数据一致性** — 如检查外键引用、权限绑定链路完整性

每项修改前向用户说明原因和方案，确认后执行。修改完成后暂存：

```bash
git add <modified_files>
```

同步更新方案文档。

---

## Phase 4: 逐提交追溯验证

验证的目的是确保源分支的每个修改都在目标分支中有体现，不遗漏。

### 4.1 列出源分支独有提交

```bash
git log --oneline <source> --not <target> --no-merges
```

### 4.2 逐提交核对

对提交数量较多的情况，使用 Agent 并行验证以提高效率。每个提交检查：
- 涉及的文件和具体变更内容
- 目标分支对应位置是否已包含等效变更
- 标记状态：`VERIFIED` / `SUPERSEDED`（被更高版本覆盖）/ `MISSING`

### 4.3 生成验证报告

```markdown
| 提交 | 描述 | 涉及文件 | 状态 | 备注 |
|---|---|---|---|---|
| abc1234 | fix: 修复索引 | job.sql | VERIFIED | 已融入 CREATE TABLE |
| def5678 | feat: 新增配置 | app.toml | VERIFIED | 配置已合入 |
| ghi9012 | fix: 版本号 | uim.sql | SUPERSEDED | 目标分支版本更高 |
```

如有 `MISSING` 状态的提交，向用户报告并讨论处理方式。

---

## Phase 5: 提交

### 5.1 生成 Commit Message

根据暂存区变更内容，按目标仓库的 commit 风格生成结构化 message：

```
Merge branch '<source_branch>' into <target_branch>

<一句话概述合入目的>

<按目录/类型分类的变更摘要>
```

先展示给用户审核。用户可能会要求调整措辞、补充内容或修改格式。确认后再执行提交。

### 5.2 执行提交并验证

```bash
git commit -m "<approved_message>"
git log --oneline --graph -5
```

确认输出中 merge commit 呈现 `|\` 分叉图形（表示有两个 parent），血缘关系完整。

---

## Error Handling

| 场景 | 处理方式 |
|---|---|
| 目标分支有未提交的修改 | 提示用户先 stash 或 commit，不在脏工作区上 merge |
| merge 后发现遗漏 | 由于尚未 commit，直接修改暂存区并重新 `git add` |
| 格式校验失败 | 提示用户重新选择策略或手动编辑该文件 |
| 验证阶段发现 MISSING | 报告给用户，讨论是补充还是标记为"不需要" |
| 用户想中途取消 | `git merge --abort` 恢复到 merge 前状态 |

## Principles

这些原则贯穿整个流程：

1. **用户驱动** — 每个关键决策都由用户确认，工具不做假设
2. **血缘完整** — 使用 `merge --no-commit` 而非 cherry-pick/rebase，保留双 parent
3. **逐文件粒度** — 冲突解决按文件甚至按冲突块粒度，不做全局一刀切
4. **可追溯** — 所有决策记录到方案文档，验证报告可复盘
5. **不到最后不提交** — 全程在暂停状态修改，给足调整空间
6. **先审后提** — commit message 先给用户检查，确认后再执行
