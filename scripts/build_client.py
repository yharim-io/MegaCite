import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def get_playwright_browsers_path():
    """获取本地 Playwright 浏览器的安装路径"""
    system = platform.system()
    home = Path.home()
    
    if system == 'Windows':
        path = home / 'AppData' / 'Local' / 'ms-playwright'
    elif system == 'Darwin': # macOS
        path = home / 'Library' / 'Caches' / 'ms-playwright'
    else: # Linux
        path = home / '.cache' / 'ms-playwright'
        
    if not path.exists():
        print(f"Error: 找不到 Playwright 浏览器路径: {path}")
        print("请先运行: playwright install chromium")
        sys.exit(1)
    
    return path

def build():
    # 1. 准备路径
    browsers_src = get_playwright_browsers_path()
    print(f"[+] 找到浏览器路径: {browsers_src}")
    
    # 2. 创建压缩包 (绕过代码签名检查)
    # 将浏览器目录的内容压缩到当前目录下的 playwright-browsers.zip
    print(f"[+] 正在压缩浏览器内核 (这可能需要几秒钟)...")
    zip_base_name = "playwright-browsers"
    shutil.make_archive(zip_base_name, 'zip', root_dir=browsers_src)
    zip_file = f"{zip_base_name}.zip"
    print(f"[+] 压缩完成: {zip_file}")

    # 3. 构造 PyInstaller 参数
    # 格式: 源文件路径:目标路径 (Windows用; Unix用:)
    sep = ';' if platform.system() == 'Windows' else ':'
    # 将 zip 文件打包进 exe 的根目录
    add_data_arg = f"{zip_file}{sep}."
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",              
        "--name", "MegaCiteClient", 
        "--paths", ".",           
        "--add-data", add_data_arg, # 核心：打包 ZIP 文件而非原始文件夹
        "client/verifier.py"
    ]
    
    print(f"\n[+] 开始构建...")
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*50)
        print(f"[SUCCESS] 打包完成！")
        print(f"可执行文件位置: dist/MegaCiteClient{'.exe' if platform.system() == 'Windows' else ''}")
        print("="*50)
    except subprocess.CalledProcessError:
        print("\n[FAIL] 打包失败")
    finally:
        # 4. 清理临时压缩包
        if os.path.exists(zip_file):
            os.remove(zip_file)
            print(f"[*] 清理临时文件: {zip_file}")

if __name__ == "__main__":
    build()