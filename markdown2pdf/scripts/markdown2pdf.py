# markdown2pdf.py
import os
import sys
import argparse
import subprocess
import dash
import feffery_markdown_components as fmc
from dash import html
import threading
import time
from playwright.sync_api import sync_playwright

# 全局变量：存储 Dash 应用实例和服务器状态
dash_app = None
server_thread = None
server_running = False

def check_and_install_dependencies():
    """检查并安装必要的 Python 依赖"""
    required_packages = {
        'feffery-markdown-components': 'feffery_markdown_components',
        'dash': 'dash',
        'playwright': 'playwright',
        'requests': 'requests'
    }

    needs_install = False

    # 检查每个包是否已安装
    for pkg, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {pkg} 已安装")
        except ImportError:
            print(f"✗ {pkg} 未安装")
            needs_install = True

    if needs_install:
        print("\n正在安装缺失的依赖...")
        packages_str = ' '.join(required_packages.keys())
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', packages_str, '-U'])
        print("依赖安装完成")

    # 检查 Playwright 浏览器
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 尝试启动 Chromium 验证是否已安装
            browser = p.chromium.launch()
            browser.close()
        print("✓ Playwright Chromium 浏览器已安装")
    except Exception as e:
        print(f"✗ Playwright Chromium 浏览器未安装: {e}")
        print("正在安装 Playwright Chromium 浏览器...")
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        print("Playwright Chromium 浏览器安装完成")

def start_dash_server(markdown_path, port=8050):
    """启动 Dash 服务器，渲染 Markdown 内容"""
    global dash_app, server_running

    # 读取 Markdown 文件内容
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"源 Markdown 文件不存在：{markdown_path}")

    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # 初始化 Dash 应用
    dash_app = dash.Dash(
        __name__,
        external_scripts=[
            "https://registry.npmmirror.com/mermaid/latest/files/dist/mermaid.min.js"
        ],
        suppress_callback_exceptions=True
    )

    # 布局：渲染 Markdown，启用 Mermaid 支持
    dash_app.layout = html.Div(
        [
            fmc.FefferyMarkdown(
                markdownStr=markdown_content,
                mermaidOptions=True,  # 关键：启用 Mermaid 渲染
                style={'width': '100%', 'padding': '20px'}
            )
        ],
        style={'width': '100%', 'margin': '0 auto', 'max-width': '1200px'}
    )

    # 启动服务器（非阻塞模式）
    def run_server():
        global server_running
        dash_app.run_server(
            port=port,
            debug=False,  # 关闭 debug 避免重复启动
            use_reloader=False,  # 禁用自动重载
            host='127.0.0.1'
        )
        server_running = False

    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    server_running = True

    # 等待服务器启动（最多等5秒）
    timeout = 5
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            import requests
            requests.get(f"http://127.0.0.1:{port}")
            break
        except:
            time.sleep(0.5)
    else:
        raise TimeoutError("Dash 服务器启动超时")

def export_pdf(port, output_pdf_path):
    """使用 Playwright 导出网页为 PDF"""
    # 确保输出目录存在
    output_dir = os.path.dirname(output_pdf_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with sync_playwright() as p:
        # 启动浏览器（无头模式，不显示窗口）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 打开 Dash 页面
        page.goto(f"http://127.0.0.1:{port}", wait_until="networkidle")

        # 等待 Mermaid 图表渲染完成（最多等10秒）
        page.wait_for_function(
            """
            () => {
                const mermaidElements = document.querySelectorAll('.mermaid');
                if (mermaidElements.length === 0) return true;
                return Array.from(mermaidElements).every(el => el.querySelector('svg') !== null);
            }
            """,
            timeout=10000
        )

        # 导出 PDF（保留背景、设置纸张大小）
        page.pdf(
            path=output_pdf_path,
            format='A4',
            print_background=True,  # 关键：保留 Mermaid 图表的背景/颜色
            margin={
                'top': '20mm',
                'bottom': '20mm',
                'left': '15mm',
                'right': '15mm'
            }
        )

        # 关闭浏览器
        browser.close()

def stop_dash_server():
    """停止 Dash 服务器"""
    global dash_app, server_running, server_thread
    if dash_app and server_running:
        # 关闭 Flask 服务器
        dash_app.server.shutdown()
        server_thread.join()
        server_running = False

def main():
    # 检查并安装依赖
    check_and_install_dependencies()

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='将包含 Mermaid 的 Markdown 一键导出为 PDF')
    parser.add_argument('--source', '-s', required=True, help='源 Markdown 文件路径（必填）')
    parser.add_argument('--output', '-o', required=True, help='输出 PDF 文件路径（必填）')
    parser.add_argument('--port', '-p', type=int, default=8050, help='Dash 服务器端口（默认8050）')

    args = parser.parse_args()

    try:
        # 1. 启动 Dash 服务器
        print(f"\n正在读取 Markdown 文件：{args.source}")
        start_dash_server(args.source, args.port)

        # 2. 导出 PDF
        print(f"正在渲染 Mermaid 并导出 PDF：{args.output}")
        export_pdf(args.port, args.output)

        print(f"\n✅ PDF 导出成功！文件路径：{os.path.abspath(args.output)}")

    except Exception as e:
        print(f"\n❌ 导出失败：{str(e)}")
        raise
    finally:
        # 3. 停止服务器
        stop_dash_server()

if __name__ == "__main__":
    main()
