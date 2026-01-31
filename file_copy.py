#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件整理工具
功能：多平台文件复制、整理工具，支持多种复制方式和任务管理
"""

import sys
import os
import time
import threading
import logging
import shutil
import uuid
import platform
import subprocess
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGridLayout, QProgressBar, QTextEdit,
    QFileDialog, QLineEdit, QDialog, QGroupBox,
    QFormLayout, QSpinBox, QSizePolicy, QFrame, QComboBox,
    QToolButton, QSystemTrayIcon, QStyle, QMenu, QScrollArea,
    QTreeView, QCheckBox, QTableView, QHeaderView, QAbstractItemView, QButtonGroup, QRadioButton,
    QListWidget, QListWidgetItem, QTabWidget, QMenuBar, QStatusBar, QDateEdit, QTimeEdit, QSplitter,
    QCalendarWidget, QTableWidget, QTableWidgetItem
)
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtGui import QAction, QTextCursor
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QIcon, QPixmap, QGuiApplication, QRadialGradient, QPalette, QTextDocument
from PyQt6.QtCore import (Qt, QTimer, QPoint, QRect, QThread, QObject, pyqtSignal, pyqtSlot,
                            QSettings, QRectF, QPointF, QDate, QTime, QDateTime,
                            QMutex, QWaitCondition)

# 导入图标管理器
from icon_manager import icon_manager


# ===== 跨平台自启动管理器 =====
class StartupManager:
    """跨平台自启动管理器
    
    支持Windows、macOS、Linux三大操作系统的开机自启动功能
    包含启动失败重试机制和详细的错误日志记录
    """
    
    def __init__(self, app_name="FileOrganizer", app_path=None):
        """初始化自启动管理器
        
        Args:
            app_name: 应用程序名称
            app_path: 应用程序可执行文件路径
        """
        self.app_name = app_name
        self.app_path = app_path or sys.executable
        self.platform = platform.system().lower()
        self.logger = self._setup_logger()
        
        # 启动重试配置
        self.max_retries = 3
        self.retry_delay = 5  # 秒
        
        self.logger.info(f"自启动管理器初始化 - 平台: {self.platform}, 应用路径: {self.app_path}")
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(f"{self.app_name}.StartupManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def enable_startup(self, startup_type="user"):
        """启用开机自启动
        
        Args:
            startup_type: 启动类型 - "user"(用户登录后), "system"(系统启动后)
        """
        self.logger.info(f"启用开机自启动 - 类型: {startup_type}")
        
        for attempt in range(self.max_retries):
            try:
                if self.platform == "windows":
                    success = self._enable_windows_startup(startup_type)
                elif self.platform == "darwin":
                    success = self._enable_macos_startup(startup_type)
                elif self.platform == "linux":
                    success = self._enable_linux_startup(startup_type)
                else:
                    self.logger.error(f"不支持的操作系统: {self.platform}")
                    return False
                
                if success:
                    self.logger.info("开机自启动启用成功")
                    return True
                else:
                    self.logger.warning(f"启用自启动失败，第{attempt + 1}次尝试")
                    
            except Exception as e:
                self.logger.error(f"启用自启动时发生错误 (尝试 {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        self.logger.error("启用开机自启动失败，已达到最大重试次数")
        return False
    
    def disable_startup(self):
        """禁用开机自启动"""
        self.logger.info("禁用开机自启动")
        
        for attempt in range(self.max_retries):
            try:
                if self.platform == "windows":
                    success = self._disable_windows_startup()
                elif self.platform == "darwin":
                    success = self._disable_macos_startup()
                elif self.platform == "linux":
                    success = self._disable_linux_startup()
                else:
                    self.logger.error(f"不支持的操作系统: {self.platform}")
                    return False
                
                if success:
                    self.logger.info("开机自启动禁用成功")
                    return True
                else:
                    self.logger.warning(f"禁用自启动失败，第{attempt + 1}次尝试")
                    
            except Exception as e:
                self.logger.error(f"禁用自启动时发生错误 (尝试 {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        self.logger.error("禁用开机自启动失败，已达到最大重试次数")
        return False
    
    def is_startup_enabled(self):
        """检查是否已启用开机自启动"""
        try:
            if self.platform == "windows":
                return self._check_windows_startup()
            elif self.platform == "darwin":
                return self._check_macos_startup()
            elif self.platform == "linux":
                return self._check_linux_startup()
            else:
                self.logger.error(f"不支持的操作系统: {self.platform}")
                return False
        except Exception as e:
            self.logger.error(f"检查自启动状态时发生错误: {e}")
            return False
    
    def _enable_windows_startup(self, startup_type):
        """启用Windows开机自启动"""
        import winreg
        
        if startup_type == "user":
            # 用户登录后启动
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            hive = winreg.HKEY_CURRENT_USER
        else:
            # 系统启动后启动（需要管理员权限）
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            hive = winreg.HKEY_LOCAL_MACHINE
        
        try:
            # 添加命令行参数，使自启动时最小化到系统托盘
            startup_command = f'"{self.app_path}" --startup'
            
            key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, startup_command)
            winreg.CloseKey(key)
            
            self.logger.info(f"Windows自启动设置成功 - 命令: {startup_command}")
            return True
        except PermissionError:
            self.logger.error("需要管理员权限来设置系统级自启动")
            return False
        except Exception as e:
            self.logger.error(f"Windows自启动设置失败: {e}")
            return False
    
    def _disable_windows_startup(self):
        """禁用Windows开机自启动"""
        import winreg
        
        # 尝试从用户和系统注册表中删除
        hives = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
        success = True
        for hive in hives:
            try:
                key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_WRITE)
                winreg.DeleteValue(key, self.app_name)
                winreg.CloseKey(key)
            except FileNotFoundError:
                # 注册表项不存在，忽略
                pass
            except Exception as e:
                self.logger.warning(f"删除Windows自启动项失败 ({hive}): {e}")
                success = False
        
        return success
    
    def _check_windows_startup(self):
        """检查Windows开机自启动状态"""
        import winreg
        
        hives = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
        for hive in hives:
            try:
                key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_READ)
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    winreg.CloseKey(key)
                    if value == self.app_path:
                        return True
                except FileNotFoundError:
                    # 注册表值不存在
                    pass
                winreg.CloseKey(key)
            except Exception:
                # 无法访问注册表，继续检查下一个
                continue
        
        return False
    
    def _enable_macos_startup(self, startup_type):
        """启用macOS开机自启动"""
        try:
            if startup_type == "user":
                # 用户登录后启动 - 使用LaunchAgents
                plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                <key>Label</key>
                <string>com.{self.app_name.lower()}</string>
                <key>ProgramArguments</key>
                <array>
                <string>{self.app_path}</string>
                </array>
                <key>RunAtLoad</key>
                <true/>
                <key>KeepAlive</key>
                <false/>
                </dict>
                </plist>'''
                
                plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name.lower()}.plist")
                os.makedirs(os.path.dirname(plist_path), exist_ok=True)
                
                with open(plist_path, 'w') as f:
                    f.write(plist_content)
                
                # 加载启动项
                subprocess.run(['launchctl', 'load', plist_path], check=True)
                return True
            
            else:
                # 系统启动后启动（需要管理员权限）
                self.logger.warning("macOS系统级自启动需要管理员权限，建议使用用户级自启动")
                return False
                
        except Exception as e:
            self.logger.error(f"macOS自启动设置失败: {e}")
            return False
    
    def _disable_macos_startup(self):
        """禁用macOS开机自启动"""
        try:
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name.lower()}.plist")
            
            # 卸载启动项
            if os.path.exists(plist_path):
                subprocess.run(['launchctl', 'unload', plist_path], check=True)
                os.remove(plist_path)
                return True
            
            return True  # 文件不存在也算成功
            
        except Exception as e:
            self.logger.error(f"macOS自启动禁用失败: {e}")
            return False
    
    def _check_macos_startup(self):
        """检查macOS开机自启动状态"""
        try:
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name.lower()}.plist")
            return os.path.exists(plist_path)
        except Exception as e:
            self.logger.error(f"检查macOS自启动状态失败: {e}")
            return False
    
    def _enable_linux_startup(self, startup_type):
        """启用Linux开机自启动"""
        try:
            if startup_type == "user":
                # 用户登录后启动 - 使用autostart目录
                autostart_dir = os.path.expanduser("~/.config/autostart")
                desktop_file = os.path.join(autostart_dir, f"{self.app_name}.desktop")
                
                desktop_content = f'''[Desktop Entry]
                Type=Application
                Name={self.app_name}
                Exec={self.app_path}
                Hidden=false
                NoDisplay=false
                X-GNOME-Autostart-enabled=true
                '''
                
                os.makedirs(autostart_dir, exist_ok=True)
                with open(desktop_file, 'w') as f:
                    f.write(desktop_content)
                
                return True
            
            else:
                # 系统启动后启动（需要root权限）
                self.logger.warning("Linux系统级自启动需要root权限，建议使用用户级自启动")
                return False
                
        except Exception as e:
            self.logger.error(f"Linux自启动设置失败: {e}")
            return False
    
    def _disable_linux_startup(self):
        """禁用Linux开机自启动"""
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, f"{self.app_name}.desktop")
            
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                return True
            
            return True  # 文件不存在也算成功
            
        except Exception as e:
            self.logger.error(f"Linux自启动禁用失败: {e}")
            return False
    
    def _check_linux_startup(self):
        """检查Linux开机自启动状态"""
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, f"{self.app_name}.desktop")
            return os.path.exists(desktop_file)
        except Exception as e:
            self.logger.error(f"检查Linux自启动状态失败: {e}")
            return False

# ===== 文件整理工具 =====
"""
文件整理工具主要组件：
1. TaskConfigDialog - 任务配置对话框，用于设置单个复制任务的参数
2. CopyThread - 复制线程，支持多种复制方式和进度保存
3. FileOrganizerApp - 主应用窗口，包含任务管理和执行功能
4. StartupManager - 跨平台自启动管理器
"""

class TaskConfigDialog(QDialog):
    """任务配置对话框，用于为每个复制任务设置独立的配置"""
    
    DIALOG_STYLE_SHEET = """
        /* ===== 对话框基础样式 ===== */
        QDialog {
            background-color: #f1f3f5;
        }
        
        /* ===== 组框样式 ===== */
        QGroupBox {
            border: 1px solid #e9ecef;
            border-radius: 6px;
            margin-top: 12px;
            background-color: #ffffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 8px 0 8px;
            background-color: #ffffff;
            color: #343a40;
            font-weight: 600;
            font-size: 14px;
        }
        
        /* ===== 输入控件样式 ===== */
        QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit {
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 8px 12px;
            background-color: #ffffff;
            color: #343a40;
            min-height: 36px;
            font-size: 14px;
        }
        
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
            border-color: #5c7cfa;
            outline: none;
        }
        
        QLineEdit::placeholder, QComboBox::placeholder {
            color: #868e96;
        }
        
        /* ===== 按钮样式 ===== */
        QPushButton {
            background-color: #5c7cfa;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
            min-height: 32px;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #748ffc;
        }
        
        QPushButton:pressed {
            background-color: #4c6ef5;
        }
        
        QPushButton:disabled {
            background-color: #adb5bd;
        }
        
        /* ===== 滚动区域样式 ===== */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            width: 12px;
            background-color: #e9ecef;
        }
        
        QScrollBar::handle:vertical {
            background-color: #dee2e6;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #868e96;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* ===== 标签样式 ===== */
        QLabel {
            color: #343a40;
            font-size: 14px;
        }
    """
    
    def __init__(self, parent=None, task_config=None):
        """初始化任务配置对话框
        
        Args:
            parent: 父窗口
            task_config: 现有任务配置，用于编辑模式
        """
        super().__init__(parent)
        self.setWindowTitle("任务配置")
        self.setStyleSheet(self.DIALOG_STYLE_SHEET)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 任务配置数据
        self.task_config = task_config if task_config else {
            "task_id": str(uuid.uuid4()),
            "source_folder": "",
            "dest_folder": "",
            "copy_mode": "完整文件夹结构复制",
            "file_filters": [],
            "suffix_filters": [],
            "description": "",
            "status": "未完成"
        }
        
        self.init_ui()
        self.setup_shadow_effect()
        self.setup_animation()
        self.center_window()
    
    def setup_shadow_effect(self):
        """设置窗口阴影效果"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def setup_animation(self):
        """设置窗口动画效果"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        # 初始化动画，不设置目标几何形状（将在showEvent中设置）
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(250)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(150)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # 连接淡出动画完成信号
        self.fade_out_animation.finished.connect(self.close)
    
    def showEvent(self, event):
        """显示事件触发动画"""
        super().showEvent(event)
        
        # 确保窗口居中
        self.center_window()
        
        # 在显示时获取正确的目标几何形状
        self._target_geometry = self.geometry()
        
        start_geom = QRect(self._target_geometry.x(), self._target_geometry.y() + 20,
                          self._target_geometry.width(), self._target_geometry.height())
        
        self.scale_animation.setStartValue(start_geom)
        self.scale_animation.setEndValue(self._target_geometry)
        self.scale_animation.start()
        self.fade_in_animation.start()
    
    def closeEvent(self, event):
        """关闭事件触发动画"""
        self.fade_out_animation.start()
        event.ignore()
        
    def center_window(self):
        """将窗口左上角对齐到主窗口左上角，确保所有窗口位置一致"""
        # 获取所有屏幕
        screens = QGuiApplication.screens()
        if not screens:
            return
        
        # 获取主屏幕的左上角位置作为所有窗口的基准位置
        main_screen = screens[0]
        screen_geometry = main_screen.geometry()
        
        # 设置所有窗口的左上角都对齐到主屏幕的左上角偏右下方一点，避免完全重叠
        top_left = QPoint(screen_geometry.x() + 50, screen_geometry.y() + 50)
        
        # 设置窗口位置
        self.move(top_left)
    
    def init_ui(self):
        """初始化对话框界面 - 优化布局"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建主滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== 第一部分：基本配置 - 优化布局 ==========
        basic_group = QGroupBox("基本配置")
        basic_layout = QGridLayout(basic_group)  # 使用GridLayout更灵活
        basic_layout.setSpacing(15)
        
        # 任务描述 (0,0)
        basic_layout.addWidget(QLabel("任务描述："), 0, 0, 1, 1)
        self.desc_edit = QLineEdit(self.task_config.get("description", ""))
        self.desc_edit.setPlaceholderText("输入任务描述（可选）")
        self.desc_edit.setMinimumWidth(300)
        basic_layout.addWidget(self.desc_edit, 0, 1, 1, 3)
        
        # 源文件夹 (1,0)
        basic_layout.addWidget(QLabel("源文件夹："), 1, 0, 1, 1)
        self.source_edit = QLineEdit(self.task_config.get("source_folder", ""))
        self.source_edit.setReadOnly(True)
        basic_layout.addWidget(self.source_edit, 1, 1, 1, 2)
        browse_btn = QPushButton("浏览...")
        browse_btn.setMaximumWidth(100)  # 限制按钮宽度
        browse_btn.clicked.connect(self.browse_source)
        basic_layout.addWidget(browse_btn, 1, 3, 1, 1)
        
        # 目标文件夹 (2,0)
        basic_layout.addWidget(QLabel("目标文件夹："), 2, 0, 1, 1)
        self.dest_edit = QLineEdit(self.task_config.get("dest_folder", ""))
        self.dest_edit.setReadOnly(True)
        basic_layout.addWidget(self.dest_edit, 2, 1, 1, 2)
        browse_dest_btn = QPushButton("浏览...")
        browse_dest_btn.setMaximumWidth(100)  # 限制按钮宽度
        browse_dest_btn.clicked.connect(self.browse_dest)
        basic_layout.addWidget(browse_dest_btn, 2, 3, 1, 1)
        
        # 复制方式 (3,0)
        basic_layout.addWidget(QLabel("复制方式："), 3, 0, 1, 1)
        self.copy_mode_combo = QComboBox()
        self.copy_mode_combo.addItems([
            "完整文件夹结构复制", 
            "文件内容合并复制", 
            "增量差异复制", 
            "覆盖式复制"
        ])
        # 设置默认值
        copy_mode = self.task_config.get("copy_mode", "完整文件夹结构复制")
        index = self.copy_mode_combo.findText(copy_mode)
        if index != -1:
            self.copy_mode_combo.setCurrentIndex(index)
        self.copy_mode_combo.setMinimumWidth(200)
        basic_layout.addWidget(self.copy_mode_combo, 3, 1, 1, 3)
        
        layout.addWidget(basic_group)
        
        # ========== 第二部分：筛选条件 - 优化布局 ==========
        filter_group = QGroupBox("文件筛选条件")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(20)
        
        # 文件名筛选部分
        filename_filter_widget = QWidget()
        filename_filter_layout = QVBoxLayout(filename_filter_widget)
        filename_filter_layout.setSpacing(10)
        
        # 文件名筛选输入行
        filename_layout = QHBoxLayout()
        filename_label = QLabel("文件名包含：")
        filename_label.setMinimumWidth(80)
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("输入关键字，多个用逗号分隔")
        add_filename_btn = QPushButton("添加")
        add_filename_btn.setMaximumWidth(80)  # 限制按钮宽度
        add_filename_btn.clicked.connect(self.add_filename_filter)
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_edit)
        filename_layout.addWidget(add_filename_btn)
        filename_filter_layout.addLayout(filename_layout)
        
        # 文件名筛选列表
        filename_filter_layout.addWidget(QLabel("文件名筛选条件列表："))
        self.filename_list = QListWidget()
        self.filename_list.setMinimumHeight(120)
        filename_filter_layout.addWidget(self.filename_list)
        
        filter_layout.addWidget(filename_filter_widget)
        
        # 分隔线
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setFrameShadow(QFrame.Shadow.Sunken)
        filter_layout.addWidget(vline)
        
        # 文件后缀筛选部分
        suffix_filter_widget = QWidget()
        suffix_filter_layout = QVBoxLayout(suffix_filter_widget)
        suffix_filter_layout.setSpacing(10)
        
        # 文件后缀筛选输入行
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("文件后缀：")
        suffix_label.setMinimumWidth(80)
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText("输入后缀，多个用逗号分隔，如：.txt,.doc")
        add_suffix_btn = QPushButton("添加")
        add_suffix_btn.setMaximumWidth(80)  # 限制按钮宽度
        add_suffix_btn.clicked.connect(self.add_suffix_filter)
        suffix_layout.addWidget(suffix_label)
        suffix_layout.addWidget(self.suffix_edit)
        suffix_layout.addWidget(add_suffix_btn)
        suffix_filter_layout.addLayout(suffix_layout)
        
        # 文件后缀筛选列表
        suffix_filter_layout.addWidget(QLabel("文件后缀筛选条件列表："))
        self.suffix_list = QListWidget()
        self.suffix_list.setMinimumHeight(120)
        suffix_filter_layout.addWidget(self.suffix_list)
        
        filter_layout.addWidget(suffix_filter_widget)
        
        layout.addWidget(filter_group)
        
        # 清空筛选条件按钮
        clear_filters_btn = QPushButton("清空所有筛选条件")
        clear_filters_btn.setMaximumWidth(200)  # 限制按钮宽度
        clear_filters_btn.clicked.connect(self.clear_all_filters)
        layout.addWidget(clear_filters_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        # ========== 按钮区域 - 居中显示 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setSpacing(20)
        
        save_btn = QPushButton("保存")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        # 添加垂直间距
        spacer = QWidget()
        spacer.setMinimumHeight(20)
        layout.addWidget(spacer)
        
        layout.addLayout(btn_layout)
        
        # 加载现有筛选条件
        self.load_filters()
        
        # 将内容容器设置为滚动区域的部件
        scroll_area.setWidget(content_widget)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)
        
        # 设置最小尺寸
        self.setMinimumSize(800, 500)
    
    def browse_source(self):
        """浏览选择源文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if folder:
            self.source_edit.setText(folder)
            self.task_config["source_folder"] = folder
    
    def browse_dest(self):
        """浏览选择目标文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if folder:
            self.dest_edit.setText(folder)
            self.task_config["dest_folder"] = folder
    
    def add_filename_filter(self):
        """添加文件名筛选条件"""
        text = self.filename_edit.text().strip()
        if text:
            filters = [f.strip() for f in text.split(",") if f.strip()]
            for f in filters:
                if f not in self.task_config["file_filters"]:
                    self.task_config["file_filters"].append(f)
            self.filename_edit.clear()
            self.update_filename_list()
    
    def add_suffix_filter(self):
        """添加文件后缀筛选条件"""
        text = self.suffix_edit.text().strip()
        if text:
            filters = [f.strip() for f in text.split(",") if f.strip()]
            for f in filters:
                # 确保后缀名以点开头
                if not f.startswith("."):
                    f = "." + f
                if f not in self.task_config["suffix_filters"]:
                    self.task_config["suffix_filters"].append(f)
            self.suffix_edit.clear()
            self.update_suffix_list()
    
    def update_filename_list(self):
        """更新文件名筛选条件列表"""
        self.filename_list.clear()
        for f in self.task_config["file_filters"]:
            item = QListWidgetItem(f)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.filename_list.addItem(item)
    
    def update_suffix_list(self):
        """更新文件后缀筛选条件列表"""
        self.suffix_list.clear()
        for f in self.task_config["suffix_filters"]:
            item = QListWidgetItem(f)
            self.suffix_list.addItem(item)
    
    def clear_all_filters(self):
        """清空所有筛选条件"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有筛选条件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.task_config["file_filters"].clear()
            self.task_config["suffix_filters"].clear()
            self.update_filename_list()
            self.update_suffix_list()
    
    def load_filters(self):
        """加载现有筛选条件"""
        self.update_filename_list()
        self.update_suffix_list()
    
    def get_task_config(self):
        """获取任务配置
        
        Returns:
            dict: 任务配置字典
        """
        # 更新配置数据
        self.task_config["description"] = self.desc_edit.text().strip()
        self.task_config["source_folder"] = self.source_edit.text().strip()
        self.task_config["dest_folder"] = self.dest_edit.text().strip()  # 保存目标文件夹
        self.task_config["copy_mode"] = self.copy_mode_combo.currentText()
        
        # 更新文件名筛选条件，只保留被勾选的
        self.task_config["file_filters"] = []
        for i in range(self.filename_list.count()):
            item = self.filename_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.task_config["file_filters"].append(item.text())
        
        return self.task_config
    
    def accept(self):
        """确认保存配置"""
        # 验证配置
        if not self.source_edit.text().strip():
            QMessageBox.warning(self, "警告", "请选择源文件夹")
            return
        
        if not self.dest_edit.text().strip():
            QMessageBox.warning(self, "警告", "请选择目标文件夹")
            return
        
        super().accept()


class ScheduledTaskConfigDialog(QDialog):
    """定时任务配置对话框，用于设置定时任务的参数"""
    
    def __init__(self, parent=None, task_config=None):
        """初始化定时任务配置对话框
        
        Args:
            parent: 父窗口
            task_config: 现有任务配置，用于编辑模式
        """
        super().__init__(parent)
        self.setWindowTitle("定时任务配置")
        self.setStyleSheet(TaskConfigDialog.DIALOG_STYLE_SHEET)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 定时任务配置数据
        self.task_config = task_config if task_config else {
            "task_id": str(uuid.uuid4()),
            "name": "",
            "description": "",
            "enabled": True,
            "trigger_type": "once",
            "trigger_time": datetime.now(),
            "repeat_interval": 1,
            "weekdays": [],
            "month_day": 1,
            "linked_task_id": "",
            "last_executed": None,
            "next_execution": None,
            "status": "pending"
        }
        
        self.init_ui()
        self.setup_shadow_effect()
        self.setup_animation()
        self.center_window()
    
    def setup_shadow_effect(self):
        """设置窗口阴影效果"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def setup_animation(self):
        """设置窗口动画效果"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        # 初始化动画，不设置目标几何形状（将在showEvent中设置）
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(250)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(150)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # 连接淡出动画完成信号
        self.fade_out_animation.finished.connect(self.close)
    
    def showEvent(self, event):
        """显示事件触发动画"""
        super().showEvent(event)
        
        # 确保窗口居中
        self.center_window()
        
        # 在显示时获取正确的目标几何形状
        self._target_geometry = self.geometry()
        
        start_geom = QRect(self._target_geometry.x(), self._target_geometry.y() + 20,
                          self._target_geometry.width(), self._target_geometry.height())
        
        self.scale_animation.setStartValue(start_geom)
        self.scale_animation.setEndValue(self._target_geometry)
        self.scale_animation.start()
        self.fade_in_animation.start()
    
    def closeEvent(self, event):
        """关闭事件触发动画"""
        self.fade_out_animation.start()
        event.ignore()
        
    def center_window(self):
        """将窗口左上角对齐到主窗口左上角，确保所有窗口位置一致"""
        # 获取所有屏幕
        screens = QGuiApplication.screens()
        if not screens:
            return
        
        # 获取主屏幕的左上角位置作为所有窗口的基准位置
        main_screen = screens[0]
        screen_geometry = main_screen.geometry()
        
        # 设置所有窗口的左上角都对齐到主屏幕的左上角偏右下方一点，避免完全重叠
        top_left = QPoint(screen_geometry.x() + 50, screen_geometry.y() + 50)
        
        # 设置窗口位置
        self.move(top_left)
    
    def init_ui(self):
        """初始化定时任务配置对话框界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setSpacing(10)
        
        # 任务名称
        basic_layout.addWidget(QLabel("任务名称："), 0, 0, 1, 1)
        self.name_edit = QLineEdit(self.task_config.get("name", ""))
        self.name_edit.setPlaceholderText("输入定时任务名称")
        basic_layout.addWidget(self.name_edit, 0, 1, 1, 3)
        
        # 任务描述
        basic_layout.addWidget(QLabel("任务描述："), 1, 0, 1, 1)
        self.desc_edit = QLineEdit(self.task_config.get("description", ""))
        self.desc_edit.setPlaceholderText("输入定时任务描述")
        basic_layout.addWidget(self.desc_edit, 1, 1, 1, 3)
        
        # 关联的文件复制任务
        basic_layout.addWidget(QLabel("关联任务："), 2, 0, 1, 1)
        self.task_combo = QComboBox()
        # 这里需要填充已有的文件复制任务
        basic_layout.addWidget(self.task_combo, 2, 1, 1, 3)
        
        # 启用状态
        self.enabled_check = QCheckBox("启用此定时任务")
        self.enabled_check.setChecked(self.task_config.get("enabled", True))
        basic_layout.addWidget(self.enabled_check, 3, 0, 1, 4)
        
        content_layout.addWidget(basic_group)
        
        # 触发条件
        trigger_group = QGroupBox("触发条件")
        trigger_layout = QVBoxLayout(trigger_group)
        
        # 触发类型
        trigger_type_layout = QHBoxLayout()
        trigger_type_layout.addWidget(QLabel("触发类型："))
        self.trigger_type_combo = QComboBox()
        self.trigger_type_combo.addItems(["一次性", "每日", "每周", "每月"])
        trigger_type = self.task_config.get("trigger_type", "once")
        trigger_type_map = {"once": 0, "daily": 1, "weekly": 2, "monthly": 3}
        self.trigger_type_combo.setCurrentIndex(trigger_type_map.get(trigger_type, 0))
        self.trigger_type_combo.currentIndexChanged.connect(self.on_trigger_type_changed)
        trigger_type_layout.addWidget(self.trigger_type_combo)
        trigger_type_layout.addStretch()
        trigger_layout.addLayout(trigger_type_layout)
        
        # 触发时间
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("触发时间："))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(self.task_config.get("trigger_time", datetime.now()).date())
        time_layout.addWidget(self.date_edit)
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(self.task_config.get("trigger_time", datetime.now()).time())
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        trigger_layout.addLayout(time_layout)
        
        # 重复间隔（仅适用于每日、每周、每月）
        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(QLabel("重复间隔："))
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setMinimum(1)
        self.repeat_spin.setValue(self.task_config.get("repeat_interval", 1))
        repeat_layout.addWidget(self.repeat_spin)
        self.repeat_unit_label = QLabel("天")
        repeat_layout.addWidget(self.repeat_unit_label)
        repeat_layout.addStretch()
        trigger_layout.addLayout(repeat_layout)
        
        # 每周执行的天数（仅适用于每周）
        self.weekdays_group = QGroupBox("每周执行天数")
        self.weekdays_layout = QHBoxLayout(self.weekdays_group)
        self.weekday_checks = []
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(weekdays):
            check = QCheckBox(day)
            if i in self.task_config.get("weekdays", []):
                check.setChecked(True)
            self.weekday_checks.append(check)
            self.weekdays_layout.addWidget(check)
        trigger_layout.addWidget(self.weekdays_group)
        
        # 每月执行的日期（仅适用于每月）
        self.monthday_widget = QWidget()
        self.monthday_layout = QHBoxLayout(self.monthday_widget)
        self.monthday_layout.setContentsMargins(0, 0, 0, 0)
        self.monthday_layout.addWidget(QLabel("每月执行日期："))
        self.monthday_spin = QSpinBox()
        self.monthday_spin.setMinimum(1)
        self.monthday_spin.setMaximum(31)
        self.monthday_spin.setValue(self.task_config.get("month_day", 1))
        self.monthday_layout.addWidget(self.monthday_spin)
        self.monthday_layout.addStretch()
        trigger_layout.addWidget(self.monthday_widget)
        
        content_layout.addWidget(trigger_group)
        
        # 初始显示控制
        self.on_trigger_type_changed(self.trigger_type_combo.currentIndex())
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)
        
        save_btn = QPushButton("保存")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        content_layout.addLayout(button_layout)
        
        # 将内容容器设置为滚动区域的部件
        scroll_area.setWidget(content_widget)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)
        
        # 设置固定尺寸，与主窗口比例协调
        self.setFixedSize(800, 500)
    
    def on_trigger_type_changed(self, index):
        """当触发类型改变时，更新界面控件的显示状态"""
        # 0: 一次性, 1: 每日, 2: 每周, 3: 每月
        if index == 0:  # 一次性
            self.repeat_spin.setEnabled(False)
            self.weekdays_group.hide()
            self.monthday_widget.hide()
        elif index == 1:  # 每日
            self.repeat_spin.setEnabled(True)
            self.repeat_unit_label.setText("天")
            self.weekdays_group.hide()
            self.monthday_widget.hide()
        elif index == 2:  # 每周
            self.repeat_spin.setEnabled(True)
            self.repeat_unit_label.setText("周")
            self.weekdays_group.show()
            self.monthday_widget.hide()
        elif index == 3:  # 每月
            self.repeat_spin.setEnabled(True)
            self.repeat_unit_label.setText("月")
            self.weekdays_group.hide()
            self.monthday_widget.show()
    
    def get_task_config(self):
        """获取定时任务配置
        
        Returns:
            dict: 定时任务配置字典
        """
        trigger_type_map = {0: "once", 1: "daily", 2: "weekly", 3: "monthly"}
        trigger_type = trigger_type_map.get(self.trigger_type_combo.currentIndex(), "once")
        
        # 计算触发时间
        trigger_time = datetime.combine(
            self.date_edit.date().toPyDate(),
            self.time_edit.time().toPyTime()
        )
        
        # 获取选中的工作日
        weekdays = []
        for i, check in enumerate(self.weekday_checks):
            if check.isChecked():
                weekdays.append(i)
        
        # 计算下次执行时间
        next_execution = self.calculate_next_execution(trigger_type, trigger_time, weekdays)
        
        # 获取选中的文件复制任务ID
        selected_task_id = self.task_combo.currentData()
        
        # 更新配置
        self.task_config.update({
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "enabled": self.enabled_check.isChecked(),
            "trigger_type": trigger_type,
            "trigger_time": trigger_time,
            "repeat_interval": self.repeat_spin.value(),
            "weekdays": weekdays,
            "month_day": self.monthday_spin.value(),
            "next_execution": next_execution,
            "linked_task_id": selected_task_id if selected_task_id else ""
        })
        
        return self.task_config
    
    def calculate_next_execution(self, trigger_type, trigger_time, weekdays):
        """计算下次执行时间
        
        Args:
            trigger_type: 触发类型
            trigger_time: 触发时间
            weekdays: 每周执行的天数
            
        Returns:
            datetime: 下次执行时间
        """
        now = datetime.now()
        next_time = trigger_time
        
        if next_time <= now:
            if trigger_type == "once":
                # 一次性任务如果时间已过，返回当前时间
                return now
            elif trigger_type == "daily":
                # 每日任务，计算下一天的同一时间
                days_to_add = (now - next_time).days + 1
                next_time += timedelta(days=days_to_add)
            elif trigger_type == "weekly":
                # 每周任务，计算下一个指定的工作日
                if not weekdays:
                    # 如果没有选择工作日，默认周一
                    weekdays = [0]
                
                # 找到下一个工作日
                current_weekday = now.weekday()  # 0是周一
                days_ahead = None
                for day in sorted(weekdays):
                    if day > current_weekday:
                        days_ahead = day - current_weekday
                        break
                
                if days_ahead is None:
                    # 本周没有更多的工作日，计算到下一周的第一个工作日
                    days_ahead = (7 - current_weekday) + sorted(weekdays)[0]
                
                next_time += timedelta(days=days_ahead)
            elif trigger_type == "monthly":
                # 每月任务，计算下一个月的指定日期
                # 简化处理，假设每个月都有31天
                next_time = next_time.replace(month=next_time.month + 1)
                # 处理月份溢出
                if next_time.month > 12:
                    next_time = next_time.replace(year=next_time.year + 1, month=1)
        
        return next_time
    
    def load_tasks(self, tasks):
        """加载已有的文件复制任务
        
        Args:
            tasks: 文件复制任务列表
        """
        self.task_combo.clear()
        for task in tasks:
            self.task_combo.addItem(
                f"{task.get('description', '未命名任务')} ({task.get('task_id')[:8]})",
                task.get('task_id')
            )
        
        # 设置当前选中的任务
        linked_task_id = self.task_config.get('linked_task_id', '')
        if linked_task_id:
            index = self.task_combo.findData(linked_task_id)
            if index != -1:
                self.task_combo.setCurrentIndex(index)


