#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件整理工具打包脚本
用于将Python应用程序打包为Windows可执行文件
"""

import os
import sys
import shutil
from pathlib import Path

def create_build_script():
    """创建PyInstaller打包脚本"""
    
    # 检查是否存在图标文件
    icon_path = "app_icon.ico"
    if not os.path.exists(icon_path):
        print("⚠️  警告：未找到图标文件 app_icon.ico")
        print("请确保图标文件存在，否则打包后的exe将使用默认图标")
        icon_option = ""
    else:
        icon_option = f'--icon="{icon_path}"'
        print(f"✅ 找到图标文件: {icon_path}")
    
    # PyInstaller打包命令
    build_command = f'''
pyinstaller --noconfirm --onefile --windowed \
  --name "文件整理工具" \
  {icon_option} \
  --add-data "*.json;." \
  --add-data "*.log;." \
  --hidden-import="PyQt6.QtWidgets" \
  --hidden-import="PyQt6.QtGui" \
  --hidden-import="PyQt6.QtCore" \
  --hidden-import="uuid" \
  --hidden-import="os" \
  --hidden-import="sys" \
  --hidden-import="json" \
  --hidden-import="datetime" \
  --hidden-import="logging" \
  --hidden-import="threading" \
  --hidden-import="time" \
  --hidden-import="shutil" \
  --hidden-import="pathlib" \
  file_copy.py
'''
    
    return build_command

def create_installer_script():
    """创建安装脚本"""
    
    installer_script = '''@echo off
chcp 65001 >nul

echo ========================================
echo       文件整理工具安装程序
echo ========================================
echo.

set "SOURCE_EXE=dist\\文件整理工具.exe"
set "DESKTOP_DIR=%USERPROFILE%\\Desktop"
set "START_MENU_DIR=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"

if not exist "%SOURCE_EXE%" (
    echo ❌ 错误：未找到打包后的可执行文件
    echo 请先运行 build.py 进行打包
    pause
    exit /b 1
)

echo 📋 正在安装文件整理工具...
echo.

:: 复制到桌面
copy "%SOURCE_EXE%" "%DESKTOP_DIR%\\文件整理工具.exe" >nul
if %errorlevel% equ 0 (
    echo ✅ 已创建桌面快捷方式
) else (
    echo ❌ 创建桌面快捷方式失败
)

:: 复制到开始菜单
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%" >nul
copy "%SOURCE_EXE%" "%START_MENU_DIR%\\文件整理工具.exe" >nul
if %errorlevel% equ 0 (
    echo ✅ 已添加到开始菜单
) else (
    echo ❌ 添加到开始菜单失败
)

echo.
echo 🎉 安装完成！
echo.
echo 📍 桌面快捷方式: %DESKTOP_DIR%\\文件整理工具.exe
echo 📍 开始菜单位置: %START_MENU_DIR%\\文件整理工具.exe
echo.
pause
'''
    
    return installer_script

def main():
    """主函数"""
    
    print("🚀 文件整理工具打包程序")
    print("=" * 50)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return
    
    # 创建打包脚本
    build_command = create_build_script()
    
    # 创建安装脚本
    installer_script = create_installer_script()
    
    # 保存打包脚本
    with open("build.bat", "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("chcp 65001 >nul\n")
        f.write("echo 正在打包文件整理工具...\n")
        f.write("echo.\n")
        f.write(build_command)
        f.write("\necho.\n")
        f.write("echo 🎉 打包完成！\n")
        f.write("echo 可执行文件位置: dist\\文件整理工具.exe\n")
        f.write("pause\n")
    
    # 保存安装脚本
    with open("install.bat", "w", encoding="utf-8") as f:
        f.write(installer_script)
    
    print("📁 已创建打包脚本:")
    print("   - build.bat (打包脚本)")
    print("   - install.bat (安装脚本)")
    print()
    print("📋 使用说明:")
    print("   1. 运行 build.bat 进行打包")
    print("   2. 打包完成后运行 install.bat 进行安装")
    print()
    print("⚠️  注意事项:")
    print("   - 确保已安装 PyInstaller: pip install pyinstaller")
    print("   - 如需自定义图标，请将图标文件命名为 app_icon.ico")
    print()
    
    # 询问是否立即打包
    response = input("是否立即开始打包? (y/n): ").lower().strip()
    if response == 'y':
        print("\n🔄 开始打包...")
        os.system("build.bat")
    else:
        print("\n📝 您可以在需要时运行 build.bat 进行打包")

if __name__ == "__main__":
    main()