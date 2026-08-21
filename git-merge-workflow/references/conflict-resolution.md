# Conflict Resolution Reference

冲突解决的详细参考文档，由 SKILL.md Phase 2 引用。

## 冲突策略执行方法

### 保留目标分支 (ours)

```bash
git checkout --ours <file>
git add <file>
```

### 保留源分支 (theirs)

```bash
git checkout --theirs <file>
git add <file>
```

### 两边保留

手动编辑文件，移除冲突标记（`<<<<<<<`, `=======`, `>>>>>>>`），保留双方所有内容。注意内容的排列顺序可能需要调整以保证逻辑正确。

### 逐块选择 (per-hunk)

1. 读取文件内容，解析所有冲突块（以 `<<<<<<<` 和 `>>>>>>>` 为边界）
2. 逐块展示双方内容，使用 AskUserQuestion 让用户选择：
   - 保留目标分支的内容
   - 保留源分支的内容
   - 两边都保留
3. 按用户选择重组文件内容
4. 写回文件并暂存

### 手动编辑

1. 告知用户文件路径和冲突块位置
2. 等待用户确认编辑完成
3. 验证文件中不再包含冲突标记（`<<<<<<<`, `=======`, `>>>>>>>`）
4. 暂存

## 格式校验方法

解决冲突后，按文件扩展名自动校验格式，防止合并引入语法错误：

| 文件类型 | 校验命令 | 说明 |
|---|---|---|
| `.toml` | `python3 -c "import tomllib; tomllib.load(open('<file>','rb'))"` | Python 3.11+，低版本用 `pip install tomli` |
| `.yaml` / `.yml` | `python3 -c "import yaml; yaml.safe_load(open('<file>'))"` | 需要 PyYAML |
| `.json` | `python3 -c "import json; json.load(open('<file>'))"` | 标准库 |
| `.xml` | `python3 -c "import xml.etree.ElementTree as ET; ET.parse('<file>')"` | 标准库 |
| `.conf` (nginx) | `nginx -t -c <file>` | 需要 nginx 可用 |
| `.sql` | 检查括号匹配、分号结尾、无残留冲突标记 | 正则检查 |
| `.go` | `gofmt -e <file>` | Go 格式检查 |
| `.py` | `python3 -m py_compile <file>` | Python 语法检查 |
| 其他 | 仅检查无残留冲突标记 | `grep -c '<<<<<<<' <file>` |

校验优先级：
1. 检查是否残留冲突标记（所有文件必检）
2. 按文件类型做格式/语法校验（工具可用时）
3. 校验工具不可用时跳过，仅做残留标记检查

## 冲突解决记录模板

```markdown
### 冲突解决记录

| 序号 | 文件 | 冲突块数 | 策略 | 备注 |
|---|---|---|---|---|
| 1 | configs/app.toml | 3 | 逐块选择 | 块1:保留目标, 块2:两边保留, 块3:保留源 |
| 2 | src/handler.go | 1 | 保留目标分支 | 源分支改动已在目标分支中实现 |
| 3 | sql/schema.sql | 2 | 手动编辑 | DDL 需融入 CREATE TABLE 定义 |
```