class CopyThread(QThread):
    """文件复制线程类，支持任务进度保存和恢复"""
    
    # 定义信号
    progress = pyqtSignal(str)  # 复制进度信号
    finished = pyqtSignal(int, int)  # 复制完成信号，参数：成功数，失败数
    status_updated = pyqtSignal(dict)  # 状态更新信号，用于保存进度
    
    def __init__(self, source_folder, dest_folder, selected_file_filters, selected_suffix_filters, log_file_path, copy_mode="完整文件夹结构复制", task_id=None):
        """初始化复制线程
        
        Args:
            source_folder: 源文件夹路径
            dest_folder: 目标文件夹路径
            selected_file_filters: 文件名筛选条件
            selected_suffix_filters: 文件后缀筛选条件
            log_file_path: 日志文件路径
            copy_mode: 复制方式
            task_id: 任务ID，用于保存进度
        """
        super().__init__()
        self.source_folder = source_folder
        self.dest_folder = dest_folder
        self.selected_file_filters = selected_file_filters
        self.selected_suffix_filters = selected_suffix_filters
        self.log_file_path = log_file_path
        self.copy_mode = copy_mode
        self.task_id = task_id if task_id else str(uuid.uuid4())
        
        # 任务状态
        self.task_status = {
            "task_id": self.task_id,
            "source_folder": source_folder,
            "dest_folder": dest_folder,
            "copy_mode": copy_mode,
            "file_filters": selected_file_filters,
            "suffix_filters": selected_suffix_filters,
            "status": "pending",  # pending, running, paused, completed, failed
            "copied_count": 0,
            "failed_count": 0,
            "total_files": 0,
            "total_size": 0,  # 总文件大小（字节）
            "copied_size": 0,  # 已复制大小（字节）
            "current_file": "",
            "current_file_size": 0,  # 当前文件大小
            "current_file_copied": 0,  # 当前文件已复制大小
            "progress": 0.0,
            "start_time": None,
            "end_time": None,
            "speed": 0  # 当前速度（字节/秒）
        }
        
        # 速度跟踪
        self.last_update_time = None
        self.last_copied_size = 0
        
        # 已处理的文件列表
        self.processed_files = set()
        
        # 暂停标志
        self.paused = False
        self.pause_condition = QWaitCondition()
        self.mutex = QMutex()
        
        # 加载已保存的进度
        self.load_progress()
    
    def load_progress(self):
        """加载已保存的任务进度"""
        try:
            progress_file = f"task_{self.task_id}_progress.json"
            if os.path.exists(progress_file):
                with open(progress_file, "r", encoding="utf-8") as f:
                    import json
                    saved_progress = json.load(f)
                    
                # 恢复任务状态
                self.task_status.update(saved_progress.get("task_status", {}))
                
                # 恢复已处理的文件列表
                self.processed_files = set(saved_progress.get("processed_files", []))
                
                self.progress.emit(f"✓ 已恢复任务进度：{self.task_id}")
        except Exception as e:
            self.progress.emit(f"✗ 加载任务进度失败：{str(e)}")
    
    def format_size(self, size_bytes):
        """格式化文件大小显示
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            str: 格式化后的文件大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        if i == 0:
            return f"{int(size_bytes)} {size_names[i]}"
        else:
            return f"{size_bytes:.1f} {size_names[i]}"
    
    def save_progress(self):
        """保存任务进度"""
        try:
            progress_file = f"task_{self.task_id}_progress.json"
            progress_data = {
                "task_status": self.task_status,
                "processed_files": list(self.processed_files)
            }
            
            import json
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2, default=str)
            
            # 发送状态更新信号
            self.status_updated.emit(self.task_status)
        except Exception as e:
            self.progress.emit(f"✗ 保存任务进度失败：{str(e)}")
    
    def run(self):
        """执行文件复制操作，支持多种复制方式和进度保存"""
        copied_count = 0
        failed_count = 0
        
        try:
            # 更新任务状态为运行中
            self.task_status["status"] = "running"
            self.task_status["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_progress()
            
            # 查找匹配的文件并计算总大小
            matched_files = []
            total_size = 0
            for root, dirs, files in os.walk(self.source_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查文件名筛选条件
                    match_filename = False
                    if not self.selected_file_filters:
                        match_filename = True
                    else:
                        for f in self.selected_file_filters:
                            if f in file:
                                match_filename = True
                                break
                    
                    # 检查后缀名筛选条件
                    match_suffix = False
                    if not self.selected_suffix_filters:
                        match_suffix = True
                    else:
                        file_ext = os.path.splitext(file)[1].lower()
                        for s in self.selected_suffix_filters:
                            if file_ext == s.lower():
                                match_suffix = True
                                break
                    
                    if match_filename and match_suffix:
                        matched_files.append(file_path)
                        # 计算文件大小
                        try:
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                        except:
                            # 如果无法获取文件大小，跳过
                            pass
            
            # 更新总文件数和总大小
            self.task_status["total_files"] = len(matched_files)
            self.task_status["total_size"] = total_size
            self.save_progress()
            
            # 发送总大小信息
            if total_size > 0:
                size_str = self.format_size(total_size)
                self.progress.emit(f"总文件大小：{size_str}")
            
            # 初始化速度跟踪
            self.last_update_time = datetime.now()
            self.last_copied_size = 0
            
            # 根据复制方式执行不同的复制逻辑
            for i, file_path in enumerate(matched_files):
                # 检查文件是否已经处理过
                if file_path in self.processed_files:
                    continue
                    
                # 检查是否暂停
                self.mutex.lock()
                while self.paused:
                    self.task_status["status"] = "paused"
                    self.save_progress()
                    self.progress.emit(f"⏸️  任务已暂停：{self.task_id}")
                    self.pause_condition.wait(self.mutex)
                self.mutex.unlock()
                
                try:
                    # 更新当前处理的文件
                    self.task_status["current_file"] = file_path
                    self.save_progress()
                    
                    if self.copy_mode == "完整文件夹结构复制":
                        # 保留完整文件夹结构
                        relative_path = os.path.relpath(file_path, self.source_folder)
                        dest_file_path = os.path.join(self.dest_folder, relative_path)
                        # 创建目标文件夹
                        dest_dir = os.path.dirname(dest_file_path)
                        if not os.path.exists(dest_dir):
                            os.makedirs(dest_dir)
                    elif self.copy_mode == "文件内容合并复制":
                        # 合并文件到同一目录
                        dest_file_path = os.path.join(self.dest_folder, os.path.basename(file_path))
                        # 如果文件已存在，添加编号
                        if os.path.exists(dest_file_path):
                            base_name, ext = os.path.splitext(os.path.basename(file_path))
                            counter = 1
                            while os.path.exists(os.path.join(self.dest_folder, f"{base_name}_{counter}{ext}")):
                                counter += 1
                            dest_file_path = os.path.join(self.dest_folder, f"{base_name}_{counter}{ext}")
                    elif self.copy_mode == "增量差异复制":
                        # 只复制新增或修改的文件
                        relative_path = os.path.relpath(file_path, self.source_folder)
                        dest_file_path = os.path.join(self.dest_folder, relative_path)
                        # 创建目标文件夹
                        dest_dir = os.path.dirname(dest_file_path)
                        if not os.path.exists(dest_dir):
                            os.makedirs(dest_dir)
                        # 检查文件是否需要复制
                        if os.path.exists(dest_file_path):
                            # 比较文件修改时间
                            src_mtime = os.path.getmtime(file_path)
                            dst_mtime = os.path.getmtime(dest_file_path)
                            if src_mtime <= dst_mtime:
                                # 文件没有更新，跳过
                                continue
                    else:  # 覆盖式复制
                        relative_path = os.path.relpath(file_path, self.source_folder)
                        dest_file_path = os.path.join(self.dest_folder, relative_path)
                        # 创建目标文件夹
                        dest_dir = os.path.dirname(dest_file_path)
                        if not os.path.exists(dest_dir):
                            os.makedirs(dest_dir)
                    
                    # 获取当前文件大小
                    try:
                        file_size = os.path.getsize(file_path)
                        self.task_status["current_file_size"] = file_size
                        self.task_status["current_file_copied"] = 0
                    except:
                        file_size = 0
                        self.task_status["current_file_size"] = 0
                        self.task_status["current_file_copied"] = 0
                    
                    # 发送正在复制消息，更新图标
                    size_str = self.format_size(file_size) if file_size > 0 else "未知大小"
                    self.progress.emit(f"正在复制：{file_path} ({size_str})")
                    
                    # 复制文件（分块复制以便跟踪进度和速度）
                    copied_count += 1
                    with open(file_path, "rb") as src, open(dest_file_path, "wb") as dst:
                        # 分块复制，每块64KB
                        chunk_size = 64 * 1024  # 64KB
                        while True:
                            chunk = src.read(chunk_size)
                            if not chunk:
                                break
                            dst.write(chunk)
                            
                            # 更新已复制大小
                            self.task_status["current_file_copied"] += len(chunk)
                            self.task_status["copied_size"] += len(chunk)
                            
                            # 计算当前文件进度
                            if file_size > 0:
                                file_progress = (self.task_status["current_file_copied"] / file_size) * 100
                                
                                # 计算总体进度（基于文件大小）
                                if self.task_status["total_size"] > 0:
                                    total_progress = (self.task_status["copied_size"] / self.task_status["total_size"]) * 100
                                    self.task_status["progress"] = total_progress
                                    
                                    # 发送进度消息
                                    self.progress.emit(f"进度：{total_progress:.1f}%")
                            
                            # 计算速度
                            current_time = datetime.now()
                            if self.last_update_time:
                                time_diff = (current_time - self.last_update_time).total_seconds()
                                if time_diff >= 1:  # 每秒更新一次速度
                                    size_diff = self.task_status["copied_size"] - self.last_copied_size
                                    speed = size_diff / time_diff  # 字节/秒
                                    self.task_status["speed"] = speed
                                    
                                    # 更新跟踪变量
                                    self.last_update_time = current_time
                                    self.last_copied_size = self.task_status["copied_size"]
                                    
                                    # 发送速度消息
                                    speed_str = self.format_size(speed) + "/s"
                                    self.progress.emit(f"速度：{speed_str}")
                            else:
                                self.last_update_time = current_time
                                self.last_copied_size = self.task_status["copied_size"]
                    
                    self.processed_files.add(file_path)
                    self.task_status["copied_count"] = copied_count
                    self.save_progress()
                    
                    self.progress.emit(f"✓ 复制成功：{file_path} -> {dest_file_path}")
                    
                    # 记录日志
                    self.log_operation("文件复制", file_path, dest_file_path, "成功")
                    
                except PermissionError:
                    failed_count += 1
                    self.processed_files.add(file_path)
                    self.task_status["failed_count"] = failed_count
                    self.save_progress()
                    self.progress.emit(f"✗ 复制失败：{file_path} - 权限不足")
                    self.log_operation("文件复制", file_path, "", "失败：权限不足")
                except FileNotFoundError:
                    failed_count += 1
                    self.processed_files.add(file_path)
                    self.task_status["failed_count"] = failed_count
                    self.save_progress()
                    self.progress.emit(f"✗ 复制失败：{file_path} - 文件不存在")
                    self.log_operation("文件复制", file_path, "", "失败：文件不存在")
                except Exception as e:
                    failed_count += 1
                    self.processed_files.add(file_path)
                    self.task_status["failed_count"] = failed_count
                    self.save_progress()
                    error_msg = str(e)
                    self.progress.emit(f"✗ 复制失败：{file_path} - {error_msg}")
                    self.log_operation("文件复制", file_path, "", f"失败：{error_msg}")
        
        except Exception as e:
            self.task_status["status"] = "failed"
            self.task_status["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_progress()
            self.progress.emit(f"✗ 复制过程出错：{str(e)}")
            self.log_operation("批量复制", "未知源", "未知目标", f"失败：{str(e)}")
        
        finally:
            # 更新任务状态为已完成
            self.task_status["status"] = "completed"
            self.task_status["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.task_status["copied_count"] = copied_count
            self.task_status["failed_count"] = failed_count
            self.task_status["progress"] = 100.0
            self.save_progress()
            
            # 删除进度文件，任务已完成
            try:
                progress_file = f"task_{self.task_id}_progress.json"
                if os.path.exists(progress_file):
                    os.remove(progress_file)
            except Exception as e:
                self.progress.emit(f"✗ 删除进度文件失败：{str(e)}")
            
            # 发送完成信号
            self.finished.emit(copied_count, failed_count)
    
    def pause(self):
        """暂停任务"""
        self.mutex.lock()
        self.paused = True
        self.task_status["status"] = "paused"
        self.save_progress()
        self.mutex.unlock()
        
    def resume(self):
        """恢复任务"""
        self.mutex.lock()
        self.paused = False
        self.task_status["status"] = "running"
        self.save_progress()
        self.pause_condition.wakeOne()
        self.mutex.unlock()
        
    def log_operation(self, operation_type, source, destination, result):
        """记录操作日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {operation_type} - {source} -> {destination} - {result}\n"
        
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"日志写入失败：{str(e)}")


