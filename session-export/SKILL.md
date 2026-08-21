---
name: session-export
description: "将 Claude Code 的 JSONL 会话记录转换为可读的导出格式（Markdown、JSON、TXT）。当用户想要导出之前的会话记录、提取历史对话、将 JSONL 转成可读文本、查看压缩前的完整对话、恢复被 context compaction 截断的聊天记录时，使用此技能。即使用户只是说'导出上次的聊天记录'或'我想看之前的对话'，也应触发。"
---

# Session Export

将 Claude Code 的 JSONL 会话 transcript 文件转换为可读的导出格式。

Claude Code 的 `/export` 命令只能导出当前会话的内容。当会话经过 context compaction（上下文压缩）后，原始对话会被压缩为摘要，`/export` 无法恢复完整记录。但 JSONL transcript 文件保存了完整的原始交互，本技能将其转换为人类可读的格式。

## Usage

```
/session-export <jsonl_path> [output_dir] [--formats md,json,txt] [--no-time] [--name <name>]
```

- `jsonl_path`（必填）：JSONL transcript 文件路径
- `output_dir`（可选）：输出目录，默认与输入文件同目录
- `--formats`（可选）：输出格式，逗号分隔，默认全部（md,json,txt）
- `--no-time`（可选）：隐藏时间戳，导出文件中不显示操作时间
- `--name`（可选）：自定义输出文件名（不含扩展名），推荐格式 `日期_项目名_需求名`

**Example 1** — 导出上一次被压缩的会话：
```
/session-export ~/.claude/projects/myproject/abc123.jsonl ./doc/
```

**Example 2** — 只导出 Markdown，不显示时间：
```
/session-export ~/.claude/projects/myproject/abc123.jsonl --formats md --no-time
```

**Example 3** — 自定义文件名：
```
/session-export ~/.claude/projects/myproject/abc123.jsonl ./doc/ --name 2026-03-10_udcp_merge-maintain-to-dev
```

## How It Works

### Step 1: 定位 JSONL 文件

用户提供 JSONL 文件路径后，验证文件存在。

JSONL transcript 文件通常位于：
```
~/.claude/projects/<project-path-encoded>/<session-uuid>.jsonl
```

如果用户不确定路径，帮助他们查找：
```bash
ls -lt ~/.claude/projects/*/  # 列出所有项目的 transcript
```

### Step 2: 执行转换

运行 bundled 脚本进行转换：

```bash
python3 <skill-path>/scripts/session_export.py <jsonl_path> [output_dir] [--formats md,json,txt] [--no-time] [--name <name>]
```

`<skill-path>` 是本技能目录的绝对路径（即 SKILL.md 所在目录）。

### Step 3: 呈现结果

转换完成后向用户报告：
- 提取了多少条消息
- 各格式文件的输出路径
- 文件大小

## Output Formats

### Markdown (.md)

带格式的对话记录，包含：
- 文件元信息（来源、消息数、导出时间）
- 按时间排列的 User/Assistant 消息
- 工具调用以 `[Tool: xxx]` 标注
- 工具结果以 `[Result]` 标注（超过 200 字符自动截断）

### JSON (.json)

结构化数据，适合程序化处理：

```json
{
  "source": "path/to/file.jsonl",
  "message_count": 345,
  "exported_at": "2026-03-10T22:30:00",
  "messages": [
    {
      "role": "user",
      "timestamp": "2026-03-10T06:16:23.910Z",
      "timestamp_formatted": "2026-03-10 06:16:23",
      "text": "你好",
      "tools": []
    },
    {
      "role": "assistant",
      "timestamp": "2026-03-10T06:16:40.217Z",
      "timestamp_formatted": "2026-03-10 06:16:40",
      "text": "你好！有什么可以帮你的吗？",
      "tools": [],
      "model": "claude-opus-4-6"
    }
  ]
}
```

### TXT (.txt)

纯文本格式，无 Markdown 标记，适合在任何编辑器中查看：

```
[2026-03-10 06:16:23] User:
你好
------------------------------------------------------------
[2026-03-10 06:16:40] Assistant:
你好！有什么可以帮你的吗？
------------------------------------------------------------
```
