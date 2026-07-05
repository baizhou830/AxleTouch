"""
使用 PyInstaller 打包桌宠为 exe
用法: python build.py
"""
import os
import sys
import subprocess

# 项目根目录
ROOT = os.path.dirname(os.path.abspath(__file__))

# 输出目录
OUTPUT_DIR = os.path.join(ROOT, "dist")

# 需要打包的数据文件（资源文件）
DATA_FILES = [
    ("assets", "assets"),  # assets 目录下的所有文件
]

# 排除不必要的模块以减少体积
EXCLUDES = [
    "tkinter",
    "turtle",
    "test",
    "distutils",
    "setuptools",
    "unittest",
    "email",
    "http",
    "xml",
    "xmlrpc",
]

def main():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                 # 单文件 exe
        "--windowed",                 # 无控制台窗口（GUI 应用）
        "--name", "AxleTouch",
        "--icon", os.path.join(ROOT, "assets", "icon.ico"),  # exe 图标
        "--distpath", OUTPUT_DIR,
        "--noconfirm",
        "--clean",
    ]

    # 添加数据文件
    for src, dst in DATA_FILES:
        cmd.extend(["--add-data", f"{os.path.join(ROOT, src)}{os.pathsep}{dst}"])

    # 添加排除
    for mod in EXCLUDES:
        cmd.extend(["--exclude-module", mod])

    # 入口脚本
    cmd.append(os.path.join(ROOT, "main.py"))

    print("=" * 60)
    print("开始打包 AxleTouch ...")
    print("=" * 60)
    print(f"Python: {sys.executable}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"命令: {' '.join(cmd)}")
    print("=" * 60)

    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode == 0:
        print("\n✅ 打包成功！")
        print(f"📦 exe 文件位于: {os.path.join(OUTPUT_DIR, 'AxleTouch.exe')}")
        print("\n💡 首次运行前，请将 config.toml 复制到 exe 同目录下")
        print("💡 assets 目录已内嵌到 exe 中，无需额外复制")
    else:
        print(f"\n❌ 打包失败，返回值: {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
