---
name: markdown2pdf
description: 将包含 Mermaid 图表的 Markdown 文件转换为 PDF。使用时用户需要转换 Markdown 文件到 PDF，Markdown 文件中包含 Mermaid 图表需要渲染，需要将 Markdown 文档导出为格式化的 PDF 文档。支持 Python 实现，通过 Dash 渲染 Markdown 和 Playwright 导出 PDF，自动处理依赖安装检查。
---

# Markdown 转 PDF

这个技能将包含 Mermaid 图表的 Markdown 文件转换为格式完善的 PDF 文档。

## 使用场景

- 将 Markdown 文档导出为 PDF
- Markdown 文档包含 Mermaid 图表需要正确渲染
- 需要保留 Mermaid 图表的样式和颜色
- 需要批量处理多个 Markdown 文件

## 核心工作流

1. 检查依赖是否已安装
2. 使用 `scripts/markdown2pdf.py` 脚本执行转换
3. 指定源 Markdown 文件和输出 PDF 路径

## 基本使用

```bash
python scripts/markdown2pdf.py -s input.md -o output.pdf
```

## 参数说明

- `-s/--source`: 源 Markdown 文件路径（必填）
- `-o/--output`: 输出 PDF 文件路径（必填）
- `-p/--port`: Dash 服务器端口（可选，默认 8050）

## 注意事项

- 首次使用需要安装依赖，脚本会自动检查并安装
- 若 PDF 中文乱码，确保系统已安装中文字体
- 若端口被占用，使用 `-p` 指定其他端口（如 8080）
- 确保 Markdown 中的 Mermaid 代码无语法错误

## 参考信息

详细信息和使用示例参见 `scripts/markdown2pdf.py` 源码。
