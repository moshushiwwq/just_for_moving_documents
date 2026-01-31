#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标资源管理器
功能：提供统一的图标资源管理，确保应用程序各位置使用一致的图标
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QRadialGradient
from PyQt6.QtCore import Qt, QPointF


class IconManager:
    """图标资源管理器类
    
    提供统一的图标资源管理，确保应用程序各位置使用一致的图标
    支持多种尺寸和状态的图标生成
    """
    
    def __init__(self):
        """初始化图标管理器"""
        # 主颜色方案
        self.primary_color = QColor(92, 124, 250)  # 主蓝色
        self.secondary_color = QColor(81, 207, 102)  # 成功绿色
        self.warning_color = QColor(252, 196, 25)  # 警告黄色
        self.error_color = QColor(255, 107, 107)  # 错误红色
        
        # 预生成图标缓存
        self.icon_cache = {}
    
    def get_application_icon(self, size=64):
        """获取应用程序主图标
        
        Args:
            size: 图标尺寸，支持16, 32, 48, 64, 128, 256像素
            
        Returns:
            QIcon: 应用程序图标
        """
        cache_key = f"app_{size}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        pixmap = self._create_application_pixmap(size)
        icon = QIcon(pixmap)
        self.icon_cache[cache_key] = icon
        return icon
    
    def get_tray_icon(self, state="normal"):
        """获取系统托盘图标
        
        Args:
            state: 图标状态 - "normal"(正常), "running"(运行中), "warning"(警告), "error"(错误)
            
        Returns:
            QIcon: 系统托盘图标
        """
        cache_key = f"tray_{state}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        pixmap = self._create_tray_pixmap(state)
        icon = QIcon(pixmap)
        self.icon_cache[cache_key] = icon
        return icon
    
    def get_dialog_icon(self, size=32):
        """获取对话框图标
        
        Args:
            size: 图标尺寸
            
        Returns:
            QIcon: 对话框图标
        """
        cache_key = f"dialog_{size}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        pixmap = self._create_dialog_pixmap(size)
        icon = QIcon(pixmap)
        self.icon_cache[cache_key] = icon
        return icon
    
    def _create_application_pixmap(self, size):
        """创建应用程序主图标位图
        
        Args:
            size: 图标尺寸
            
        Returns:
            QPixmap: 应用程序图标位图
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        center_x, center_y = size // 2, size // 2
        radius = size * 0.4  # 图标半径
        
        # 创建渐变背景
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, self.primary_color.lighter(150))
        gradient.setColorAt(0.7, self.primary_color)
        gradient.setColorAt(1, self.primary_color.darker(120))
        
        painter.setBrush(gradient)
        painter.setPen(QPen(self.primary_color.darker(150), max(1, size // 32)))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))
        
        # 绘制文件整理图标（文件夹+箭头）
        self._draw_file_organizer_icon(painter, center_x, center_y, size)
        
        painter.end()
        return pixmap
    
    def _create_tray_pixmap(self, state):
        """创建系统托盘图标位图
        
        Args:
            state: 图标状态
            
        Returns:
            QPixmap: 系统托盘图标位图
        """
        size = 32  # 系统托盘图标标准尺寸
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x, center_y = size // 2, size // 2
        radius = 12
        
        # 根据状态选择颜色
        color_map = {
            "normal": self.primary_color,
            "running": self.secondary_color,
            "warning": self.warning_color,
            "error": self.error_color
        }
        
        primary_color = color_map.get(state, self.primary_color)
        secondary_color = primary_color.darker(130)
        
        # 创建渐变背景
        gradient = QRadialGradient(center_x - 3, center_y - 3, radius)
        gradient.setColorAt(0, primary_color.lighter(130))
        gradient.setColorAt(1, primary_color)
        
        painter.setBrush(gradient)
        painter.setPen(QPen(secondary_color, 1))
        painter.drawEllipse(int(center_x - radius + 1), int(center_y - radius + 1), int(radius * 2 - 2), int(radius * 2 - 2))
        
        # 绘制简化的文件整理图标
        self._draw_simplified_icon(painter, center_x, center_y)
        
        painter.end()
        return pixmap
    
    def _create_dialog_pixmap(self, size):
        """创建对话框图标位图
        
        Args:
            size: 图标尺寸
            
        Returns:
            QPixmap: 对话框图标位图
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x, center_y = size // 2, size // 2
        radius = size * 0.35
        
        # 创建渐变背景
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, self.primary_color.lighter(140))
        gradient.setColorAt(0.8, self.primary_color)
        gradient.setColorAt(1, self.primary_color.darker(130))
        
        painter.setBrush(gradient)
        painter.setPen(QPen(self.primary_color.darker(150), max(1, size // 40)))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))
        
        # 绘制中等复杂度的图标
        self._draw_medium_icon(painter, center_x, center_y, size)
        
        painter.end()
        return pixmap
    
    def _draw_file_organizer_icon(self, painter, center_x, center_y, size):
        """绘制文件整理图标（详细版本）
        
        Args:
            painter: 绘图器
            center_x: 中心点X坐标
            center_y: 中心点Y坐标
            size: 图标尺寸
        """
        scale = size / 64.0
        
        # 绘制文件夹
        folder_color = QColor(255, 255, 255)
        painter.setPen(QPen(folder_color, max(2, int(2 * scale))))
        painter.setBrush(QBrush(folder_color))
        
        # 文件夹主体
        folder_points = [
            QPointF(center_x - 12 * scale, center_y - 8 * scale),
            QPointF(center_x - 8 * scale, center_y - 12 * scale),
            QPointF(center_x + 10 * scale, center_y - 12 * scale),
            QPointF(center_x + 12 * scale, center_y - 8 * scale),
            QPointF(center_x + 12 * scale, center_y + 8 * scale),
            QPointF(center_x - 12 * scale, center_y + 8 * scale)
        ]
        painter.drawPolygon(folder_points)
        
        # 文件夹标签
        painter.drawRect(int(center_x - 8 * scale), int(center_y - 12 * scale), 
                        int(16 * scale), int(4 * scale))
        
        # 绘制箭头（表示整理）
        arrow_color = self.primary_color
        painter.setPen(QPen(arrow_color, max(2, int(2 * scale))))
        
        # 箭头线
        painter.drawLine(int(center_x - 5 * scale), int(center_y),
                        int(center_x + 5 * scale), int(center_y))
        
        # 箭头头部
        arrow_points = [
            QPointF(center_x + 5 * scale, center_y),
            QPointF(center_x + 2 * scale, center_y - 3 * scale),
            QPointF(center_x + 2 * scale, center_y + 3 * scale)
        ]
        painter.drawPolygon(arrow_points)
    
    def _draw_simplified_icon(self, painter, center_x, center_y):
        """绘制简化版图标（用于系统托盘）
        
        Args:
            painter: 绘图器
            center_x: 中心点X坐标
            center_y: 中心点Y坐标
        """
        # 绘制文件夹简化图标
        icon_color = QColor(255, 255, 255)
        painter.setPen(QPen(icon_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(QBrush(icon_color))
        
        # 简化的文件夹图标
        icon_path = [
            QPointF(center_x - 4, center_y - 2),
            QPointF(center_x - 1, center_y - 5),
            QPointF(center_x + 5, center_y - 9),
            QPointF(center_x + 8, center_y - 6),
            QPointF(center_x + 4, center_y - 2),
            QPointF(center_x + 1, center_y - 1)
        ]
        painter.drawPolyline(icon_path)
    
    def _draw_medium_icon(self, painter, center_x, center_y, size):
        """绘制中等复杂度图标（用于对话框）
        
        Args:
            painter: 绘图器
            center_x: 中心点X坐标
            center_y: 中心点Y坐标
            size: 图标尺寸
        """
        scale = size / 32.0
        
        # 绘制文件夹图标
        folder_color = QColor(255, 255, 255)
        painter.setPen(QPen(folder_color, max(1, int(1.5 * scale))))
        painter.setBrush(QBrush(folder_color))
        
        # 文件夹主体
        folder_points = [
            QPointF(center_x - 6 * scale, center_y - 4 * scale),
            QPointF(center_x - 4 * scale, center_y - 6 * scale),
            QPointF(center_x + 5 * scale, center_y - 6 * scale),
            QPointF(center_x + 6 * scale, center_y - 4 * scale),
            QPointF(center_x + 6 * scale, center_y + 4 * scale),
            QPointF(center_x - 6 * scale, center_y + 4 * scale)
        ]
        painter.drawPolygon(folder_points)
        
        # 文件夹标签
        painter.drawRect(int(center_x - 4 * scale), int(center_y - 6 * scale), 
                        int(8 * scale), int(2 * scale))
        
        # 简化的箭头
        arrow_color = self.primary_color
        painter.setPen(QPen(arrow_color, max(1, int(1.5 * scale))))
        
        # 箭头线
        painter.drawLine(int(center_x - 2 * scale), int(center_y),
                        int(center_x + 2 * scale), int(center_y))
        
        # 箭头头部
        arrow_points = [
            QPointF(center_x + 2 * scale, center_y),
            QPointF(center_x + 1 * scale, center_y - 1.5 * scale),
            QPointF(center_x + 1 * scale, center_y + 1.5 * scale)
        ]
        painter.drawPolygon(arrow_points)


# 全局图标管理器实例
icon_manager = IconManager()