class FileOrganizerApp(QMainWindow):
    """文件整理工具主窗口类"""
    
    # 定义信号
    copy_progress = pyqtSignal(str)  # 复制进度信号
    copy_finished = pyqtSignal(int, int)  # 复制完成信号，参数：成功数，失败数
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 设置窗口基本属性
        self.setWindowTitle("文件整理工具")
        self.setMinimumSize(900, 600)
        
        # 设置应用程序图标（使用统一的图标管理器）
        self.setWindowIcon(icon_manager.get_application_icon(64))
        
        # 初始化QSettings，使用明确的文件路径来保存设置
        import os
        settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.ini")
        self.settings = QSettings(settings_file, QSettings.Format.IniFormat)
        
        # 初始化设置文件路径
        self.settings_json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        
        # 初始化变量
        self.tasks = []  # 任务列表，每个任务包含独立的配置
        self.scheduled_tasks = []  # 定时任务列表
        self.scheduled_task_history = []  # 定时任务执行历史
        self.current_task = None  # 当前执行的任务
        self.current_thread = None  # 当前执行的线程
        self.log_file_path = "file_organizer.log"
        
        # 定时任务调度器相关
        self.scheduler_timer = QTimer()  # 用于检查定时任务的定时器
        self.scheduler_interval = 60000  # 检查间隔，默认为60秒
        
        # 窗口关闭设置 - 暂时不初始化默认值，由load_settings设置
        
        # 开机自启动设置 - 暂时不初始化默认值，由load_settings设置
        
        # 初始化跨平台自启动管理器
        self.startup_manager = StartupManager("文件整理工具", sys.executable)
        
        # 加载用户配置（会设置默认值）
        self.load_settings()
        
        # 连接信号和槽
        self.copy_progress.connect(self.update_copy_progress)
        self.copy_finished.connect(self.on_copy_finished)
        
        # 初始化日志系统
        self.init_logging()
        
        # 初始化定时任务
        self.init_scheduler()
        
        # 初始化系统托盘图标
        self.init_system_tray()
        
        # 初始化UI
        self.init_ui()
        
        # 窗口居中显示
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示在屏幕上，支持多显示器，向上偏移优化视觉体验"""
        screens = QGuiApplication.screens()
        if not screens:
            return
        
        window_size = self.size()
        
        total_geometry = screens[0].geometry()
        for screen in screens[1:]:
            total_geometry = total_geometry.united(screen.geometry())
        
        center_point = total_geometry.center()
        # 向上偏移50px，优化视觉体验
        top_left = center_point - QPoint(window_size.width() // 2, window_size.height() // 2 + 50)
        
        self.move(top_left)
    
    def init_ui(self):
        """初始化用户界面，支持跨平台响应式设计"""
        # 添加现代化响应式样式表
        self.setStyleSheet("""
            /* ===== 基础样式 ===== */
            QMainWindow {
                background-color: #f1f3f5;
            }
            
            /* ===== 组框样式 ===== */
            QGroupBox {
                border: 1px solid #e9ecef;
                border-radius: 6px;
                margin-top: 12px;
                background-color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #ffffff;
                color: #343a40;
                font-weight: 600;
                font-size: 14px;
            }
            
            /* ===== 输入控件样式 ===== */
            QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px 12px;
                background-color: #ffffff;
                color: #343a40;
                min-height: 36px;
                font-size: 14px;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
                border-color: #5c7cfa;
                outline: none;
            }
            
            QLineEdit::placeholder, QComboBox::placeholder {
                color: #868e96;
            }
            
            /* ===== 按钮样式 ===== */
            QPushButton {
                background-color: #5c7cfa;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #748ffc;
            }
            
            QPushButton:pressed {
                background-color: #4c6ef5;
            }
            
            QPushButton:disabled {
                background-color: #adb5bd;
            }
            
            /* ===== 任务管理按钮样式 ===== */
            .TaskButton {
                min-height: 28px;
                min-width: 70px;
                padding: 6px 12px;
                font-size: 12px;
            }
            
            /* ===== 文本区域样式 ===== */
            QTextEdit, QListWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
                color: #343a40;
                font-size: 14px;
            }
            
            QTextEdit {
                font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", sans-serif;
            }
            
            /* ===== 标签页样式 ===== */
            QTabWidget::pane {
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #495057;
                padding: 10px 20px;
                border: 1px solid #e9ecef;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-size: 14px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #5c7cfa;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
            
            /* ===== 菜单样式 ===== */
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e9ecef;
                padding: 4px;
            }
            
            QMenuBar::item:selected {
                background-color: #5c7cfa;
                color: white;
                border-radius: 4px;
            }
            
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 4px;
            }
            
            QMenu::item {
                padding: 8px 20px 8px 20px;
                color: #343a40;
                font-size: 14px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            
            QMenu::item:selected {
                background-color: #5c7cfa;
                color: white;
            }
            
            QMenu::separator {
                height: 1px;
                background-color: #e9ecef;
                margin: 4px 8px;
            }
            
            /* ===== 工具栏样式 ===== */
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e9ecef;
                spacing: 8px;
                padding: 4px;
            }
            
            /* ===== 列表项样式 ===== */
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            
            QListWidget::item:selected {
                background-color: #5c7cfa;
                color: white;
            }
            
            QListWidget::item:hover:!selected {
                background-color: #e9ecef;
            }
            
            /* ===== 进度条样式 ===== */
            QProgressBar {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                text-align: center;
                background-color: #f8f9fa;
                min-height: 20px;
            }
            
            QProgressBar::chunk {
                background-color: #5c7cfa;
                border-radius: 3px;
            }
            
            /* ===== 状态栏样式 ===== */
            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #e9ecef;
                padding: 4px 8px;
                font-size: 12px;
                color: #868e96;
            }
            
            /* ===== 表格样式 ===== */
            QTableWidget {
                background-color: #ffffff;
                font-size: 13px;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #343a40;
                padding: 10px 12px;
                font-weight: 600;
                border: 1px solid #e9ecef;
            }
            
            QHeaderView::section:checked {
                background-color: #5c7cfa;
                color: white;
            }
            
            /* ===== 滚动条样式 ===== */
            QScrollBar:vertical {
                width: 12px;
                background-color: #f8f9fa;
            }
            
            QScrollBar::handle:vertical {
                background-color: #dee2e6;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #868e96;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* ===== 复选框样式 ===== */
            QCheckBox {
                spacing: 8px;
                color: #343a40;
                font-size: 14px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #dee2e6;
            }
            
            QCheckBox::indicator:checked {
                background-color: #5c7cfa;
                border-color: #5c7cfa;
            }
        """)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 创建中央部件和标签页
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 创建主标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        # 默认不显示关闭按钮，将在添加标签页时单独设置
        self.tab_widget.setTabsClosable(False)
        main_layout.addWidget(self.tab_widget)
        
        # 存储任务详情标签页的引用
        self.task_detail_tabs_dict = {}
        
        # 创建各个功能标签页
        self.create_file_organize_tab()
        self.create_task_detail_main_tab()  # 在文件整理和定时任务之间添加任务详情标签
        self.create_scheduler_tab()
        self.create_logs_tab()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        
        # 文件菜单
        file_menu = QMenu("文件", self)
        menu_bar.addMenu(file_menu)
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设置菜单
        settings_menu = QMenu("设置", self)
        menu_bar.addMenu(settings_menu)
        
        app_settings_action = QAction("应用程序设置", self)
        app_settings_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(app_settings_action)
        
        # 帮助菜单
        help_menu = QMenu("帮助", self)
        menu_bar.addMenu(help_menu)
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_file_organize_tab(self):
        """创建文件整理标签页，支持响应式布局"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # 任务管理区域
        task_group = QGroupBox("任务管理")
        task_layout = QVBoxLayout(task_group)
        task_layout.setSpacing(10)
        
        # 任务操作按钮区域 - 移到顶部
        task_actions_widget = QWidget()
        task_actions_layout = QHBoxLayout(task_actions_widget)
        task_actions_layout.setSpacing(12)
        
        # 添加任务按钮
        add_task_btn = QPushButton("添加任务")
        add_task_btn.setProperty("class", "TaskButton")
        add_task_btn.setFixedHeight(36)
        add_task_btn.setMinimumWidth(90)
        add_task_btn.clicked.connect(self.add_new_task)
        task_actions_layout.addWidget(add_task_btn)
        
        # 编辑任务按钮
        edit_task_btn = QPushButton("编辑任务")
        edit_task_btn.setProperty("class", "TaskButton")
        edit_task_btn.setFixedHeight(36)
        edit_task_btn.setMinimumWidth(90)
        edit_task_btn.clicked.connect(self.edit_selected_task)
        task_actions_layout.addWidget(edit_task_btn)
        
        # 删除任务按钮
        delete_task_btn = QPushButton("删除任务")
        delete_task_btn.setProperty("class", "TaskButton")
        delete_task_btn.setFixedHeight(36)
        delete_task_btn.setMinimumWidth(90)
        delete_task_btn.clicked.connect(self.delete_selected_task)
        task_actions_layout.addWidget(delete_task_btn)
        

        
        # 填充空间
        task_actions_layout.addStretch()
        
        task_layout.addWidget(task_actions_widget)
        
        # 任务列表
        self.file_task_list_widget = QListWidget()
        self.file_task_list_widget.setMinimumHeight(150)
        # 添加双击事件处理
        self.file_task_list_widget.doubleClicked.connect(self.on_task_double_clicked)
        task_layout.addWidget(self.file_task_list_widget)
        
        # 添加到主布局
        main_layout.addWidget(task_group)
        
        # 将标签页添加到主标签控件
        self.tab_widget.addTab(tab, "文件整理")
        # 文件整理标签页不需要关闭按钮
        
        # 初始化任务列表显示
        self.update_task_list_display()
    
    def create_scheduler_tab(self):
        """创建定时任务标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 使用标签页来组织定时任务和执行历史
        scheduler_tabs = QTabWidget()
        
        # ========== 定时任务管理标签 ==========
        task_management_tab = QWidget()
        task_management_layout = QVBoxLayout(task_management_tab)
        
        # 任务操作按钮区域
        task_actions_widget = QWidget()
        task_actions_layout = QHBoxLayout(task_actions_widget)
        task_actions_layout.setSpacing(10)
        
        # 添加任务按钮
        add_task_btn = QPushButton("添加定时任务")
        add_task_btn.clicked.connect(self.add_scheduled_task)
        task_actions_layout.addWidget(add_task_btn)
        
        # 编辑任务按钮
        edit_task_btn = QPushButton("编辑定时任务")
        edit_task_btn.clicked.connect(self.edit_scheduled_task)
        task_actions_layout.addWidget(edit_task_btn)
        
        # 删除任务按钮
        delete_task_btn = QPushButton("删除定时任务")
        delete_task_btn.clicked.connect(self.delete_scheduled_task)
        task_actions_layout.addWidget(delete_task_btn)
        
        # 启用/禁用任务按钮
        toggle_task_btn = QPushButton("启用/禁用")
        toggle_task_btn.clicked.connect(self.toggle_scheduled_task)
        task_actions_layout.addWidget(toggle_task_btn)
        
        # 填充空间
        task_actions_layout.addStretch()
        
        task_management_layout.addWidget(task_actions_widget)
        
        # 定时任务列表
        list_group = QGroupBox("定时任务列表")
        list_layout = QVBoxLayout(list_group)
        
        self.scheduled_task_list = QListWidget()
        self.scheduled_task_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # 设置列表项大小
        self.scheduled_task_list.setMinimumHeight(200)
        
        # 双击打开任务详情
        self.scheduled_task_list.doubleClicked.connect(self.on_scheduled_task_double_clicked)
        
        list_layout.addWidget(self.scheduled_task_list)
        task_management_layout.addWidget(list_group)
        
        # ========== 执行历史标签 ==========
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        # 执行历史表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["历史ID", "任务名称", "执行时间", "状态", "结果"])
        
        # 设置表格属性
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 设置列宽
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        history_layout.addWidget(self.history_table)
        
        # ========== 添加标签页 ==========
        scheduler_tabs.addTab(task_management_tab, "定时任务管理")
        scheduler_tabs.addTab(history_tab, "执行历史记录")
        
        # 添加到主布局
        layout.addWidget(scheduler_tabs)
        
        # 更新定时任务列表
        self.update_scheduler_tab()
        
        # 将定时任务标签页添加到主标签控件
        self.tab_widget.addTab(tab, "定时任务")
        # 定时任务标签页不需要关闭按钮
    
    def create_task_detail_main_tab(self):
        """创建任务详情主标签页（在文件整理和定时任务之间）"""
        # 创建一个包含标签页控件的容器，支持多个任务详情
        self.task_detail_container = QWidget()
        layout = QVBoxLayout(self.task_detail_container)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)
        

        
        # 创建任务详情标签页控件
        self.task_detail_tabs = QTabWidget()
        self.task_detail_tabs.setTabsClosable(True)
        self.task_detail_tabs.tabCloseRequested.connect(self.close_task_detail_tab)
        

        
        layout.addWidget(self.task_detail_tabs)
        

        
        # 将任务详情标签页添加到主标签控件
        self.tab_widget.addTab(self.task_detail_container, "任务详情")
        # 任务详情标签页不需要关闭按钮
    

    
    def create_logs_tab(self):
        """创建日志标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 日志设置
        log_settings_group = QGroupBox("日志设置")
        log_settings_layout = QFormLayout(log_settings_group)
        
        # 日志文件路径设置
        log_path_layout = QHBoxLayout()
        self.log_path_line_edit = QLineEdit()
        self.log_path_line_edit.setText(self.log_file_path)
        log_path_layout.addWidget(self.log_path_line_edit)
        
        browse_log_path_btn = QPushButton("浏览")
        browse_log_path_btn.clicked.connect(self.browse_log_path)
        log_path_layout.addWidget(browse_log_path_btn)
        
        save_log_path_btn = QPushButton("保存设置")
        save_log_path_btn.clicked.connect(self.save_log_settings)
        log_path_layout.addWidget(save_log_path_btn)
        
        log_settings_layout.addRow("日志文件路径:", log_path_layout)
        
        layout.addWidget(log_settings_group)
        
        # 日志查看
        log_group = QGroupBox("日志查看")
        log_layout = QVBoxLayout(log_group)
        
        # 日志内容
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_layout.addWidget(self.log_text_edit)
        
        layout.addWidget(log_group)
        
        # 日志操作
        log_action_layout = QHBoxLayout()
        
        refresh_log_btn = QPushButton("刷新日志")
        refresh_log_btn.clicked.connect(self.refresh_logs)
        
        view_older_btn = QPushButton("向后查看")
        view_older_btn.clicked.connect(self.view_older_logs)
        
        export_log_btn = QPushButton("导出日志")
        export_log_btn.clicked.connect(self.export_logs)
        
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_logs)
        
        log_action_layout.addWidget(refresh_log_btn)
        log_action_layout.addWidget(view_older_btn)
        log_action_layout.addWidget(export_log_btn)
        log_action_layout.addWidget(clear_log_btn)        
        layout.addLayout(log_action_layout)
        
        self.tab_widget.addTab(tab, "日志")
        # 日志标签页不需要关闭按钮
        
        # 初始刷新日志
        self.refresh_logs()
    
    def on_task_type_changed(self):
        """任务类型改变时的处理"""
        task_type = self.task_type_combo.currentText()
        self.period_widget.setVisible(task_type == "周期性定时")
    
    def init_logging(self):
        """初始化日志系统"""
        # 默认日志文件路径
        self.log_file_path = os.path.join(os.getcwd(), "file_organizer.log")
        
        # 创建日志文件（如果不存在）
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, "w", encoding="utf-8") as f:
                f.write("# 文件整理工具日志\n")
    
    def init_scheduler(self):
        """初始化定时任务调度器"""
        self.scheduled_tasks = []  # 定时任务列表
        self.scheduled_task_history = []  # 定时任务执行历史
        self.timer = QTimer()  # 用于检查定时任务的定时器
        self.scheduler_interval = 60000  # 检查间隔，默认为60秒
        
        # 连接定时器信号到槽函数
        self.timer.timeout.connect(self.check_scheduled_tasks)
        # 启动定时器，每60秒检查一次
        self.timer.start(self.scheduler_interval)
        
        # 加载定时任务配置
        self.load_scheduled_tasks()
    
    def check_scheduled_tasks(self):
        """检查并执行到期的定时任务"""
        now = datetime.now()
        
        for task in self.scheduled_tasks:
            if not task.get("enabled", False):
                continue
            
            next_execution = task.get("next_execution")
            if next_execution and next_execution <= now:
                # 执行定时任务
                self.execute_scheduled_task(task)
    
    def execute_scheduled_task(self, scheduled_task):
        """执行定时任务
        
        Args:
            scheduled_task: 定时任务配置
        """
        # 查找关联的文件复制任务
        task_id = scheduled_task.get("linked_task_id")
        file_task = None
        
        if not task_id:
            # 关联的文件复制任务ID未设置
            error_msg = f"定时任务 {scheduled_task.get('name')} 执行失败：关联的文件复制任务ID未设置"
            self.log_message(error_msg)
            self.show_tray_notification("定时任务执行失败", error_msg, QSystemTrayIcon.MessageIcon.Critical)
            return
        
        for task in self.tasks:
            if task.get("task_id") == task_id:
                file_task = task
                break
        
        if not file_task:
            # 关联的文件复制任务不存在
            error_msg = f"定时任务 {scheduled_task.get('name')} 执行失败：关联的文件复制任务不存在"
            self.log_message(error_msg)
            self.show_tray_notification("定时任务执行失败", error_msg, QSystemTrayIcon.MessageIcon.Critical)
            return
        
        # 显示任务开始通知
        task_name = scheduled_task.get("name", "未命名任务")
        self.show_tray_notification("定时任务执行开始", f"{task_name} 已开始执行")
        
        # 更新定时任务状态
        scheduled_task["last_executed"] = datetime.now()
        scheduled_task["status"] = "running"
        
        # 记录执行历史
        history_record = {
            "history_id": str(uuid.uuid4()),
            "task_id": scheduled_task.get("task_id"),
            "task_name": task_name,
            "execution_time": datetime.now(),
            "status": "running",
            "result": ""
        }
        self.scheduled_task_history.append(history_record)
        
        # 执行文件复制任务（静默执行，不显示确认对话框）
        self.is_scheduled_task = True  # 设置定时任务标志
        try:
            self.run_task(file_task)
        finally:
            self.is_scheduled_task = False  # 清除标志
        
        # 更新执行历史记录
        for record in self.scheduled_task_history:
            if record.get("history_id") == history_record.get("history_id"):
                record["status"] = "success"
                record["result"] = "执行完成"
                break
        
        # 更新定时任务下次执行时间
        self.update_next_execution(scheduled_task)
        
        # 保存定时任务配置
        self.save_scheduled_tasks()
        
        # 更新UI显示
        self.update_scheduler_tab()
        
        # 显示任务完成通知
        self.show_tray_notification("定时任务执行完成", f"{task_name} 已执行完成")
    
    def update_next_execution(self, scheduled_task):
        """更新定时任务的下次执行时间
        
        Args:
            scheduled_task: 定时任务配置
        """
        trigger_type = scheduled_task.get("trigger_type")
        trigger_time = scheduled_task.get("trigger_time")
        repeat_interval = scheduled_task.get("repeat_interval", 1)
        weekdays = scheduled_task.get("weekdays", [])
        month_day = scheduled_task.get("month_day", 1)
        
        now = datetime.now()
        next_time = None
        
        if trigger_type == "once":
            # 一次性任务，执行后不再执行
            next_time = None
        elif trigger_type == "daily":
            # 每日任务，按间隔天数执行
            next_time = now + timedelta(days=repeat_interval)
            next_time = next_time.replace(
                hour=trigger_time.hour,
                minute=trigger_time.minute,
                second=trigger_time.second,
                microsecond=0
            )
        elif trigger_type == "weekly":
            # 每周任务，按间隔周数执行
            if not weekdays:
                weekdays = [0]  # 默认周一
            
            # 计算下一个指定的工作日
            days_ahead = None
            current_weekday = now.weekday()
            
            for day in sorted(weekdays):
                if day > current_weekday:
                    days_ahead = day - current_weekday
                    break
            
            if days_ahead is None:
                days_ahead = (7 - current_weekday) + sorted(weekdays)[0]
            
            # 加上间隔周数
            days_ahead += (repeat_interval - 1) * 7
            next_time = now + timedelta(days=days_ahead)
            next_time = next_time.replace(
                hour=trigger_time.hour,
                minute=trigger_time.minute,
                second=trigger_time.second,
                microsecond=0
            )
        elif trigger_type == "monthly":
            # 每月任务，按间隔月数执行
            # 简化处理，假设每个月都有31天
            months_to_add = repeat_interval
            year = now.year
            month = now.month + months_to_add
            
            # 处理月份溢出
            while month > 12:
                month -= 12
                year += 1
            
            # 处理每月天数
            # 简化处理，确保日期有效
            try:
                next_time = datetime(year, month, month_day, 
                                   trigger_time.hour, trigger_time.minute, trigger_time.second)
            except ValueError:
                # 如果日期无效，使用当月最后一天
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                next_time = datetime(year, month, last_day, 
                                   trigger_time.hour, trigger_time.minute, trigger_time.second)
        
        scheduled_task["next_execution"] = next_time
    
    def add_scheduled_task(self):
        """添加定时任务"""
        dialog = ScheduledTaskConfigDialog(self)
        dialog.load_tasks(self.tasks)
        
        if dialog.exec():
            task_config = dialog.get_task_config()
            self.scheduled_tasks.append(task_config)
            self.save_scheduled_tasks()
            self.update_scheduler_tab()
    
    def on_scheduled_task_double_clicked(self, index):
        """双击定时任务显示任务详情（标签页形式）
        
        Args:
            index: 双击的任务索引
        """
        # 获取选中的定时任务
        item = self.scheduled_task_list.item(index.row())
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        # 查找对应的定时任务
        scheduled_task = None
        for task in self.scheduled_tasks:
            if task.get("task_id") == task_id:
                scheduled_task = task
                break
        
        if not scheduled_task:
            return
        
        # 获取关联的文件复制任务
        linked_task_id = scheduled_task.get("linked_task_id")
        if not linked_task_id:
            QMessageBox.warning(self, "警告", "该定时任务没有关联的文件复制任务")
            return
        
        # 查找对应的文件复制任务
        file_task = None
        for task in self.tasks:
            if task.get("task_id") == linked_task_id:
                file_task = task
                break
        
        if not file_task:
            QMessageBox.warning(self, "警告", "关联的文件复制任务不存在")
            return
        
        # 在主任务详情标签页中显示任务详情
        self.show_task_detail_in_main_tab(file_task)
    
    def edit_scheduled_task(self):
        """编辑选中的定时任务"""
        selected_items = self.scheduled_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要编辑的定时任务")
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        # 查找对应的定时任务
        for task in self.scheduled_tasks:
            if task.get("task_id") == task_id:
                dialog = ScheduledTaskConfigDialog(self, task)
                dialog.load_tasks(self.tasks)
                
                if dialog.exec():
                    updated_task = dialog.get_task_config()
                    # 更新任务
                    for i, t in enumerate(self.scheduled_tasks):
                        if t.get("task_id") == task_id:
                            self.scheduled_tasks[i] = updated_task
                            break
                    
                    self.save_scheduled_tasks()
                    self.update_scheduler_tab()
                break
    
    def delete_scheduled_task(self):
        """删除选中的定时任务"""
        selected_items = self.scheduled_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要删除的定时任务")
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "确认", "确定要删除选中的定时任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除定时任务
            self.scheduled_tasks = [task for task in self.scheduled_tasks 
                                  if task.get("task_id") != task_id]
            
            self.save_scheduled_tasks()
            self.update_scheduler_tab()
    
    def toggle_scheduled_task(self):
        """启用/禁用选中的定时任务"""
        selected_items = self.scheduled_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要启用/禁用的定时任务")
            return
        
        item = selected_items[0]
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        # 查找对应的定时任务
        for task in self.scheduled_tasks:
            if task.get("task_id") == task_id:
                task["enabled"] = not task.get("enabled", False)
                break
        
        self.save_scheduled_tasks()
        self.update_scheduler_tab()
    
    def save_scheduled_tasks(self):
        """保存定时任务配置"""
        try:
            import json
            scheduled_tasks_file = "scheduled_tasks.json"
            
            # 转换datetime对象为字符串，以便JSON序列化
            def datetime_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"类型 {type(obj)} 不能被序列化")
            
            with open(scheduled_tasks_file, "w", encoding="utf-8") as f:
                json.dump(self.scheduled_tasks, f, ensure_ascii=False, indent=2, 
                         default=datetime_serializer)
        except Exception as e:
            self.log_message(f"保存定时任务配置失败：{str(e)}")
    
    def load_scheduled_tasks(self):
        """加载定时任务配置"""
        try:
            import json
            scheduled_tasks_file = "scheduled_tasks.json"
            
            if os.path.exists(scheduled_tasks_file):
                with open(scheduled_tasks_file, "r", encoding="utf-8") as f:
                    scheduled_tasks = json.load(f)
                    
                    # 转换字符串为datetime对象
                    for task in scheduled_tasks:
                        if task.get("trigger_time"):
                            task["trigger_time"] = datetime.fromisoformat(task.get("trigger_time"))
                        if task.get("next_execution"):
                            task["next_execution"] = datetime.fromisoformat(task.get("next_execution"))
                        if task.get("last_executed"):
                            task["last_executed"] = datetime.fromisoformat(task.get("last_executed"))
                    
                    self.scheduled_tasks = scheduled_tasks
        except Exception as e:
            self.log_message(f"加载定时任务配置失败：{str(e)}")
            self.scheduled_tasks = []
    
    def init_system_tray(self):
        """初始化系统托盘图标 - 跨平台兼容版本"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用统一的图标管理器设置托盘图标
        self.tray_icon.setIcon(icon_manager.get_tray_icon("normal"))
        
        self.tray_icon.setToolTip("文件整理工具 - 准备就绪")
        
        self.tray_menu = QMenu()
        
        show_window_action = QAction("📂 显示窗口", self)
        show_window_action.triggered.connect(self.show_window)
        self.tray_menu.addAction(show_window_action)
        
        self.status_action = QAction("📊 任务状态", self)
        self.status_action.triggered.connect(self.show_task_status)
        self.tray_menu.addAction(self.status_action)
        
        self.tray_menu.addSeparator()
        
        self.toggle_scheduler_action = QAction("⏸️ 暂停定时任务", self)
        self.toggle_scheduler_action.triggered.connect(self.toggle_scheduler)
        self.tray_menu.addAction(self.toggle_scheduler_action)
        
        self.tray_menu.addSeparator()
        
        exit_action = QAction("❌ 退出程序", self)
        exit_action.triggered.connect(self.quit_application)
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        self.tray_icon.show()
        
        self.is_scheduler_paused = False
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_tray_icon)
        self.animation_frame = 0
        
        self.window().hideEvent = self.on_hide_window
    
    def create_tray_icon(self, state="normal"):
        """创建自定义托盘图标
        
        Args:
            state: 图标状态 - "normal"(正常), "running"(运行中), "warning"(警告), "error"(错误)
            
        Returns:
            QIcon: 自定义图标
        """
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        color_map = {
            "normal": QColor(92, 124, 250),
            "running": QColor(81, 207, 102),
            "warning": QColor(252, 196, 25),
            "error": QColor(255, 107, 107)
        }
        
        primary_color = color_map.get(state, color_map["normal"])
        secondary_color = primary_color.darker(130)
        
        if state == "running" and self.animation_frame % 2 == 0:
            primary_color = primary_color.lighter(120)
        
        center_x, center_y = 16, 16
        radius = 12
        
        gradient = QRadialGradient(center_x - 3, center_y - 3, radius)
        gradient.setColorAt(0, primary_color.lighter(130))
        gradient.setColorAt(1, primary_color)
        
        painter.setBrush(gradient)
        painter.setPen(QPen(secondary_color, 1))
        painter.drawEllipse(center_x - radius + 1, center_y - radius + 1, radius * 2 - 2, radius * 2 - 2)
        
        icon_path = [
            QPointF(center_x - 4, center_y - 2),
            QPointF(center_x - 1, center_y - 5),
            QPointF(center_x + 5, center_y - 9),
            QPointF(center_x + 8, center_y - 6),
            QPointF(center_x + 4, center_y - 2),
            QPointF(center_x + 1, center_y - 1)
        ]
        
        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawPolyline(icon_path)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def animate_tray_icon(self):
        """托盘图标动画效果"""
        self.animation_frame += 1
        
        if self.animation_frame >= 8:
            self.animation_frame = 0
        
        # 使用统一的图标管理器设置运行状态图标
        self.tray_icon.setIcon(icon_manager.get_tray_icon("running"))
        
        if self.animation_frame == 7:
            self.animation_timer.stop()
            # 使用统一的图标管理器设置正常状态图标
            self.tray_icon.setIcon(icon_manager.get_tray_icon("normal"))
            self.update_tray_tooltip()
    
    def start_tray_animation(self):
        """开始托盘图标动画"""
        self.animation_frame = 0
        self.animation_timer.start(500)
    
    def update_tray_tooltip(self):
        """更新托盘图标提示信息"""
        task_count = len(self.tasks)
        scheduled_count = len([t for t in self.scheduled_tasks if t.get("enabled", False)])
        
        if task_count == 0:
            tooltip = "文件整理工具 - 暂无任务"
        elif scheduled_count > 0:
            tooltip = f"文件整理工具 - {task_count}个任务，{scheduled_count}个定时任务已启用"
        else:
            tooltip = f"文件整理工具 - {task_count}个任务"
        
        if self.is_scheduler_paused:
            tooltip += " (定时任务已暂停)"
        
        self.tray_icon.setToolTip(tooltip)
    
    def show_task_status(self):
        """显示任务状态对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("任务状态")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(TaskConfigDialog.DIALOG_STYLE_SHEET)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(dialog)
        
        task_count = len(self.tasks)
        enabled_count = len([t for t in self.scheduled_tasks if t.get("enabled", False)])
        running_count = len([t for t in self.scheduled_tasks if t.get("status") == "running"])
        
        status_text = QLabel(f"""<h3>📊 当前状态</h3>
        <p><b>文件复制任务：</b>{task_count}个</p>
        <p><b>定时任务：</b>{enabled_count}个已启用，{running_count}个运行中</p>
        <p><b>定时任务状态：</b>{'已暂停' if self.is_scheduler_paused else '运行中'}</p>""")
        status_text.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(status_text)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 窗口居中显示
        self._center_dialog_on_screen(dialog)
        
        dialog.exec()
    
    def _center_dialog_on_screen(self, dialog):
        """将对话框居中显示在屏幕上"""
        screens = QGuiApplication.screens()
        if not screens:
            return
        
        dialog_size = dialog.size()
        screen = screens[0]
        screen_geometry = screen.geometry()
        
        center_point = screen_geometry.center()
        top_left = center_point - QPoint(dialog_size.width() // 2, dialog_size.height() // 2)
        
        dialog.move(top_left)
    
    def toggle_scheduler(self):
        """暂停/恢复定时任务调度器"""
        self.is_scheduler_paused = not self.is_scheduler_paused
        
        if self.is_scheduler_paused:
            self.timer.stop()
            self.toggle_scheduler_action.setText("▶️ 恢复定时任务")
            self.show_tray_notification("定时任务已暂停", "系统将不会自动执行定时任务", QSystemTrayIcon.MessageIcon.Warning)
        else:
            self.timer.start(60000)
            self.toggle_scheduler_action.setText("⏸️ 暂停定时任务")
            self.show_tray_notification("定时任务已恢复", "系统将自动执行到期的定时任务")
        
        self.update_tray_tooltip()
    
    def on_hide_window(self, event):
        """窗口隐藏事件处理"""
        if self.isMinimized():
            # 最小化时隐藏窗口，只显示系统托盘图标
            self.hide()
            # 显示托盘通知
            self.show_tray_notification("文件整理工具已最小化", "程序已在后台运行，点击托盘图标可恢复窗口")
            event.ignore()
        else:
            # 正常隐藏，不处理
            event.accept()
    
    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件处理
        
        Args:
            reason: 激活原因（点击、双击等）
        """
        # 点击托盘图标时切换窗口显示/隐藏状态
        # 使用兼容的PyQt6枚举值访问方式
        trigger_reason = getattr(QSystemTrayIcon.ActivationReason, 'Trigger', None)
        if trigger_reason is not None and reason == trigger_reason:
            if self.isVisible():
                # 如果窗口可见，则最小化到系统托盘
                self.showMinimized()
                self.hide()
            else:
                # 如果窗口隐藏，则显示并激活窗口
                self.show()
                self.showNormal()
                self.raise_()
                self.activateWindow()
    
    def show_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_application(self):
        """退出应用程序"""
        # 隐藏托盘图标
        self.tray_icon.hide()
        # 退出应用
        QApplication.quit()
    
    def show_tray_notification(self, title, message, icon_type=QSystemTrayIcon.MessageIcon.Information):
        """显示系统托盘通知
        
        Args:
            title: 通知标题
            message: 通知内容
            icon_type: 通知图标类型
        """
        self.tray_icon.showMessage(title, message, icon_type, 5000)  # 5秒后自动消失
    
    def update_scheduler_tab(self):
        """更新定时任务标签页显示"""
        # 检查定时任务列表控件是否存在
        if hasattr(self, "scheduled_task_list"):
            self.scheduled_task_list.clear()
            
            for task in self.scheduled_tasks:
                status = "已启用" if task.get("enabled", False) else "已禁用"
                trigger_type_map = {
                    "once": "一次性",
                    "daily": "每日",
                    "weekly": "每周",
                    "monthly": "每月"
                }
                trigger_type = trigger_type_map.get(task.get("trigger_type", "once"))
                
                next_execution = task.get("next_execution")
                next_execution_str = next_execution.strftime("%Y-%m-%d %H:%M:%S") if next_execution else "无"
                
                item_text = f"{task.get('name', '未命名任务')} | {trigger_type} | {status} | 下次执行：{next_execution_str}"
                item = QListWidgetItem(item_text)
                
                # 设置任务ID以便后续关联
                item.setData(Qt.ItemDataRole.UserRole, task.get("task_id"))
                
                # 设置状态颜色
                if task.get("enabled", False):
                    item.setForeground(QColor(40, 167, 69))  # 绿色
                else:
                    item.setForeground(QColor(108, 117, 125))  # 灰色
                
                self.scheduled_task_list.addItem(item)
        
        # 检查执行历史表格是否存在
        if hasattr(self, "history_table"):
            self.update_history_table()
    
    def update_history_table(self):
        """更新执行历史表格"""
        self.history_table.setRowCount(0)
        
        for i, record in enumerate(self.scheduled_task_history):
            self.history_table.insertRow(i)
            
            # 历史ID
            self.history_table.setItem(i, 0, QTableWidgetItem(record.get("history_id", "")))
            
            # 任务名称
            self.history_table.setItem(i, 1, QTableWidgetItem(record.get("task_name", "")))
            
            # 执行时间
            exec_time = record.get("execution_time")
            if isinstance(exec_time, datetime):
                exec_time_str = exec_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                exec_time_str = str(exec_time)
            self.history_table.setItem(i, 2, QTableWidgetItem(exec_time_str))
            
            # 状态
            status = record.get("status", "")
            status_item = QTableWidgetItem(status)
            if status == "success":
                status_item.setForeground(QColor(40, 167, 69))  # 绿色
            elif status == "failed":
                status_item.setForeground(QColor(220, 53, 69))  # 红色
            else:
                status_item.setForeground(QColor(255, 193, 7))  # 黄色
            self.history_table.setItem(i, 3, status_item)
            
            # 结果
            self.history_table.setItem(i, 4, QTableWidgetItem(record.get("result", "")))
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 写入日志文件
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败：{str(e)}")
        
        # 更新日志标签页
        if hasattr(self, "log_text_edit"):
            self.log_text_edit.append(log_entry)
    
    def update_task_list_display(self):
        """更新任务列表显示 - 修复重复显示问题，并添加状态显示"""
        # 清空列表（关键修复：确保先清空再添加）
        self.file_task_list_widget.clear()
        
        # 只添加实际存在的任务
        for i, task in enumerate(self.tasks):
            desc = task.get("description", f"任务 {i+1}")
            source = os.path.basename(task.get("source_folder", "")) if task.get("source_folder") else "未设置"
            dest = os.path.basename(task.get("dest_folder", "")) if task.get("dest_folder") else "未设置"
            copy_mode = task.get("copy_mode", "完整文件夹结构复制")
            status = task.get("status", "未完成")  # 获取任务状态
            
            # 构建任务显示文本，包含状态
            if status == "已完成":
                item_text = f"{desc} | {copy_mode} | 源: {source} | 目标: {dest} | ✅ {status}"
            else:
                item_text = f"{desc} | {copy_mode} | 源: {source} | 目标: {dest} | ❌ {status}"
            
            item = QListWidgetItem(item_text)
            
            # 设置状态样式
            if status == "已完成":
                item.setForeground(QColor(40, 167, 69))  # 绿色
            else:
                item.setForeground(QColor(220, 53, 69))  # 红色
            
            # 存储任务ID以便后续关联
            item.setData(Qt.ItemDataRole.UserRole, task.get("task_id"))
            self.file_task_list_widget.addItem(item)
    
    def add_new_task(self):
        """添加新任务 - 修复重复添加问题"""
        dialog = TaskConfigDialog(self)
        if dialog.exec():
            task_config = dialog.get_task_config()
            # 确保任务ID唯一
            if not task_config.get("task_id"):
                task_config["task_id"] = str(uuid.uuid4())
            
            # 设置初始状态为未完成
            task_config["status"] = "未完成"
            
            # 只添加一次（关键修复）
            self.tasks.append(task_config)
            
            # 只更新一次列表
            self.update_task_list_display()
            
            # 保存配置
            self.save_settings()
            
            self.statusBar.showMessage(f"已添加新任务：{task_config.get('description', '未命名任务')}")
    
    def edit_selected_task(self):
        """编辑选中的任务"""
        selected_items = self.file_task_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要编辑的任务")
            return
        
        index = self.file_task_list_widget.row(selected_items[0])
        if 0 <= index < len(self.tasks):
            dialog = TaskConfigDialog(self, self.tasks[index])
            if dialog.exec():
                task_config = dialog.get_task_config()
                # 保留原有状态
                task_config["status"] = self.tasks[index].get("status", "未完成")
                self.tasks[index] = task_config
                self.update_task_list_display()
                self.save_settings()
    
    def delete_selected_task(self):
        """删除选中的任务"""
        selected_items = self.file_task_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要删除的任务")
            return
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除选中的 {len(selected_items)} 个任务吗？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 获取选中任务的索引
        selected_indices = [self.file_task_list_widget.row(item) for item in selected_items]
        # 按降序删除
        for index in sorted(selected_indices, reverse=True):
            if 0 <= index < len(self.tasks):
                del self.tasks[index]
        
        self.update_task_list_display()
        self.save_settings()
        self.statusBar.showMessage(f"已删除 {len(selected_items)} 个任务")
    
    def run_selected_task(self):
        """运行选中的任务 - 修复无法执行问题"""
        selected_items = self.file_task_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要运行的任务")
            return
        
        index = self.file_task_list_widget.row(selected_items[0])
        if 0 <= index < len(self.tasks):
            task = self.tasks[index]
            self.run_task(task)
    
    def run_task(self, task):
        """运行指定的任务 - 完全重构执行逻辑"""
        try:
            # 获取任务配置
            source_folder = task.get("source_folder", "")
            dest_folder = task.get("dest_folder", "")
            copy_mode = task.get("copy_mode", "完整文件夹结构复制")
            file_filters = task.get("file_filters", [])
            suffix_filters = task.get("suffix_filters", [])
            task_id = task.get("task_id", str(uuid.uuid4()))
            
            # 验证配置
            if not source_folder:
                QMessageBox.warning(self, "警告", "任务配置中缺少源文件夹信息")
                return
            
            if not dest_folder:
                QMessageBox.warning(self, "警告", "任务配置中缺少目标文件夹信息")
                return
            
            # 验证文件夹存在性
            if not os.path.exists(source_folder):
                # 对于定时任务，静默记录错误而不显示对话框
                if hasattr(self, 'is_scheduled_task') and self.is_scheduled_task:
                    error_msg = f"源文件夹不存在：{source_folder}"
                    self.log_message(f"定时任务执行失败：{error_msg}")
                    return
                else:
                    QMessageBox.warning(self, "警告", f"源文件夹不存在：{source_folder}")
                    return
            
            if not os.path.exists(dest_folder):
                # 对于定时任务，自动创建目标文件夹而不询问
                if hasattr(self, 'is_scheduled_task') and self.is_scheduled_task:
                    try:
                        os.makedirs(dest_folder)
                        self.log_message(f"自动创建目标文件夹：{dest_folder}")
                    except Exception as e:
                        error_msg = f"创建目标文件夹失败：{str(e)}"
                        self.log_message(f"定时任务执行失败：{error_msg}")
                        return
                else:
                    reply = QMessageBox.question(self, "确认", "目标文件夹不存在，是否创建？",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        try:
                            os.makedirs(dest_folder)
                        except Exception as e:
                            QMessageBox.critical(self, "错误", f"创建目标文件夹失败：{str(e)}")
                            return
                    else:
                        return
            
            # 检查权限
            if not os.access(source_folder, os.R_OK):
                # 对于定时任务，静默记录错误而不显示对话框
                if hasattr(self, 'is_scheduled_task') and self.is_scheduled_task:
                    error_msg = f"没有读取源文件夹的权限：{source_folder}"
                    self.log_message(f"定时任务执行失败：{error_msg}")
                    return
                else:
                    QMessageBox.warning(self, "警告", f"没有读取源文件夹的权限：{source_folder}")
                    return
            
            if not os.access(dest_folder, os.W_OK):
                # 对于定时任务，静默记录错误而不显示对话框
                if hasattr(self, 'is_scheduled_task') and self.is_scheduled_task:
                    error_msg = f"没有写入目标文件夹的权限：{dest_folder}"
                    self.log_message(f"定时任务执行失败：{error_msg}")
                    return
                else:
                    QMessageBox.warning(self, "警告", f"没有写入目标文件夹的权限：{dest_folder}")
                    return
            
            # 确认执行（定时任务静默执行，不显示确认对话框）
            if not (hasattr(self, 'is_scheduled_task') and self.is_scheduled_task):
                reply = QMessageBox.question(self, "确认执行", 
                                           f"确定要执行任务 '{task.get('description', '未命名任务')}' 吗？\n"
                                           f"源文件夹：{source_folder}\n"
                                           f"目标文件夹：{dest_folder}\n"
                                           f"复制方式：{copy_mode}",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # 停止当前正在执行的任务（如果有）
            if self.current_thread and self.current_thread.isRunning():
                self.current_thread.terminate()
                self.current_thread.wait()
            
            # 清空结果显示（已删除）
            
            # 更新按钮状态（按钮已删除，无需更新）
            
            # 创建并启动复制线程
            self.current_thread = CopyThread(
                source_folder=source_folder,
                dest_folder=dest_folder,
                selected_file_filters=file_filters,
                selected_suffix_filters=suffix_filters,
                log_file_path=self.log_file_path,
                copy_mode=copy_mode,
                task_id=task_id
            )
            
            # 连接信号
            self.current_thread.progress.connect(self.update_copy_progress)
            self.current_thread.finished.connect(lambda copied, failed, t=task: self.on_copy_finished(copied, failed, t))
            
            # 启动线程
            self.current_thread.start()
            
            # 记录当前任务
            self.current_task = task
            
            # 显示开始信息（已删除）
            
            self.statusBar.showMessage(f"正在执行任务：{task.get('description', '未命名任务')}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"任务执行过程中发生错误：{str(e)}")
            self.log_operation("任务执行", "未知源", "未知目标", f"失败：{str(e)}")
            # 恢复按钮状态（按钮已删除，无需更新）
    
    def pause_selected_task(self):
        """暂停选中的任务"""
        if self.current_thread and self.current_thread.isRunning() and not self.current_thread.paused:
            self.current_thread.pause()
            # 按钮状态更新（按钮已删除，无需更新）
            self.statusBar.showMessage("任务已暂停")
            # 任务暂停信息（已删除）
    
    def resume_selected_task(self):
        """恢复选中的任务"""
        if self.current_thread and self.current_thread.isRunning() and self.current_thread.paused:
            self.current_thread.resume()
            # 按钮状态更新（按钮已删除，无需更新）
            self.statusBar.showMessage("任务已恢复")
            # 任务恢复信息（已删除）
    
    def stop_selected_task(self):
        """停止当前任务"""
        if self.current_thread and self.current_thread.isRunning():
            reply = QMessageBox.question(self, "确认停止", 
                                       "确定要停止当前任务吗？已复制的文件将保留，未完成的将中断。",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                # 终止线程
                self.current_thread.terminate()
                self.current_thread.wait()
                
                # 清理
                self.current_thread = None
                self.current_task = None
                
                # 更新按钮状态（按钮已删除，无需更新）
                
                # 任务停止信息（已删除）
                self.statusBar.showMessage("任务已停止")
    
    def update_copy_progress(self, message):
        """更新复制进度（进度条和文本区域已删除）"""
        # 进度显示功能已删除
    
    def on_copy_finished(self, copied_count, failed_count, task=None):
        """复制完成后的处理 - 添加任务状态更新"""
        # 显示复制结果统计（进度条和文本区域已删除）
        
        # 更新状态栏
        self.statusBar.showMessage(f"任务完成：成功 {copied_count} 个，失败 {failed_count} 个")
        
        # 更新任务状态为已完成
        if task:
            # 找到任务并更新状态
            for i, t in enumerate(self.tasks):
                if t.get("task_id") == task.get("task_id"):
                    self.tasks[i]["status"] = "已完成"
                    break
            
            # 记录日志
            self.log_operation(
                "批量复制", 
                task.get("source_folder", ""), 
                task.get("dest_folder", ""), 
                f"完成 - 成功 {copied_count} 个，失败 {failed_count} 个"
            )
            
            # 更新任务列表显示
            self.update_task_list_display()
            # 保存配置
            self.save_settings()
        
        # 恢复按钮状态（按钮已删除，无需更新）
        
        # 清理当前任务
        self.current_thread = None
        self.current_task = None
        
        # 刷新日志
        self.refresh_logs()
    
    def log_operation(self, operation_type, source, destination, result):
        """记录操作日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {operation_type} - {source} -> {destination} - {result}\n"
        
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"日志写入失败：{str(e)}")
    
    def on_task_double_clicked(self, index):
        """双击任务显示详细结果和进度条（在任务详情标签页中显示）
        
        Args:
            index: 双击的任务索引
        """
        # 获取选中的任务
        item = self.file_task_list_widget.item(index.row())
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        # 查找对应的任务
        task = None
        for t in self.tasks:
            if t.get("task_id") == task_id:
                task = t
                break
        
        if not task:
            return
        
        # 在任务详情标签页中显示任务详情
        self.show_task_detail_in_main_tab(task)
    

    
    def show_task_detail_in_main_tab(self, task):
        """在任务详情标签页中以标签页形式显示任务详情，支持多个任务同时打开
        
        Args:
            task: 任务配置
        """
        # 切换到任务详情标签页
        task_detail_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "任务详情":
                task_detail_index = i
                break
        
        if task_detail_index >= 0:
            self.tab_widget.setCurrentIndex(task_detail_index)
        
        # 检查是否已经打开了该任务的详情标签页
        task_id = task.get("task_id")
        existing_tab_index = self.find_task_detail_tab(task_id)
        if existing_tab_index >= 0:
            # 如果已经打开，切换到该标签页
            self.task_detail_tabs.setCurrentIndex(existing_tab_index)
            return
        
        # 创建新的任务详情标签页
        self.create_task_detail_tab(task)
    
    def find_task_detail_tab(self, task_id):
        """查找任务详情标签页的索引
        
        Args:
            task_id: 任务ID
            
        Returns:
            int: 标签页索引，如果未找到返回-1
        """
        for i in range(self.task_detail_tabs.count()):
            scroll_area = self.task_detail_tabs.widget(i)
            if scroll_area and scroll_area.widget():
                content_widget = scroll_area.widget()
                if hasattr(content_widget, 'task_id') and content_widget.task_id == task_id:
                    return i
        return -1
    
    def create_task_detail_tab(self, task):
        """创建任务详情标签页，支持滚动条
        
        Args:
            task: 任务配置
        """
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(8, 8, 8, 8)
        
        # 任务标题
        title_label = QLabel(f"任务详情 - {task.get('description', '未命名任务')}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: #343a40;")
        content_layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)
        
        # 任务信息区域
        info_group = QGroupBox("任务信息")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(10)
        
        # 添加任务信息
        info_layout.addWidget(QLabel("任务ID:"), 0, 0)
        task_id_label = QLabel(task.get("task_id", "未设置"))
        task_id_label.setStyleSheet("font-family: 'Courier New', monospace; color: #6c757d;")
        info_layout.addWidget(task_id_label, 0, 1)
        
        info_layout.addWidget(QLabel("任务描述:"), 1, 0)
        info_layout.addWidget(QLabel(task.get("description", "未命名任务")), 1, 1)
        
        info_layout.addWidget(QLabel("源文件夹:"), 2, 0)
        info_layout.addWidget(QLabel(task.get("source_folder", "未设置")), 2, 1)
        
        info_layout.addWidget(QLabel("目标文件夹:"), 3, 0)
        info_layout.addWidget(QLabel(task.get("dest_folder", "未设置")), 3, 1)
        
        info_layout.addWidget(QLabel("复制方式:"), 4, 0)
        info_layout.addWidget(QLabel(task.get("copy_mode", "完整文件夹结构复制")), 4, 1)
        
        info_layout.addWidget(QLabel("任务状态:"), 5, 0)
        status_label = QLabel(task.get("status", "未完成"))
        if task.get("status") == "已完成":
            status_label.setStyleSheet("color: #28a745;")
        else:
            status_label.setStyleSheet("color: #dc3545;")
        info_layout.addWidget(status_label, 5, 1)
        
        content_layout.addWidget(info_group)
        
        # 详细进度区域
        progress_group = QGroupBox("详细进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 当前文件信息
        current_file_layout = QHBoxLayout()
        current_file_layout.addWidget(QLabel("当前文件:"))
        current_file_label = QLabel("等待开始...")
        current_file_layout.addWidget(current_file_label)
        current_file_layout.addStretch()
        
        # 文件图标
        file_icon_label = QLabel()
        file_icon_label.setFixedSize(55, 55)
        self.update_file_icon(file_icon_label, "ready")
        current_file_layout.addWidget(file_icon_label)
        progress_layout.addLayout(current_file_layout)
        
        # 速度显示
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("速度:"))
        speed_label = QLabel("等待开始...")
        speed_layout.addWidget(speed_label)
        speed_layout.addStretch()
        progress_layout.addLayout(speed_layout)
        
        # 进度条
        detail_progress_bar = QProgressBar()
        detail_progress_bar.setRange(0, 100)
        detail_progress_bar.setValue(0)
        progress_layout.addWidget(detail_progress_bar)
        
        content_layout.addWidget(progress_group)
        
        # 操作结果区域
        result_group = QGroupBox("操作结果")
        result_layout = QVBoxLayout(result_group)
        
        detail_result_text = QTextEdit()
        detail_result_text.setReadOnly(True)
        detail_result_text.setMinimumHeight(150)
        result_layout.addWidget(detail_result_text)
        
        content_layout.addWidget(result_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 执行任务按钮
        execute_btn = QPushButton("执行任务")
        execute_btn.clicked.connect(lambda: self.execute_task_with_detail(task, content_widget, detail_progress_bar, detail_result_text, current_file_label, speed_label, file_icon_label))
        button_layout.addWidget(execute_btn)
        
        # 暂停任务按钮
        pause_btn = QPushButton("暂停任务")
        pause_btn.setEnabled(False)  # 初始状态为禁用
        pause_btn.clicked.connect(lambda: self.pause_task_detail(content_widget, pause_btn))
        button_layout.addWidget(pause_btn)
        
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(lambda: self.close_current_task_detail_tab(content_widget))
        button_layout.addWidget(close_btn)
        
        content_layout.addLayout(button_layout)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        
        # 存储UI组件引用到标签页
        content_widget.task_id = task.get("task_id")
        content_widget.detail_progress_bar = detail_progress_bar
        content_widget.detail_result_text = detail_result_text
        content_widget.current_file_label = current_file_label
        content_widget.speed_label = speed_label
        content_widget.file_icon_label = file_icon_label
        content_widget.pause_btn = pause_btn
        content_widget.execute_btn = execute_btn
        
        # 添加标签页
        tab_index = self.task_detail_tabs.addTab(scroll_area, task.get("description", "未命名任务"))
        self.task_detail_tabs.setCurrentIndex(tab_index)
        
        # 占位符已删除，无需隐藏
        self.task_detail_container.execute_btn = execute_btn
        self.task_detail_container.task_id = task.get("task_id")
    

    
    def pause_task_detail(self, content_widget, pause_btn):
        """暂停任务详情中的任务执行
        
        Args:
            content_widget: 任务详情内容组件
            pause_btn: 暂停按钮
        """
        if hasattr(content_widget, 'detail_thread') and content_widget.detail_thread:
            thread = content_widget.detail_thread
            if thread.isRunning():
                if thread.paused:
                    # 恢复任务
                    thread.resume()
                    pause_btn.setText("暂停任务")
                    self.statusBar.showMessage("任务已恢复")
                else:
                    # 暂停任务
                    thread.pause()
                    pause_btn.setText("恢复任务")
                    self.statusBar.showMessage("任务已暂停")
    
    def close_current_task_detail_tab(self, content_widget):
        """关闭当前任务详情标签页
        
        Args:
            content_widget: 任务详情内容组件
        """
        # 查找包含该内容组件的标签页索引
        for i in range(self.task_detail_tabs.count()):
            scroll_area = self.task_detail_tabs.widget(i)
            if scroll_area and scroll_area.widget() == content_widget:
                self.close_task_detail_tab(i)
                break
    
    def close_task_detail_tab(self, index):
        """关闭任务详情标签页
        
        Args:
            index: 标签页索引
        """
        # 获取标签页组件（现在是QScrollArea）
        scroll_area = self.task_detail_tabs.widget(index)
        
        # 获取内容组件（包含任务详情）
        if scroll_area and scroll_area.widget():
            content_widget = scroll_area.widget()
            
            # 检查是否有正在运行的线程，如果有则直接停止
            if hasattr(content_widget, 'detail_thread') and content_widget.detail_thread:
                thread = content_widget.detail_thread
                if thread.isRunning():
                    # 直接停止线程，不显示确认对话框
                    thread.terminate()
                    thread.wait()
        
        # 移除标签页
        self.task_detail_tabs.removeTab(index)
        
        # 占位符已删除，无需显示
    
    def close_main_tab(self, index):
        """关闭主标签页
        
        Args:
            index: 标签页索引
        """
        # 获取标签页文本
        tab_text = self.tab_widget.tabText(index)
        
        # 如果是任务详情标签页，检查是否有正在运行的任务
        if tab_text == "任务详情" and hasattr(self.task_detail_container, 'detail_thread'):
            thread = self.task_detail_container.detail_thread
            if thread and thread.isRunning():
                # 询问用户是否停止任务
                reply = QMessageBox.question(self, "确认关闭", 
                                           "任务仍在运行，确定要关闭标签页吗？\n\n关闭标签页将停止当前任务。",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    # 停止线程
                    thread.terminate()
                    thread.wait()
                else:
                    return  # 用户取消关闭
        
        # 移除标签页
        self.tab_widget.removeTab(index)
        
        # 如果是任务详情标签页，重新创建空的容器
        if tab_text == "任务详情":
            self.create_task_detail_main_tab()
    
    def execute_task_with_detail(self, task, dialog, progress_bar, result_text, current_file_label, speed_label, file_icon_label):
        """在任务详情对话框中执行任务并更新进度显示
        
        Args:
            task: 要执行的任务
            dialog: 任务详情对话框
            progress_bar: 进度条组件
            result_text: 结果文本组件
            current_file_label: 当前文件标签
            speed_label: 速度标签
            file_icon_label: 文件图标标签
        """
        try:
            # 获取任务配置
            source_folder = task.get("source_folder", "")
            dest_folder = task.get("dest_folder", "")
            copy_mode = task.get("copy_mode", "完整文件夹结构复制")
            file_filters = task.get("file_filters", [])
            suffix_filters = task.get("suffix_filters", [])
            task_id = task.get("task_id", str(uuid.uuid4()))
            
            # 验证配置
            if not source_folder:
                QMessageBox.warning(dialog, "警告", "任务配置中缺少源文件夹信息")
                return
            
            if not dest_folder:
                QMessageBox.warning(dialog, "警告", "任务配置中缺少目标文件夹信息")
                return
            
            # 验证文件夹存在性
            if not os.path.exists(source_folder):
                QMessageBox.warning(dialog, "警告", f"源文件夹不存在：{source_folder}")
                return
            
            if not os.path.exists(dest_folder):
                reply = QMessageBox.question(dialog, "确认", "目标文件夹不存在，是否创建？",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        os.makedirs(dest_folder)
                    except Exception as e:
                        QMessageBox.critical(dialog, "错误", f"创建目标文件夹失败：{str(e)}")
                        return
                else:
                    return
            
            # 检查权限
            if not os.access(source_folder, os.R_OK):
                QMessageBox.warning(dialog, "警告", f"没有读取源文件夹的权限：{source_folder}")
                return
            
            if not os.access(dest_folder, os.W_OK):
                QMessageBox.warning(dialog, "警告", f"没有写入目标文件夹的权限：{dest_folder}")
                return
            
            # 清空结果显示
            result_text.clear()
            progress_bar.setValue(0)
            current_file_label.setText("准备就绪")
            speed_label.setText("速度: 0 B/s")
            
            # 启用暂停按钮
            if hasattr(dialog, 'pause_btn'):
                dialog.pause_btn.setEnabled(True)
                dialog.pause_btn.setText("暂停任务")
            
            # 禁用执行按钮
            if hasattr(dialog, 'execute_btn'):
                dialog.execute_btn.setEnabled(False)
            
            # 显示开始信息
            result_text.append(f"开始执行任务：{task.get('description', '未命名任务')}")
            result_text.append(f"源文件夹：{source_folder}")
            result_text.append(f"目标文件夹：{dest_folder}")
            result_text.append(f"复制方式：{copy_mode}")
            result_text.append("-" * 50)
            
            # 创建并启动复制线程
            thread = CopyThread(
                source_folder=source_folder,
                dest_folder=dest_folder,
                selected_file_filters=file_filters,
                selected_suffix_filters=suffix_filters,
                log_file_path=self.log_file_path,
                copy_mode=copy_mode,
                task_id=task_id
            )
            
            # 将线程保存到对话框属性中，以便在对话框关闭时正确处理
            setattr(dialog, 'detail_thread', thread)
            
            # 连接进度更新信号
            thread.progress.connect(lambda msg: self.update_detail_progress(msg, result_text, progress_bar, current_file_label, speed_label, file_icon_label))
            thread.finished.connect(lambda copied, failed: self.on_detail_task_finished(copied, failed, task, result_text, progress_bar))
            
            # 启动线程
            thread.start()
            
        except Exception as e:
            QMessageBox.critical(dialog, "错误", f"任务执行过程中发生错误：{str(e)}")
            self.log_operation("任务执行", "未知源", "未知目标", f"失败：{str(e)}")
    
    def update_file_icon(self, icon_label, state, file_path=None):
        """更新文件图标状态
        
        Args:
            icon_label: 图标标签组件
            state: 图标状态 ("ready", "copying", "success", "error")
            file_path: 文件路径，用于显示具体文件图标
        """
        # 如果是复制中状态且有文件路径，显示具体文件图标
        if state == "copying" and file_path and os.path.exists(file_path):
            try:
                # 使用更简单的方法获取文件图标 - 根据文件扩展名显示对应图标
                ext = os.path.splitext(file_path)[1].lower()
                
                # 常见文件类型的图标映射
                icon_colors = {
                    '.txt': QColor(92, 124, 250),    # 蓝色 - 文本文件
                    '.doc': QColor(41, 128, 185),    # 深蓝色 - Word文档
                    '.docx': QColor(41, 128, 185),   # 深蓝色 - Word文档
                    '.pdf': QColor(231, 76, 60),     # 红色 - PDF文件
                    '.jpg': QColor(155, 89, 182),    # 紫色 - 图片文件
                    '.jpeg': QColor(155, 89, 182),   # 紫色 - 图片文件
                    '.png': QColor(155, 89, 182),    # 紫色 - 图片文件
                    '.gif': QColor(155, 89, 182),    # 紫色 - 图片文件
                    '.mp3': QColor(243, 156, 18),    # 橙色 - 音频文件
                    '.mp4': QColor(243, 156, 18),    # 橙色 - 视频文件
                    '.avi': QColor(243, 156, 18),    # 橙色 - 视频文件
                    '.zip': QColor(230, 126, 34),    # 深橙色 - 压缩文件
                    '.rar': QColor(230, 126, 34),    # 深橙色 - 压缩文件
                    '.exe': QColor(39, 174, 96),     # 绿色 - 可执行文件
                }
                
                # 获取对应的颜色，如果没有匹配则使用灰色（未知文件）
                color = icon_colors.get(ext, QColor(128, 128, 128))  # 未知文件 - 灰色
                
                # 创建文件图标（增大到55x55像素）
                pixmap = QPixmap(55, 55)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # 使用文件类型对应的颜色
                painter.setPen(QPen(color, 3))
                painter.setBrush(QBrush(color, Qt.BrushStyle.SolidPattern))
                
                # 绘制文件图标（调整尺寸以适应55x55）
                painter.drawRect(10, 20, 35, 28)  # 文件主体
                painter.drawRect(15, 10, 30, 10)   # 文件标签
                
                # 添加文件扩展名文本（增大字体）
                if ext:
                    painter.setPen(QPen(QColor(255, 255, 255), 2))
                    painter.setFont(QFont("Arial", 10))
                    # 显示扩展名（去掉点号，只显示前3个字符）
                    ext_text = ext[1:4] if len(ext) > 1 else ext[1:]
                    painter.drawText(10, 20, 35, 28, Qt.AlignmentFlag.AlignCenter, ext_text.upper())
                
                painter.end()
                icon_label.setPixmap(pixmap)
                return
                
            except Exception as e:
                # 如果获取图标失败，使用默认图标
                print(f"获取文件图标失败: {e}")
                pass
        
        # 创建默认图标（增大到55x55像素）
        pixmap = QPixmap(55, 55)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 根据状态设置颜色
        if state == "ready":
            # 准备状态 - 蓝色
            color = QColor(92, 124, 250)  # 蓝色
        elif state == "copying":
            # 复制中状态 - 橙色
            color = QColor(255, 165, 0)   # 橙色
        elif state == "success":
            # 成功状态 - 绿色
            color = QColor(40, 167, 69)   # 绿色
        elif state == "error":
            # 错误状态 - 红色
            color = QColor(220, 53, 69)   # 红色
        else:
            color = QColor(92, 124, 250)  # 默认蓝色
        
        painter.setPen(QPen(color, 3))
        painter.setBrush(QBrush(color, Qt.BrushStyle.SolidPattern))
        
        # 绘制文件图标（调整尺寸以适应55x55）
        painter.drawRect(10, 20, 35, 28)  # 文件主体
        painter.drawRect(15, 10, 30, 10)   # 文件标签
        
        # 根据状态添加额外效果（调整位置以适应55x55）
        if state == "copying":
            # 复制中状态 - 添加动画效果（箭头）
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(25, 15, 40, 15)
            painter.drawLine(35, 10, 40, 15)
            painter.drawLine(35, 20, 40, 15)
        elif state == "success":
            # 成功状态 - 添加勾号
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(15, 30, 25, 40)
            painter.drawLine(25, 40, 40, 25)
        elif state == "error":
            # 错误状态 - 添加叉号
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(15, 15, 40, 40)
            painter.drawLine(40, 15, 15, 40)
        
        painter.end()
        icon_label.setPixmap(pixmap)
    
    def update_detail_progress(self, message, result_text, progress_bar, current_file_label, speed_label, file_icon_label=None):
        """更新任务详情对话框中的进度显示
        
        Args:
            message: 进度消息
            result_text: 结果文本组件
            progress_bar: 进度条组件
            current_file_label: 当前文件标签
            speed_label: 速度标签
            file_icon_label: 文件图标标签（可选）
        """
        # 解析消息，更新文件信息和速度
        import re
        
        # 过滤掉进度和速度相关的消息，只显示重要的操作结果
        if not ("进度：" in message or "速度：" in message or "总文件大小：" in message):
            # 添加重要消息到结果文本
            result_text.append(message)
        
        # 简化的图标更新逻辑 - 确保图标能够正确更新
        if file_icon_label:
            # 任务开始时设置图标为准备状态
            if "开始执行任务" in message:
                self.update_file_icon(file_icon_label, "ready")
            
            # 检测到文件操作消息时，智能更新图标状态
            elif any(keyword in message for keyword in ["正在复制", "复制", "文件", "进度"]):
                # 优先处理正在复制消息
                if "正在复制" in message:
                    file_match = re.search(r"正在复制：([^\s]+)", message)
                    if file_match:
                        file_path = file_match.group(1)
                        current_file_label.setText(os.path.basename(file_path))
                        self.update_file_icon(file_icon_label, "copying", file_path)
                
                # 其他文件操作消息，只在没有当前文件时更新为复制中状态
                elif not current_file_label.text() or current_file_label.text() == "":
                    file_match = re.search(r"([A-Za-z]:\\[^\s]+\.\w+|[^\s]+\.\w+)", message)
                    if file_match:
                        file_path = file_match.group(1)
                        if os.path.exists(file_path):
                            current_file_label.setText(os.path.basename(file_path))
                            self.update_file_icon(file_icon_label, "copying", file_path)
            
            # 任务完成时设置图标为成功状态（只在全部复制完成时）
            elif "复制完成" in message or "任务完成" in message:
                self.update_file_icon(file_icon_label, "success")
            
            # 复制失败消息只在任务完成时处理
            elif "✗ 复制失败" in message and ("复制完成" in message or "任务完成" in message):
                self.update_file_icon(file_icon_label, "error")
        
        # 更新进度条（基于实际文件操作）
        if "进度" in message:
            progress_match = re.search(r"进度：(\d+(?:\.\d+)?)%", message)
            if progress_match:
                progress_value = float(progress_match.group(1))
                progress_bar.setValue(int(progress_value))
        
        # 更新速度显示
        if "速度：" in message:
            speed_match = re.search(r"速度：(.+?)/s", message)
            if speed_match:
                speed_label.setText(f"速度: {speed_match.group(1)}/s")
        
        # 更新当前文件信息
        if "正在复制：" in message:
            # 提取文件名和大小信息
            file_match = re.search(r"正在复制：([^()]+)\((.*?)\)", message)
            if file_match:
                file_path = file_match.group(1).strip()
                file_size = file_match.group(2)
                current_file_label.setText(f"{os.path.basename(file_path)} ({file_size})")
                
                # 更新文件图标为复制中状态
                if file_icon_label:
                    self.update_file_icon(file_icon_label, "copying", file_path)
        
        # 自动滚动到底部
        cursor = result_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        result_text.setTextCursor(cursor)
    
    def on_detail_task_finished(self, copied_count, failed_count, task, result_text, progress_bar):
        """任务详情对话框中任务完成后的处理
        
        Args:
            copied_count: 成功复制数量
            failed_count: 失败数量
            task: 任务对象
            result_text: 结果文本组件
            progress_bar: 进度条组件
        """
        # 显示复制结果统计
        result_text.append("-" * 50)
        result_text.append(f"\n✅ 复制完成：成功 {copied_count} 个，失败 {failed_count} 个")
        
        # 更新进度条为100%
        progress_bar.setValue(100)
        
        # 更新任务状态为已完成
        for i, t in enumerate(self.tasks):
            if t.get("task_id") == task.get("task_id"):
                self.tasks[i]["status"] = "已完成"
                break
        
        # 重置按钮状态
        # 查找对应的任务详情标签页
        for i in range(self.task_detail_tabs.count()):
            scroll_area = self.task_detail_tabs.widget(i)
            if scroll_area and scroll_area.widget():
                content_widget = scroll_area.widget()
                if hasattr(content_widget, 'task_id') and content_widget.task_id == task.get("task_id"):
                    # 禁用暂停按钮
                    if hasattr(content_widget, 'pause_btn'):
                        content_widget.pause_btn.setEnabled(False)
                    # 启用执行按钮
                    if hasattr(content_widget, 'execute_btn'):
                        content_widget.execute_btn.setEnabled(True)
                    break
        
        # 记录日志
        self.log_operation(
            "批量复制", 
            task.get("source_folder", ""), 
            task.get("dest_folder", ""), 
            f"完成 - 成功 {copied_count} 个，失败 {failed_count} 个"
        )
        
        # 更新任务列表显示
        self.update_task_list_display()
        # 保存配置
        self.save_settings()
    
    def refresh_logs(self):
        """刷新日志显示 - 只显示最新内容并提供向后查看功能"""
        if not os.path.exists(self.log_file_path):
            self.log_text_edit.setText("日志文件不存在")
            return
        
        try:
            # 尝试多种编码方式读取日志文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
            content = ""
            
            for encoding in encodings:
                try:
                    with open(self.log_file_path, "r", encoding=encoding) as f:
                        lines = f.readlines()
                    # 如果成功读取且内容不为空，则使用该编码
                    if lines:
                        # 只显示最新的100行内容
                        if len(lines) > 100:
                            content = "".join(lines[-100:])
                            # 添加提示信息
                            content = f"[显示最新100行，共{len(lines)}行，点击'向后查看'按钮查看更多历史记录]\n\n{content}"
                        else:
                            content = "".join(lines)
                        break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"使用编码 {encoding} 读取日志文件失败：{str(e)}")
                    continue
            
            # 如果所有编码都失败，尝试二进制读取并解码
            if not content.strip():
                try:
                    with open(self.log_file_path, "rb") as f:
                        raw_content = f.read()
                    # 尝试自动检测编码
                    import chardet
                    detected = chardet.detect(raw_content)
                    encoding = detected.get('encoding', 'utf-8')
                    raw_text = raw_content.decode(encoding, errors='replace')
                    lines = raw_text.split('\n')
                    if lines:
                        # 只显示最新的100行内容
                        if len(lines) > 100:
                            content = "\n".join(lines[-100:])
                            # 添加提示信息
                            content = f"[显示最新100行，共{len(lines)}行，点击'向后查看'按钮查看更多历史记录]\n\n{content}"
                        else:
                            content = raw_text
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"无法读取日志文件：{str(e)}")
                    return
            
            self.log_text_edit.setText(content)
            
            # 滚动到最后一行
            cursor = self.log_text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text_edit.setTextCursor(cursor)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取日志文件失败：{str(e)}")
    
    def view_older_logs(self):
        """查看更早的日志记录"""
        if not os.path.exists(self.log_file_path):
            QMessageBox.information(self, "提示", "日志文件不存在")
            return
        
        try:
            # 读取完整的日志文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
            content = ""
            
            for encoding in encodings:
                try:
                    with open(self.log_file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    if content.strip():
                        break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"使用编码 {encoding} 读取日志文件失败：{str(e)}")
                    continue
            
            # 如果所有编码都失败，尝试二进制读取并解码
            if not content.strip():
                try:
                    with open(self.log_file_path, "rb") as f:
                        raw_content = f.read()
                    import chardet
                    detected = chardet.detect(raw_content)
                    encoding = detected.get('encoding', 'utf-8')
                    content = raw_content.decode(encoding, errors='replace')
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"无法读取日志文件：{str(e)}")
                    return
            
            # 显示完整的日志内容
            self.log_text_edit.setText(content)
            
            # 滚动到顶部
            cursor = self.log_text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.log_text_edit.setTextCursor(cursor)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取日志文件失败：{str(e)}")
    
    def export_logs(self):
        """导出日志"""
        if not os.path.exists(self.log_file_path):
            QMessageBox.warning(self, "警告", "日志文件不存在")
            return
        
        export_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "file_organizer_logs.txt", "文本文件 (*.txt);;所有文件 (*.*)")
        
        if export_path:
            try:
                shutil.copy2(self.log_file_path, export_path)
                QMessageBox.information(self, "成功", "日志导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"日志导出失败：{str(e)}")
    
    def clear_logs(self):
        """清空日志"""
        reply = QMessageBox.question(self, "确认", "确定要清空日志吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.log_file_path, "w", encoding="utf-8") as f:
                    f.write("# 文件整理工具日志\n")
                self.refresh_logs()
                QMessageBox.information(self, "成功", "日志已清空")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空日志失败：{str(e)}")
    
    def browse_log_path(self):
        """浏览日志文件路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择日志文件路径", self.log_file_path, "日志文件 (*.log);;所有文件 (*.*)")
        if file_path:
            self.log_path_line_edit.setText(file_path)
    
    def save_log_settings(self):
        """保存日志设置"""
        new_log_path = self.log_path_line_edit.text().strip()
        if not new_log_path:
            QMessageBox.warning(self, "警告", "日志文件路径不能为空")
            return
        
        try:
            # 检查路径是否可写
            with open(new_log_path, "a", encoding="utf-8") as f:
                pass
            
            # 保存新的日志路径
            self.log_file_path = new_log_path
            
            # 创建日志文件（如果不存在）
            if not os.path.exists(self.log_file_path):
                with open(self.log_file_path, "w", encoding="utf-8") as f:
                    f.write("# 文件整理工具日志\n")
            
            QMessageBox.information(self, "成功", "日志设置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存日志设置失败：{str(e)}")
    
    def show_settings_dialog(self):
        """显示应用程序设置对话框"""
        # 创建设置对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("应用程序设置")
        dialog.setFixedSize(400, 400)
        dialog.setStyleSheet(TaskConfigDialog.DIALOG_STYLE_SHEET)
        
        # 设置对话框图标，与主窗口图标保持一致
        dialog.setWindowIcon(self.create_tray_icon("normal"))
        
        # 创建布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建设置组
        settings_group = QGroupBox("窗口设置")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(15)
        
        # 添加自动隐藏到托盘选项
        minimize_to_tray_check = QCheckBox(
            "关闭窗口时自动隐藏到系统托盘区域"
        )
        minimize_to_tray_check.setChecked(self.minimize_to_tray)
        settings_layout.addWidget(minimize_to_tray_check)
        
        # 添加开机自启动选项
        startup_check = QCheckBox(
            "开机自启动并隐藏到系统托盘"
        )
        startup_check.setChecked(self.startup)
        settings_layout.addWidget(startup_check)
        
        # 添加自启动类型选择
        startup_type_layout = QHBoxLayout()
        startup_type_label = QLabel("自启动时机：")
        startup_type_label.setStyleSheet("color: #343a40; font-size: 14px;")
        startup_type_layout.addWidget(startup_type_label)
        
        startup_type_combo = QComboBox()
        startup_type_combo.addItem("用户登录后启动", "user")
        startup_type_combo.addItem("系统启动后启动", "system")
        
        # 设置当前选择
        current_index = startup_type_combo.findData(self.startup_type)
        if current_index >= 0:
            startup_type_combo.setCurrentIndex(current_index)
        
        startup_type_combo.setEnabled(self.startup)
        startup_type_layout.addWidget(startup_type_combo)
        startup_type_layout.addStretch()
        settings_layout.addLayout(startup_type_layout)
        
        # 添加平台信息
        platform_info = QLabel(f"当前平台：{platform.system()} - {self.startup_manager.platform}")
        platform_info.setStyleSheet("color: #868e96; font-size: 12px; font-style: italic;")
        settings_layout.addWidget(platform_info)
        
        # 添加状态信息
        status_info = QLabel("")
        status_info.setStyleSheet("color: #5c7cfa; font-size: 12px;")
        settings_layout.addWidget(status_info)
        
        # 添加提示标签
        hint_label = QLabel(
            "提示：启用此选项后，关闭窗口时应用程序不会退出，而是最小化到系统托盘；启用开机自启动后，应用程序将在系统启动后自动运行并隐藏到系统托盘。"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #868e96; font-size: 12px;")
        settings_layout.addWidget(hint_label)
        
        main_layout.addWidget(settings_group)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)
        
        # 添加确定按钮
        ok_button = QPushButton("确定")
        ok_button.setMinimumWidth(100)
        # 直接在lambda中保存两个设置
        ok_button.clicked.connect(lambda: self.save_app_settings(
            minimize_to_tray_check.isChecked(),
            startup_check.isChecked(),
            startup_type_combo.currentData()
        ))
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        # 添加取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # 显示对话框
        # 计算并设置对话框居中位置
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            dialog_geometry = dialog.frameGeometry()
            center_point = screen_geometry.center()
            dialog_geometry.moveCenter(center_point)
            dialog.move(dialog_geometry.topLeft())
        dialog.exec()
    
    def on_startup_toggled(self, checked):
        """自启动选项切换回调"""
        # 注意：startup_type_combo是局部变量，不需要在这里访问
        pass
    
    def update_startup_status(self):
        """更新自启动状态显示"""
        # 注意：startup_type_combo是局部变量，不需要在这里访问
        pass
    
    def save_app_settings(self, minimize_to_tray, startup, startup_type):
        """保存应用程序设置"""
        self.minimize_to_tray = minimize_to_tray
        self.startup = startup
        self.startup_type = startup_type
        self.save_settings()
    

    
    def show_about(self):
        """显示关于对话框"""
        # 创建自定义关于对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("关于文件整理工具")
        
        # 设置窗口尺寸与主窗口完全重叠
        main_window_size = self.size()
        dialog.setFixedSize(main_window_size)
        dialog.setStyleSheet(TaskConfigDialog.DIALOG_STYLE_SHEET)
        
        # 设置窗口图标，使用统一的图标管理器
        dialog.setWindowIcon(icon_manager.get_dialog_icon(32))
        
        # 调整窗口位置，使其与主窗口完全重叠
        main_window_pos = self.pos()
        dialog.move(main_window_pos)
        
        # 确保窗口在不同DPI缩放下正确显示
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        
        # 添加DPI适配逻辑，确保在不同缩放比例下正确显示
        screen = QApplication.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            # 根据DPI调整窗口大小和位置
            if dpi > 96:  # 高DPI屏幕
                scale_factor = dpi / 96.0
                # 确保窗口位置不会超出屏幕边界
                screen_geometry = screen.availableGeometry()
                if main_window_pos.x() + dialog.width() * scale_factor > screen_geometry.width():
                    main_window_pos.setX(max(0, screen_geometry.width() - dialog.width() * scale_factor))
                if main_window_pos.y() + dialog.height() * scale_factor > screen_geometry.height():
                    main_window_pos.setY(max(0, screen_geometry.height() - dialog.height() * scale_factor))
                dialog.move(main_window_pos)
        
        # 创建布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(20, 30, 20, 30)
        main_layout.setSpacing(30)
        
        # 添加弹性空间以更好地利用增加的窗口高度
        main_layout.addStretch(1)
        
        # 添加应用程序图标 - 使用统一的图标管理器
        icon_label = QLabel()
        # 使用应用程序图标，尺寸为96x96像素
        app_icon = icon_manager.get_application_icon(96)
        pixmap = app_icon.pixmap(96, 96)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(icon_label)
        
        # 在图标和标题之间添加弹性空间
        main_layout.addStretch(1)
        
        # 添加应用程序名称和版本
        name_label = QLabel("文件整理工具 v2.0")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #5c7cfa; margin-bottom: 10px;")
        main_layout.addWidget(name_label)
        
        # 添加作者信息
        author_label = QLabel("作者：wwq")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_label.setStyleSheet("color: #868e96; font-size: 16px; margin-bottom: 20px;")
        main_layout.addWidget(author_label)
        
        # 在标题和功能列表之间添加弹性空间
        main_layout.addStretch(1)
        
        # 添加功能列表 - 带滚动条
        features_scroll_area = QScrollArea()
        # 根据窗口高度动态设置滚动区域高度
        scroll_area_height = max(150, min(300, int(main_window_size.height() * 0.4)))
        features_scroll_area.setMinimumHeight(scroll_area_height)
        features_scroll_area.setMaximumHeight(int(main_window_size.height() * 0.5))
        features_scroll_area.setWidgetResizable(True)
        features_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        features_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        features_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 8px;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #868e96;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        features_label = QLabel(
            "功能特性：\n" 
            "• 智能文件整理与任务管理\n" 
            "• 完整的操作日志系统\n" 
            "• 系统托盘自动隐藏功能\n"
            "• 开机自启动支持\n"
            "• 定时任务调度管理\n"
            "• 多线程文件处理\n"
            "• 实时进度监控（基于文件大小）\n"
            "• 自定义文件过滤规则\n"
            "• 批量操作支持\n"
            "• 错误处理与重试机制\n"
            "• 用户配置持久化\n"
            "\n"
            "支持的复制方式：\n"
            "• 完整文件夹结构复制 - 保留源文件夹完整结构\n"
            "• 文件内容合并复制 - 合并所有文件到同一目录\n"
            "• 增量差异复制 - 只复制新增或修改的文件\n"
            "• 覆盖式复制 - 覆盖目标文件夹中的同名文件"
        )
        features_label.setWordWrap(True)
        features_label.setStyleSheet("color: #343a40; font-size: 16px; background-color: #f8f9fa; padding: 15px; border-radius: 8px;")
        features_scroll_area.setWidget(features_label)
        main_layout.addWidget(features_scroll_area)
        
        # 在功能列表和更新说明之间添加弹性空间
        main_layout.addStretch(1)
        
        # 添加更新说明 - 带滚动条
        updates_scroll_area = QScrollArea()
        # 根据窗口高度动态设置滚动区域高度
        updates_scroll_height = max(120, min(250, int(main_window_size.height() * 0.35)))
        updates_scroll_area.setMinimumHeight(updates_scroll_height)
        updates_scroll_area.setMaximumHeight(int(main_window_size.height() * 0.45))
        updates_scroll_area.setWidgetResizable(True)
        updates_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        updates_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        updates_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 8px;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #868e96;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        updates_label = QLabel(
            "最新更新：\n"
            "• 优化任务管理界面布局\n"
            "• 增强窗口位置管理功能\n"
            "• 改进系统托盘图标显示\n"
            "• 添加DPI自适应支持\n"
            "• 优化多显示器兼容性\n"
            "• 修复系统托盘激活错误\n"
            "• 改进关于窗口高度适配\n"
            "• 添加独立滚动条支持\n"
            "• 优化视觉样式和布局\n"
            "• 增强用户体验和交互性"
        )
        updates_label.setWordWrap(True)
        updates_label.setStyleSheet("color: #868e96; font-size: 14px; background-color: #f1f3f5; padding: 12px; border-radius: 6px;")
        updates_scroll_area.setWidget(updates_label)
        main_layout.addWidget(updates_scroll_area)
        
        # 在更新说明和按钮之间添加弹性空间
        main_layout.addStretch(2)
        
        # 添加关闭按钮
        close_button = QPushButton("关闭")
        close_button.setMinimumWidth(120)
        close_button.setMinimumHeight(40)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #5c7cfa;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #4c6ef5;
            }
            QPushButton:pressed {
                background-color: #3b5bdb;
            }
        """)
        close_button.clicked.connect(dialog.accept)
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec()
    
    def load_settings(self):
        """加载用户配置"""
        try:
            import json
            import os
            
            # 检查JSON设置文件是否存在
            if os.path.exists(self.settings_json_file):
                # 从JSON文件加载设置
                with open(self.settings_json_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                
                # 加载任务列表
                if "tasks" in settings:
                    self.tasks = settings["tasks"]
                else:
                    self.tasks = []
                
                # 加载日志文件路径
                self.log_file_path = settings.get("log_file_path", "file_organizer.log")
                
                # 加载窗口关闭设置
                self.minimize_to_tray = settings.get("minimize_to_tray", False)
                
                # 加载开机自启动设置
                self.startup = settings.get("startup", False)
                
                # 加载自启动类型设置
                self.startup_type = settings.get("startup_type", "user")
                
                # 调试信息
                print(f"设置已从JSON文件加载: minimize_to_tray={self.minimize_to_tray}, startup={self.startup}, startup_type={self.startup_type}")
                print(f"设置文件路径: {self.settings_json_file}")
                
            else:
                # JSON文件不存在，尝试从INI文件迁移设置
                print("JSON设置文件不存在，尝试从INI文件迁移设置")
                
                # 加载任务列表
                tasks = self.settings.value("tasks")
                if tasks and isinstance(tasks, list):
                    self.tasks = tasks
                else:
                    self.tasks = []
                
                # 加载日志文件路径
                self.log_file_path = self.settings.value("log_file_path", "file_organizer.log")
                
                # 加载窗口关闭设置
                minimize_to_tray = self.settings.value("minimize_to_tray")
                if minimize_to_tray is not None:
                    self.minimize_to_tray = bool(minimize_to_tray)
                else:
                    self.minimize_to_tray = False
                
                # 加载开机自启动设置
                startup = self.settings.value("startup")
                if startup is not None:
                    self.startup = bool(startup)
                else:
                    self.startup = False
                
                # 加载自启动类型设置
                startup_type = self.settings.value("startup_type")
                if startup_type:
                    self.startup_type = startup_type
                else:
                    self.startup_type = "user"
                
                # 调试信息
                print(f"设置已从INI文件加载: minimize_to_tray={self.minimize_to_tray}, startup={self.startup}, startup_type={self.startup_type}")
                print(f"设置文件路径: {self.settings.fileName()}")
                
                # 将INI设置迁移到JSON文件
                self.save_settings()
                print("设置已从INI文件迁移到JSON文件")
            
            # 应用自启动设置
            if self.startup:
                self.startup_manager.enable_startup(self.startup_type)
            else:
                self.startup_manager.disable_startup()
            
        except Exception as e:
            print(f"加载配置失败：{str(e)}")
            # 发生错误时，设置默认值
            self.tasks = []
            self.minimize_to_tray = False
            self.startup = False
            self.startup_type = "user"
    
    def save_settings(self):
        """保存用户配置"""
        try:
            import json
            import os
            
            # 创建设置字典
            settings = {
                "tasks": self.tasks,
                "log_file_path": self.log_file_path,
                "minimize_to_tray": self.minimize_to_tray,
                "startup": self.startup,
                "startup_type": self.startup_type,
                "__last_save__": datetime.now().isoformat()
            }
            
            # 写入设置文件
            with open(self.settings_json_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            # 调试信息
            print(f"设置已保存: minimize_to_tray={self.minimize_to_tray}, startup={self.startup}, startup_type={self.startup_type}")
            print(f"设置文件路径: {self.settings_json_file}")
            
            # 应用自启动设置
            if self.startup:
                self.startup_manager.enable_startup(self.startup_type)
            else:
                self.startup_manager.disable_startup()
                
        except Exception as e:
            print(f"保存配置失败：{str(e)}")
    
    def resizeEvent(self, event):
        """窗口大小调整事件处理，实现自适应布局"""
        super().resizeEvent(event)
        
        width = self.width()
        height = self.height()
        
        # 调整任务列表最小高度
        if hasattr(self, 'file_task_list_widget') and self.file_task_list_widget is not None:
            try:
                min_height = max(120, height // 6)
                self.file_task_list_widget.setMinimumHeight(min_height)
            except (RuntimeError, AttributeError):
                pass
        
        # 调整定时任务列表最小高度
        if hasattr(self, 'scheduled_task_list') and self.scheduled_task_list is not None:
            try:
                sched_min_height = max(150, height // 5)
                self.scheduled_task_list.setMinimumHeight(sched_min_height)
            except (RuntimeError, AttributeError):
                pass
    
    def closeEvent(self, event):
        """窗口关闭事件处理，支持自动隐藏到托盘"""
        # 停止当前任务
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.terminate()
            self.current_thread.wait()
        
        # 保存用户配置
        self.save_settings()
        
        # 如果设置了自动隐藏到托盘，则隐藏窗口而不退出
        if self.minimize_to_tray:
            self.hide()
            self.tray_icon.showMessage(
                "文件整理工具",
                "应用程序已最小化到系统托盘",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            # 确保系统托盘图标被正确移除
            self.tray_icon.hide()
            event.accept()


if __name__ == "__main__":
    """主程序入口"""
    app = QApplication(sys.argv)
    
    # 检查命令行参数，判断是否通过自启动方式启动
    is_startup_launch = "--startup" in sys.argv
    
    # 设置应用程序全局图标（使用统一的图标管理器）
    window = FileOrganizerApp()
    app.setWindowIcon(icon_manager.get_application_icon(64))
    
    # 如果是自启动方式启动，则不显示主窗口，直接最小化到系统托盘
    if is_startup_launch:
        # 隐藏主窗口，只显示系统托盘图标
        window.hide()
        # 显示系统托盘通知
        window.show_tray_notification("文件整理工具已启动", "程序已在后台运行，点击托盘图标可显示主窗口")
    else:
        # 正常启动，显示主窗口
        window.show()
    
    sys.exit(app.exec())