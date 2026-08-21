#!/usr/bin/env python3
"""Convert Claude Code JSONL transcript to readable export formats (Markdown, JSON, TXT)."""
import json
import sys
import os
from datetime import datetime


def extract_text_from_content(content):
    """Extract readable text from message content."""
    if isinstance(content, str):
        return content, []
    if isinstance(content, list):
        parts = []
        tools = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type", "")
            if block_type == "text":
                parts.append(block["text"])
            elif block_type == "tool_use":
                tool_name = block.get("name", "unknown")
                tool_input = block.get("input", {})
                tool_desc = _describe_tool(tool_name, tool_input)
                tools.append({"tool": tool_name, "detail": tool_desc})
                parts.append(f"[Tool: {tool_name}] {tool_desc}")
            elif block_type == "tool_result":
                result_content = block.get("content", "")
                if isinstance(result_content, list):
                    for rc in result_content:
                        if isinstance(rc, dict) and rc.get("type") == "text":
                            text = rc.get("text", "")
                            if len(text) > 200:
                                text = text[:200] + "...(truncated)"
                            parts.append(f"[Result] {text}")
                elif isinstance(result_content, str) and result_content:
                    if len(result_content) > 200:
                        result_content = result_content[:200] + "...(truncated)"
                    parts.append(f"[Result] {result_content}")
        return "\n".join(parts), tools
    return str(content), []


def _describe_tool(tool_name, tool_input):
    """Generate a short description for a tool call."""
    desc_map = {
        "Bash": lambda i: i.get("command", ""),
        "Read": lambda i: i.get("file_path", ""),
        "Write": lambda i: i.get("file_path", ""),
        "Edit": lambda i: i.get("file_path", ""),
        "Grep": lambda i: f"pattern='{i.get('pattern', '')}'" + (f" path={i.get('path')}" if i.get("path") else ""),
        "Glob": lambda i: i.get("pattern", ""),
        "Agent": lambda i: i.get("description", ""),
        "AskUserQuestion": lambda i: "; ".join(q.get("question", "") for q in i.get("questions", [])),
        "WebSearch": lambda i: i.get("query", ""),
        "WebFetch": lambda i: i.get("url", ""),
    }
    fn = desc_map.get(tool_name)
    return fn(tool_input) if fn else json.dumps(tool_input, ensure_ascii=False)[:120]


def format_timestamp(ts_str):
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts_str or ""


def parse_jsonl(input_file):
    """Parse JSONL file and return structured messages."""
    messages = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type")
            if msg_type not in ("user", "assistant"):
                continue

            timestamp = obj.get("timestamp", "")
            message = obj.get("message", {})
            role = message.get("role", msg_type)
            content = message.get("content", "")
            model = message.get("model", "")

            text, tools = extract_text_from_content(content)
            text = text.strip()
            if not text:
                continue

            msg = {
                "role": role,
                "timestamp": timestamp,
                "timestamp_formatted": format_timestamp(timestamp),
                "text": text,
                "tools": tools,
            }
            if model:
                msg["model"] = model
            messages.append(msg)
    return messages


def to_markdown(messages, source_file, show_time=True):
    """Convert messages to Markdown format."""
    lines = [
        "# Claude Code Conversation Export\n",
        f"- **Source**: `{source_file}`",
        f"- **Messages**: {len(messages)}",
        f"- **Exported at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "---\n",
    ]
    for msg in messages:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        if show_time:
            lines.append(f"### {role_label} [{msg['timestamp_formatted']}]\n")
        else:
            lines.append(f"### {role_label}\n")
        lines.append(msg["text"])
        lines.append("\n---\n")
    return "\n".join(lines)


def to_txt(messages, source_file, show_time=True):
    """Convert messages to plain TXT format."""
    lines = [
        f"Claude Code Conversation Export",
        f"Source: {source_file}",
        f"Messages: {len(messages)}",
        f"Exported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
    ]
    for msg in messages:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        if show_time:
            lines.append(f"[{msg['timestamp_formatted']}] {role_label}:")
        else:
            lines.append(f"{role_label}:")
        lines.append(msg["text"])
        lines.append("-" * 60)
        lines.append("")
    return "\n".join(lines)


def to_json(messages, source_file, show_time=True):
    """Convert messages to structured JSON format."""
    if not show_time:
        messages = [
            {k: v for k, v in m.items() if k not in ("timestamp", "timestamp_formatted")}
            for m in messages
        ]
    export = {
        "source": source_file,
        "message_count": len(messages),
        "exported_at": datetime.now().isoformat(),
        "messages": messages,
    }
    return json.dumps(export, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 session_export.py <input.jsonl> [output_dir] [--formats md,json,txt] [--no-time] [--name <name>]")
        print("")
        print("Arguments:")
        print("  input.jsonl    Path to Claude Code JSONL transcript file")
        print("  output_dir     Output directory (default: same dir as input)")
        print("  --formats      Comma-separated formats: md, json, txt (default: md,json,txt)")
        print("  --no-time      Hide timestamps from output")
        print("  --name         Custom output file name (without extension)")
        print("                 Tip: use format like '2026-03-10_myproject_feature-x'")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: file not found: {input_file}")
        sys.exit(1)

    # Parse options
    output_dir = os.path.dirname(input_file) or "."
    formats = {"md", "json", "txt"}
    show_time = True
    custom_name = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--formats" and i + 1 < len(sys.argv):
            formats = set(sys.argv[i + 1].split(","))
            i += 2
        elif arg == "--no-time":
            show_time = False
            i += 1
        elif arg == "--name" and i + 1 < len(sys.argv):
            custom_name = sys.argv[i + 1]
            i += 2
        elif not arg.startswith("--"):
            output_dir = arg
            i += 1
        else:
            i += 1

    os.makedirs(output_dir, exist_ok=True)

    # Parse messages
    messages = parse_jsonl(input_file)
    if not messages:
        print("No user/assistant messages found in the file.")
        sys.exit(1)

    base_name = custom_name if custom_name else os.path.splitext(os.path.basename(input_file))[0]
    outputs = []

    if "md" in formats:
        path = os.path.join(output_dir, f"{base_name}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_markdown(messages, input_file, show_time))
        outputs.append(path)

    if "json" in formats:
        path = os.path.join(output_dir, f"{base_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_json(messages, input_file, show_time))
        outputs.append(path)

    if "txt" in formats:
        path = os.path.join(output_dir, f"{base_name}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_txt(messages, input_file, show_time))
        outputs.append(path)

    print(f"Exported {len(messages)} messages:")
    for p in outputs:
        print(f"  -> {p}")


if __name__ == "__main__":
    main()
