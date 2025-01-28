import pygame
import sys
import math
import os
import json
import random
import numpy as np
from player import Player
from world import World
from inventory import Inventory
from save_manager import SaveManager
from utils import get_font, get_documents_path

# 初始化Pygame
pygame.init()

# 游戏常量
TILE_SIZE = 32
BASE_WIDTH = 1280  # 固定宽度
BASE_HEIGHT = 720  # 固定高度
DESIGN_TILES_X = 120  # 1080p下水平方向的方块数

# 颜色常量
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
LIGHT_GRAY = (200, 200, 200)
LIGHT_RED = (255, 100, 100)
DARK_GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)

# 职业选项
CLASSES = ["战士", "法师", "弓箭手", "盗贼"]

# 发型选项
HAIRSTYLES = ["短发", "长发", "马尾", "双马尾", "波波头", "蓬松卷发", "直发", "莫西干", "寸头", "板寸", 
             "爆炸头", "辫子", "丸子头", "中分", "偏分", "飞机头", "锅盖头", "脏辫", "编织辫", "秃头"]

# 体型选项
BODY_TYPES = ["瘦小", "标准", "魁梧"]

# 游戏状态常量
GAME_STATES = {
    "MAIN_MENU": "main_menu",
    "CHARACTER_SELECT": "character_select",
    "CHARACTER_CREATE": "character_create",
    "MAP_SELECT": "map_select",
    "PLAYING": "playing",
    "SETTINGS": "settings",
    "CREDITS": "credits"
}

# 地形常量
TERRAIN_EMPTY = 0
TERRAIN_GROUND = 1
TERRAIN_PLATFORM = 2

class SimpleButton:
    def __init__(self, x, y, width, height, text, color=(200, 200, 220), font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = get_font(font_size)
        self.color = color
        self.is_hovered = False
        self.is_clicked = False
        
        # 加载音效
        self.hover_sound = None
        self.click_sound = None
        try:
            self.hover_sound = pygame.mixer.Sound("assets/sounds/ui/hover.wav")
            self.hover_sound.set_volume(0.15)
            
            self.click_sound = pygame.mixer.Sound("assets/sounds/ui/click.wav")
            self.click_sound.set_volume(0.3)
        except Exception as e:
            print(f"Warning: Could not load button sounds: {e}")
        
    def draw(self, screen):
        # 计算六边形的顶点
        center_x = self.rect.centerx
        center_y = self.rect.centery
        width = self.rect.width
        height = self.rect.height
        
        # 计算六边形的顶点（上边是横线的六边形）
        points = []
        # 上边的两个点
        points.append((center_x - width/2, center_y - height/3))  # 左上
        points.append((center_x + width/2, center_y - height/3))  # 右上
        # 右边的点
        points.append((center_x + width/2 + width/8, center_y))   # 右
        # 下边的两个点
        points.append((center_x + width/2, center_y + height/3))  # 右下
        points.append((center_x - width/2, center_y + height/3))  # 左下
        # 左边的点
        points.append((center_x - width/2 - width/8, center_y))   # 左
        
        # 根据悬停和点击状态确定颜色
        current_color = self.color
        if self.is_clicked:
            current_color = tuple(max(0, c - 30) for c in self.color)
        elif self.is_hovered:
            current_color = tuple(min(255, c + 30) for c in self.color)
        
        # 绘制填充的六边形（分上下两部分）
        upper_color = tuple(min(255, c + 20) for c in current_color)
        lower_color = tuple(max(0, c - 20) for c in current_color)
        
        # 绘制上半部分
        upper_points = [
            points[0],  # 左上
            points[1],  # 右上
            points[2],  # 右
            (center_x, center_y),  # 中心
            points[5]   # 左
        ]
        pygame.draw.polygon(screen, upper_color, upper_points)
        
        # 绘制下半部分
        lower_points = [
            points[2],  # 右
            points[3],  # 右下
            points[4],  # 左下
            points[5],  # 左
            (center_x, center_y)  # 中心
        ]
        pygame.draw.polygon(screen, lower_color, lower_points)
        
        # 绘制金色边框
        border_color = (255, 215, 0) if self.is_hovered else (218, 165, 32)
        border_width = 3 if self.is_hovered else 2
        pygame.draw.polygon(screen, border_color, points, border_width)
        
        # 绘制文本（黑色）
        text_color = (0, 0, 0)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        previous_hover = self.is_hovered
        
        # 检查点是否在六边形内
        center_x = self.rect.centerx
        center_y = self.rect.centery
        width = self.rect.width
        height = self.rect.height
        
        # 简化的六边形碰撞检测
        dx = abs(mouse_pos[0] - center_x)
        dy = abs(mouse_pos[1] - center_y)
        
        # 使用改进的碰撞检测来匹配六边形形状
        if dy <= height/3:
            max_dx = width/2 + (width/8) * (1 - dy/(height/3))
            self.is_hovered = dx <= max_dx
        else:
            self.is_hovered = dx <= width/2 and dy <= height/3
        
        # 处理悬停音效
        if not previous_hover and self.is_hovered and self.hover_sound:
            self.hover_sound.play()
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_clicked = True
                if self.click_sound:
                    self.click_sound.play()
                    
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_clicked = self.is_clicked
            self.is_clicked = False
            if was_clicked and self.is_hovered:
                return True
                
        return False

class Slider:
    def __init__(self, x, y, width, height, label, max_value=255, initial_value=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = initial_value
        self.max_value = max_value
        self.dragging = False
        self.font = get_font(24)
    
    def draw(self, screen):
        # 绘制滑块背景
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 2)
        
        # 计算滑块位置
        handle_x = self.rect.x + (self.value / self.max_value) * self.rect.width
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 5, 10, self.rect.height + 10)
        
        # 绘制滑块
        pygame.draw.rect(screen, (200, 200, 200), handle_rect)
        pygame.draw.rect(screen, (255, 255, 255), handle_rect, 2)
        
        # 绘制数值（移到滑块右边）
        value_text = self.font.render(str(int(self.value)), True, (255, 255, 255))
        value_rect = value_text.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
        screen.blit(value_text, value_rect)
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                if self.rect.collidepoint(event.pos):
                    self.dragging = True
                    # 更新值
                    self.value = (event.pos[0] - self.rect.x) / self.rect.width * self.max_value
                    self.value = max(0, min(self.max_value, self.value))
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键释放
                was_dragging = self.dragging
                self.dragging = False
                return was_dragging
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and event.buttons[0]:  # 左键拖动
                # 更新值
                self.value = (event.pos[0] - self.rect.x) / self.rect.width * self.max_value
                self.value = max(0, min(self.max_value, self.value))
                return True
        return False

class CharacterCreator:
    def __init__(self, x, y, width, height):
        """初始化角色创建器"""
        self.rect = pygame.Rect(x, y, width, height)
        self.name = ""
        self.name_active = False
        self.hairstyle_index = 0
        self.body_type_index = 0
        self.class_index = 0
        
        # 创建颜色滑块
        self.color_sliders = [
            Slider(x + 50, y + 300, 200, 20, "R", 255),
            Slider(x + 50, y + 330, 200, 20, "G", 255),
            Slider(x + 50, y + 360, 200, 20, "B", 255)
        ]
        
        # 创建按钮
        button_width = 200
        button_height = 40
        button_x = x + (width - button_width) // 2
        
        self.confirm_button = SimpleButton(
            button_x,
            y + height - 100,
            button_width,
            button_height,
            "确认",
            color=(0, 200, 0),
            font_size=32
        )
        
        self.cancel_button = SimpleButton(
            button_x,
            y + height - 50,
            button_width,
            button_height,
            "取消",
            color=(200, 0, 0),
            font_size=32
        )
        
        # 创建发型选择按钮
        self.hairstyle_prev = SimpleButton(
            x + 50,
            y + 150,
            40,
            40,
            "<",
            color=(100, 100, 200),
            font_size=32
        )
        
        self.hairstyle_next = SimpleButton(
            x + width - 90,
            y + 150,
            40,
            40,
            ">",
            color=(100, 100, 200),
            font_size=32
        )
        
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查确认按钮
            if self.confirm_button.handle_event(event):
                if self.name:  # 只有在有名字的情况下才确认
                    return True
                return False
            
            # 检查取消按钮
            if self.cancel_button.handle_event(event):
                return False
            
            # 检查发型选择按钮
            if self.hairstyle_prev.handle_event(event):
                self.hairstyle_index = (self.hairstyle_index - 1) % len(HAIRSTYLES)
                return False
            
            if self.hairstyle_next.handle_event(event):
                self.hairstyle_index = (self.hairstyle_index + 1) % len(HAIRSTYLES)
                return False
            
            # 检查名称输入框
            name_rect = pygame.Rect(self.rect.x + 50, self.rect.y + 50, 300, 40)
            self.name_active = name_rect.collidepoint(event.pos)
            
            # 检查颜色滑块
            for slider in self.color_sliders:
                if slider.handle_event(event):
                    return False
            
        elif event.type == pygame.KEYDOWN and self.name_active:
            if event.key == pygame.K_RETURN:
                self.name_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif len(self.name) < 20:  # 限制名称长度
                if event.unicode.isprintable():
                    self.name += event.unicode
            return False
            
        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:  # 左键拖动
                for slider in self.color_sliders:
                    if slider.handle_event(event):
                        return False
        
        return False

    def draw(self, screen):
        """绘制角色创建界面"""
        # 清空并填充背景
        self.buffer.fill((0, 20, 50))  # 深蓝色背景
        
        # 如果在发型选择界面，绘制发型选择界面
        if self.in_hairstyle_selection:
            self.draw_hairstyle_selection()
            return
        
        # 创建半透明面板
        panel_width = 1000  # 增加面板宽度
        panel_height = 600  # 增加面板高度
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2
        
        # 绘制标题
        title = self.title_font.render(self.get_text("create_character"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, panel_y - 30))
        self.buffer.blit(title, title_rect)
        
        # 绘制面板背景
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 128))
        self.buffer.blit(panel, (panel_x, panel_y))
        
        # 分割线
        pygame.draw.line(self.buffer, (100, 100, 150), 
                        (panel_x + 700, panel_y + 20),  # 调整分割线位置
                        (panel_x + 700, panel_y + panel_height - 20), 2)
        
        # 绘制输入框和标签
        input_y = panel_y + 40  # 稍微增加顶部间距
        label_x = panel_x + 80  # 标签左移
        input_x = panel_x + 180  # 输入框和按钮左移
        spacing = 80  # 增加垂直间距
        
        # 角色名称输入
        name_label = self.font.render("角色名称:", True, (255, 255, 255))
        self.buffer.blit(name_label, (label_x, input_y))
        
        # 绘制输入框和文本
        pygame.draw.rect(self.buffer, (255, 255, 255) if self.input_active else (150, 150, 150),
                        (input_x, input_y, 200, 30), 2)
        if hasattr(self, 'character_name'):
            name_text = self.font.render(self.character_name, True, (255, 255, 255))
            self.buffer.blit(name_text, (input_x + 5, input_y + 5))
        
        # 如果输入框处于活动状态，绘制光标
        if self.input_active and hasattr(self, 'character_name'):
            cursor_x = input_x + 5 + self.font.size(self.character_name)[0]
            if pygame.time.get_ticks() % 1000 < 500:  # 光标闪烁效果
                pygame.draw.line(self.buffer, (255, 255, 255),
                               (cursor_x, input_y + 5),
                               (cursor_x, input_y + 25), 2)
        
        # 性别选择
        input_y += spacing
        gender_label = self.font.render("性别:", True, (255, 255, 255))
        self.buffer.blit(gender_label, (label_x, input_y))
        
        # 性别按钮
        gender_button_width = 100  # 增加按钮宽度
        gender_spacing = 60  # 增加按钮间距
        for i, gender in enumerate(["男", "女"]):
            button_x = input_x + i * (gender_button_width + gender_spacing)
            button = SimpleButton(
                button_x,
                input_y,
                gender_button_width,
                35,  # 增加按钮高度
                gender,
                color=(240, 240, 255) if self.selected_gender == gender else (220, 220, 240)
            )
            button.draw(self.buffer)
            if gender == "男":
                self.male_button_rect = button.rect
            else:
                self.female_button_rect = button.rect
        
        # 发型选择
        input_y += spacing
        hair_label = self.font.render("发型:", True, (255, 255, 255))
        self.buffer.blit(hair_label, (label_x, input_y))
        
        # 发型按钮
        hair_button = SimpleButton(
            input_x,
            input_y,
            250,  # 增加按钮宽度
            35,   # 增加按钮高度
            "选择发型",
            color=(220, 220, 240)
        )
        hair_button.draw(self.buffer)
        self.hair_button_rect = hair_button.rect
        
        # 体型选择
        input_y += spacing
        body_label = self.font.render("体型:", True, (255, 255, 255))
        self.buffer.blit(body_label, (label_x, input_y))
        
        # 体型按钮
        body_button_width = 100  # 增加按钮宽度
        body_spacing = 50  # 增加按钮间距
        for i, body_type in enumerate(BODY_TYPES):
            button_x = input_x + i * (body_button_width + body_spacing)
            button = SimpleButton(
                button_x,
                input_y,
                body_button_width,
                35,  # 增加按钮高度
                body_type,
                color=(240, 240, 255) if self.selected_body_type == body_type else (220, 220, 240)
            )
            button.draw(self.buffer)
            if i == 0:
                self.thin_button_rect = button.rect
            elif i == 1:
                self.normal_button_rect = button.rect
            else:
                self.fat_button_rect = button.rect
        
        # 职业选择
        input_y += spacing
        class_label = self.font.render("职业:", True, (255, 255, 255))
        self.buffer.blit(class_label, (label_x, input_y))
        
        # 职业按钮
        class_button_width = 90  # 减小按钮宽度
        class_spacing = 40  # 减小按钮间距
        total_width = (class_button_width * len(CLASSES)) + (class_spacing * (len(CLASSES) - 1))
        start_x = input_x  # 起始位置
        
        for i, class_type in enumerate(CLASSES):
            button_x = start_x + i * (class_button_width + class_spacing)
            button = SimpleButton(
                button_x,
                input_y,
                class_button_width,
                35,  # 保持按钮高度
                class_type,
                color=(240, 240, 255) if self.selected_class == class_type else (220, 220, 240)
            )
            button.draw(self.buffer)
            if i == 0:
                self.warrior_button_rect = button.rect
            elif i == 1:
                self.mage_button_rect = button.rect
            elif i == 2:
                self.archer_button_rect = button.rect
            else:
                self.thief_button_rect = button.rect
        
        # 底部按钮
        button_y = panel_y + panel_height - 60  # 调整底部按钮位置
        button_height = 45  # 增加按钮高度
        
        # 返回按钮
        back_button = SimpleButton(
            panel_x + 80,  # 左移
            button_y,
            120,  # 增加按钮宽度
            button_height,
            "返回",
            color=(220, 220, 240)
        )
        back_button.draw(self.buffer)
        self.back_button_rect = back_button.rect
        
        # 创建按钮
        create_button = SimpleButton(
            panel_x + panel_width - 200,  # 调整位置
            button_y,
            120,  # 增加按钮宽度
            button_height,
            "创建",
            color=(220, 240, 220)
        )
        create_button.draw(self.buffer)
        self.create_button_rect = create_button.rect
        
        # 绘制角色预览
        preview_x = panel_x + 750  # 调整预览区域位置
        preview_y = panel_y + 50
        preview_width = 200
        preview_height = 400  # 增加预览区域高度
        
        # 绘制预览区域标题
        preview_title = self.font.render("角色预览", True, (255, 255, 255))
        preview_title_rect = preview_title.get_rect(center=(preview_x + preview_width//2, preview_y - 20))
        self.buffer.blit(preview_title, preview_title_rect)
        
        # 绘制预览区域背景
        pygame.draw.rect(self.buffer, (40, 40, 80), 
                        (preview_x, preview_y, preview_width, preview_height))
        
        # 绘制角色预览
        if hasattr(self, 'selected_gender') and hasattr(self, 'selected_body_type'):
            preview_data = {
                'name': '预览',
                'gender': self.selected_gender,
                'body_type': self.selected_body_type,
                'hairstyle': getattr(self, 'selected_hairstyle', {'style': '1', 'color': (0, 0, 0)}),
                'class': getattr(self, 'selected_class', '战士'),
                'skin_color': (255, 223, 196) if self.selected_gender == '女' else (240, 200, 160),
                'health': 100,
                'mana': 100
            }
            self.draw_character_preview(preview_data, preview_x, preview_y, (preview_width, preview_height))
        
        # 如果有弹出框，绘制弹出框
        if hasattr(self, 'popup') and self.popup and self.popup.visible:
            if not self.popup.should_hide():
                self.buffer.blit(self.popup.surface, self.popup.rect)
            else:
                self.popup = None
                self.needs_redraw = True
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def get_character_data(self):
        """获取角色数据，如果没有输入名称则返回 None"""
        if not self.name:  # 如果名称为空
            return None
            
        return {
            "name": self.name,
            "hairstyle": HAIRSTYLES[self.hairstyle_index],
            "body_type": BODY_TYPES[self.body_type_index],
            "class": CLASSES[self.class_index],
            "skin_color": [int(s.value) for s in self.color_sliders],
            "health": 100,
            "mana": 100,
            "inventory": []
        }

class MessageBox:
    def __init__(self, x, y, width, height, message, font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.message = message
        self.font = get_font(font_size)
        self.visible = True
        
        # 创建消息框的surface
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 创建确认按钮
        button_width = 100
        button_height = 40
        button_x = (width - button_width) // 2
        button_y = height - 60
        
        self.confirm_button = SimpleButton(
            button_x,
            button_y,
            button_width,
            button_height,
            "确定",
            color=(200, 200, 220),  # 银白色
            font_size=32
        )
        
        # 预渲染消息框
        self.render()
        
    def render(self):
        """渲染消息框到surface"""
        # 清空surface
        self.surface.fill((0, 0, 0, 0))
        
        # 绘制消息框背景
        pygame.draw.rect(self.surface, (50, 50, 50, 240), (0, 0, self.rect.width, self.rect.height))
        # 使用金色边框
        border_color = (218, 165, 32)  # 暗金色
        pygame.draw.rect(self.surface, border_color, (0, 0, self.rect.width, self.rect.height), 2)
        
        # 绘制消息文本
        text = self.font.render(self.message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.rect.width//2, self.rect.height//2 - 20))
        self.surface.blit(text, text_rect)
        
        # 绘制确认按钮
        self.confirm_button.draw(self.surface)
        
    def draw(self, surface):
        if not self.visible:
            return
            
        # 绘制全屏半透明背景
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 增加透明度，使背景更暗
        surface.blit(overlay, (0, 0))
        
        # 绘制消息框
        surface.blit(self.surface, self.rect)
        
        # 强制重绘
        pygame.display.update()

    def handle_event(self, event):
        if not self.visible:
            return False
            
        # 检查点击是否在消息框内
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.rect.collidepoint(event.pos):
                return False
            
            # 转换鼠标坐标到按钮的相对坐标系
            relative_pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
            
            # 获取按钮的绝对位置
            button_rect = pygame.Rect(
                self.rect.x + self.confirm_button.rect.x,
                self.rect.y + self.confirm_button.rect.y,
                self.confirm_button.rect.width,
                self.confirm_button.rect.height
            )
            
            # 检查点击是否在按钮上
            if button_rect.collidepoint(event.pos):
                self.visible = False
                return True
        
        # 处理鼠标移动事件，更新按钮悬停状态
        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                relative_pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                button_event = pygame.event.Event(event.type, {'pos': relative_pos, 'buttons': event.buttons})
                self.confirm_button.handle_event(button_event)
                self.needs_redraw = True
                return True
        
        return False

class Game:
    def __init__(self):
        """初始化游戏"""
        pygame.init()
        pygame.mixer.init()
        
        # 添加翻译字典
        self.translations = {
            "简体中文": {
                "start_game": "开始游戏",
                "settings": "设置",
                "credits": "制作人员",
                "quit": "退出",
                "back": "返回",
                "save_settings": "保存设置",
                "sound_volume": "音效音量",
                "music_volume": "音乐音量",
                "graphics_quality": "画面质量",
                "language": "语言",
                "low": "低",
                "medium": "中",
                "high": "高",
                "create_character": "创建角色",
                "select_character": "选择角色",
                "delete_character": "删除角色",
                "create_map": "创建地图",
                "select_map": "选择地图",
                "delete_map": "删除地图",
                "settings_saved": "设置已保存",
                "confirm_delete": "确认删除？",
                "yes": "是",
                "no": "否",
                "achievements": "成就",
                "resolution": "分辨率",
                "borderless": "无边框窗口",
                "fullscreen": "全屏",
                "windowed": "窗口",
                "apply": "应用",
                "resolution_changed": "分辨率已更改",
                "display_mode": "显示模式",
                "character_name": "角色名称",
                "gender": "性别",
                "hairstyle": "发型",
                "body_type": "体型",
                "class": "职业",
                "preview": "预览",
                "health": "生命值",
                "mana": "魔力值",
                "playtime": "游戏时间",
                "delete": "删除",
                "create": "创建",
                "name": "名字",
                "small": "小型",
                "medium": "中型",
                "large": "大型",
                "small_world": "小型世界",
                "medium_world": "中型世界",
                "large_world": "大型世界",
                "grid": "格",
                "fast_game_exploration": "适合快速游戏和探索",
                "balanced_gameplay": "平衡的游戏体验",
                "epic_adventure": "史诗般的冒险之旅",
                "select_hairstyle": "选择发型",
                "prev_page": "上一页",
                "next_page": "下一页",
                "confirm": "确认",
                "normal": "普通",
                "warrior": "战士",
                "game_design": "游戏设计",
                "programming": "程序开发",
                "art_design": "美术设计",
                "sound_design": "音效设计",
                "testing_team": "测试团队",
                "team": "团队",
                "create_world": "创建世界"
            },
            "繁體中文": {
                "start_game": "開始遊戲",
                "settings": "設置",
                "credits": "製作人員",
                "quit": "退出",
                "back": "返回",
                "save_settings": "保存設置",
                "sound_volume": "音效音量",
                "music_volume": "音樂音量",
                "graphics_quality": "畫面質量",
                "language": "語言",
                "low": "低",
                "medium": "中",
                "high": "高",
                "create_character": "創建角色",
                "select_character": "選擇角色",
                "delete_character": "刪除角色",
                "create_map": "創建地圖",
                "select_map": "選擇地圖",
                "delete_map": "刪除地圖",
                "settings_saved": "設置已保存",
                "confirm_delete": "確認刪除？",
                "yes": "是",
                "no": "否",
                "achievements": "成就",
                "resolution": "分辨率",
                "borderless": "無邊框窗口",
                "fullscreen": "全屏",
                "windowed": "窗口",
                "apply": "應用",
                "resolution_changed": "分辨率已更改",
                "display_mode": "顯示模式",
                "character_name": "角色名稱",
                "gender": "性別",
                "hairstyle": "髮型",
                "body_type": "體型",
                "class": "職業",
                "preview": "預覽",
                "health": "生命值",
                "mana": "魔力值",
                "playtime": "遊戲時間",
                "delete": "刪除",
                "create": "創建",
                "name": "名字",
                "small": "小型",
                "medium": "中型",
                "large": "大型",
                "small_world": "小型世界",
                "medium_world": "中型世界",
                "large_world": "大型世界",
                "grid": "格",
                "fast_game_exploration": "適合快速遊戲和探索",
                "balanced_gameplay": "平衡的遊戲體驗",
                "epic_adventure": "史詩般的冒險之旅",
                "select_hairstyle": "選擇髮型",
                "prev_page": "上一頁",
                "next_page": "下一頁",
                "confirm": "確認",
                "normal": "普通",
                "warrior": "戰士",
                "game_design": "遊戲設計",
                "programming": "程序開發",
                "art_design": "美術設計",
                "sound_design": "音效設計",
                "testing_team": "測試團隊",
                "team": "團隊",
                "create_world": "創建世界"
            },
            "日本語": {
                "start_game": "ゲーム開始",
                "settings": "設定",
                "credits": "クレジット",
                "quit": "終了",
                "back": "戻る",
                "save_settings": "設定を保存",
                "sound_volume": "効果音量",
                "music_volume": "音楽音量",
                "graphics_quality": "画質",
                "language": "言語",
                "low": "低",
                "medium": "中",
                "high": "高",
                "create_character": "キャラクター作成",
                "select_character": "キャラクター選択",
                "delete_character": "キャラクター削除",
                "create_map": "マップ作成",
                "select_map": "マップ選択",
                "delete_map": "マップ削除",
                "settings_saved": "設定を保存しました",
                "confirm_delete": "削除しますか？",
                "yes": "はい",
                "no": "いいえ",
                "achievements": "実績",
                "resolution": "解像度",
                "borderless": "ボーダーレス",
                "fullscreen": "フルスクリーン",
                "windowed": "ウィンドウ",
                "apply": "適用",
                "resolution_changed": "解像度を変更しました",
                "display_mode": "表示モード",
                "character_name": "キャラクター名",
                "gender": "性別",
                "hairstyle": "ヘアスタイル",
                "body_type": "体型",
                "class": "職業",
                "preview": "プレビュー",
                "health": "体力",
                "mana": "魔力",
                "playtime": "プレイ時間",
                "delete": "削除",
                "create": "作成",
                "name": "名前",
                "small": "小",
                "medium": "中",
                "large": "大",
                "small_world": "小さい世界",
                "medium_world": "中くらいの世界",
                "large_world": "大きい世界",
                "grid": "マス",
                "fast_game_exploration": "クイックゲームと探索に最適",
                "balanced_gameplay": "バランスの取れたゲームプレイ",
                "epic_adventure": "壮大な冒険の旅",
                "select_hairstyle": "ヘアスタイル選択",
                "prev_page": "前のページ",
                "next_page": "次のページ",
                "confirm": "確認",
                "normal": "普通",
                "warrior": "戦士",
                "game_design": "ゲームデザイン",
                "programming": "プログラミング",
                "art_design": "アートデザイン",
                "sound_design": "サウンドデザイン",
                "testing_team": "テストチーム",
                "team": "チーム",
                "create_world": "世界作成"
            },
            "English": {
                "start_game": "Start Game",
                "settings": "Settings",
                "credits": "Credits",
                "quit": "Quit",
                "back": "Back",
                "save_settings": "Save Settings",
                "sound_volume": "Sound Volume",
                "music_volume": "Music Volume",
                "graphics_quality": "Graphics Quality",
                "language": "Language",
                "low": "Low",
                "medium": "Medium",
                "high": "High",
                "create_character": "Create Character",
                "select_character": "Select Character",
                "delete_character": "Delete Character",
                "create_map": "Create Map",
                "select_map": "Select Map",
                "delete_map": "Delete Map",
                "settings_saved": "Settings Saved",
                "confirm_delete": "Confirm Delete?",
                "yes": "Yes",
                "no": "No",
                "achievements": "Achievements",
                "resolution": "Resolution",
                "borderless": "Borderless Window",
                "fullscreen": "Fullscreen",
                "windowed": "Windowed",
                "apply": "Apply",
                "resolution_changed": "Resolution Changed",
                "display_mode": "Display Mode",
                "character_name": "Character Name",
                "gender": "Gender",
                "hairstyle": "Hairstyle",
                "body_type": "Body Type",
                "class": "Class",
                "preview": "Preview",
                "health": "Health",
                "mana": "Mana",
                "playtime": "Playtime",
                "delete": "Delete",
                "create": "Create",
                "name": "Name",
                "small": "Small",
                "medium": "Medium",
                "large": "Large",
                "small_world": "Small World",
                "medium_world": "Medium World",
                "large_world": "Large World",
                "grid": "Grid",
                "fast_game_exploration": "Suitable for quick games and exploration",
                "balanced_gameplay": "Balanced gameplay experience",
                "epic_adventure": "Epic adventure journey",
                "select_hairstyle": "Select Hairstyle",
                "prev_page": "Previous",
                "next_page": "Next",
                "confirm": "Confirm",
                "normal": "Normal",
                "warrior": "Warrior",
                "game_design": "Game Design",
                "programming": "Programming",
                "art_design": "Art Design",
                "sound_design": "Sound Design",
                "testing_team": "Testing Team",
                "team": "Team",
                "create_world": "Create World"
            }
        }
        
        # 设置默认语言
        self.language = "简体中文"
        
        # 添加分辨率选项
        self.resolutions = [
            "1280x720",
            "1366x768",
            "1440x900",
            "1600x900",
            "1680x1050",
            "1920x1080"
        ]
        
        # 添加显示模式
        self.display_modes = ["windowed", "borderless", "fullscreen"]
        
        # 设置默认分辨率和显示模式
        self.current_resolution = "1280x720"
        self.display_mode = "windowed"
        
        # 计算初始缩放比例（基于1280x720的基准分辨率）
        width, height = map(int, self.current_resolution.split('x'))
        self.scale_x = width / 1280
        self.scale_y = height / 720
        
        # 初始化设置界面的滚动位置
        self.settings_scroll_y = 0
        self.settings_max_scroll = 0
        
        # 加载设置
        self.load_settings()
        
        # 应用显示设置
        self.apply_display_settings()
        
        # 创建缓冲区
        self.buffer = pygame.Surface((self.screen_width, self.screen_height))
        
        # 初始化时钟
        self.clock = pygame.time.Clock()
        
        # 加载字体
        self.font = get_font(32)
        self.title_font = get_font(48)
        
        # 游戏状态
        self.game_state = "main_menu"
        self.running = True
        self.needs_redraw = True
        
        # 加载背景图片
        try:
            self.menu_background = pygame.image.load("assets/backgrounds/menu_background.png").convert_alpha()
        except Exception as e:
            print(f"Warning: Could not load background image: {e}")
            self.menu_background = None
        
        # 加载背景音乐
        try:
            pygame.mixer.music.load("assets/music/menu/background_music.mp3")
            pygame.mixer.music.set_volume(0.5)  # 设置音量为50%
            pygame.mixer.music.play(-1)  # -1表示循环播放
        except Exception as e:
            print(f"Warning: Could not load background music: {e}")
        
        # 初始化按钮
        self.initialize_buttons()
        
        # 设置路径
        self.player_path = "players"
        self.world_path = "worlds"
        os.makedirs(self.player_path, exist_ok=True)
        os.makedirs(self.world_path, exist_ok=True)
        
        # 加载音效
        try:
            self.click_sound = pygame.mixer.Sound("assets/sounds/ui/click.wav")
            self.click_sound.set_volume(0.5)  # 设置音量为50%
        except Exception as e:
            print(f"加载音效时出错: {e}")
            self.click_sound = None
        
        # 加载角色和地图列表
        self.characters = []
        self.maps = []
        self.load_characters_and_maps()
        
        # 初始化角色创建相关属性
        self.character_name = ""
        self.input_active = False
        self.selected_gender = '男'
        self.selected_hairstyle = {'style': '1', 'color': (0, 0, 0)}  # 默认发型和发色
        self.selected_body_type = BODY_TYPES[1]  # 默认选择"普通"体型
        self.selected_class = CLASSES[0]  # 默认选择"战士"职业
        self.in_hairstyle_selection = False  # 是否在发型选择界面
        
        # 初始化发色滑块
        self.hair_color_sliders = {
            'R': Slider(0, 0, 200, 20, "R", 255, 0),
            'G': Slider(0, 0, 200, 20, "G", 255, 0),
            'B': Slider(0, 0, 200, 20, "B", 255, 0)
        }
        
        # 初始化发型预览状态
        self.hairstyle_page = 0  # 当前发型页码
        self.hairstyles_per_page = 8  # 每页显示的发型数量
        
        # 初始化地图创建相关属性
        self.map_name_input = ""
        self.map_name_active = False
        self.selected_map_size = self.get_text("medium")  # 默认选择中型地图
        
        # 初始化消息框和弹出框
        self.message_box = None
        self.popup = None
        
        # 初始化角色选择界面的滚动位置
        self.scroll_y = 0
        self.scroll_speed = 30  # 滚动速度
        self.is_dragging = False
        self.drag_start_y = 0
        self.scroll_start = 0
        
        # 初始化按钮
        self.initialize_buttons()

    def initialize_buttons(self):
        """初始化所有按钮"""
        # 根据当前语言设置按钮文本
        menu_texts = [
            self.get_text("start_game"),
            self.get_text("achievements"),  # 新增成就按钮
            self.get_text("settings"),
            self.get_text("credits"),
            self.get_text("quit")
        ]
        
        # 清除现有按钮
        self.menu_buttons = []
        
        # 计算按钮布局
        button_width = int(200 * self.scale_x)
        button_height = int(50 * self.scale_y)
        button_spacing = int(20 * self.scale_y)  # 按钮之间的垂直间距
        
        # 计算所有按钮加间距的总高度
        total_height = len(menu_texts) * button_height + (len(menu_texts) - 1) * button_spacing
        
        # 计算第一个按钮的起始y坐标（垂直居中）
        start_y = (self.screen_height - total_height) // 2
        
        # 创建主菜单按钮
        for i, text in enumerate(menu_texts):
            # 计算每个按钮的y坐标
            button_y = start_y + i * (button_height + button_spacing)
            
            # 创建按钮（水平居中）
            button = SimpleButton(
                self.screen_width//2 - button_width//2,  # 水平居中
                button_y,
                button_width,
                button_height,
                text
            )
            
            # 设置按钮音效
            if hasattr(self, 'hover_sound'):
                button.hover_sound = self.hover_sound
            if hasattr(self, 'click_sound'):
                button.click_sound = self.click_sound
            
            self.menu_buttons.append(button)

    def run(self):
        """游戏主循环"""
        while self.running:
            current_time = pygame.time.get_ticks()
            
            # 检查设置消息是否应该消失
            if hasattr(self, 'settings_message') and self.settings_message:
                if current_time - self.settings_message_time >= 500:  # 0.5秒后消失
                    self.settings_message = None
                    self.settings_message_time = None
                    self.needs_redraw = True
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                
                # 根据游戏状态处理事件
                if self.game_state == "main_menu":
                    self.handle_menu_events(event)
                elif self.game_state == "character_select":
                    self.handle_character_select_events(event)
                elif self.game_state == "character_create":
                    self.handle_character_create_events(event)
                elif self.game_state == "map_select":
                    self.handle_map_select_events(event)
                elif self.game_state == "map_create":
                    self.handle_map_create_events(event)
                elif self.game_state == "playing":
                    self.handle_playing_events(event)
                elif self.game_state == "settings":
                    self.handle_settings_events(event)
                elif self.game_state == "credits":
                    self.handle_credits_events(event)
                
                # 处理鼠标移动事件，更新按钮悬停状态
                if event.type == pygame.MOUSEMOTION:
                    if self.game_state == "main_menu":
                        for button in self.menu_buttons:
                            button.handle_event(event)
                        self.needs_redraw = True
            
            # 根据游戏状态更新和绘制
            if self.needs_redraw:
                if self.game_state == "main_menu":
                    self.draw_menu()
                elif self.game_state == "character_select":
                    self.draw_character_select()
                elif self.game_state == "character_create":
                    self.draw_character_create()
                elif self.game_state == "map_select":
                    self.draw_map_select()
                elif self.game_state == "map_create":
                    self.draw_map_create()
                elif self.game_state == "playing":
                    self.update()
                    self.draw_game()
                elif self.game_state == "settings":
                    self.draw_settings()
                elif self.game_state == "credits":
                    self.draw_credits()
                
                pygame.display.flip()
                self.needs_redraw = False
            
            # 限制帧率
            self.clock.tick(60)
            
            # 更新窗口标题显示FPS
            pygame.display.set_caption(f"幻境世界 - FPS: {int(self.clock.get_fps())}")

    def draw_map_select(self):
        """绘制地图选择界面"""
        # 填充深蓝色背景
        self.buffer.fill((20, 20, 40))  # 深蓝色背景
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render(self.get_text("select_map"), True, (200, 200, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 创建地图列表区域（蓝色半透明面板）
        panel_width = self.screen_width * 0.8
        panel_height = self.screen_height * 0.6
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 120
        
        # 绘制地图列表面板背景
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (50, 50, 120, 200), (0, 0, panel_width, panel_height), border_radius=10)
        self.buffer.blit(panel_surface, (panel_x, panel_y))
        
        # 如果有地图，显示地图信息
        if self.maps:
            for i, map_name in enumerate(self.maps):
                # 读取地图数据
                map_file = os.path.join(self.world_path, f"{map_name}.wld")
                if os.path.exists(map_file):
                    with open(map_file, 'r', encoding='utf-8') as f:
                        map_data = json.load(f)
                    
                    # 创建地图信息条目
                    entry_height = 80
                    entry_y = panel_y + 20 + i * (entry_height + 10)
                    
                    # 绘制条目背景（半透明白色，用于hover效果）
                    entry_surface = pygame.Surface((panel_width - 40, entry_height), pygame.SRCALPHA)
                    pygame.draw.rect(entry_surface, (255, 255, 255, 10), (0, 0, panel_width - 40, entry_height))
                    self.buffer.blit(entry_surface, (panel_x + 20, entry_y))
                    
                    # 绘制地图图标（示例：简单的方形图标）
                    icon_rect = pygame.Rect(panel_x + 20, entry_y + 10, 60, 60)
                    pygame.draw.rect(self.buffer, (100, 100, 150), icon_rect)
                    
                    # 绘制地图信息
                    info_font = get_font(32)
                    # 显示地图名称和大小
                    size_text = "中世界"  # 可以根据地图大小动态设置
                    name_surface = info_font.render(map_name, True, (255, 255, 255))
                    size_surface = info_font.render(size_text, True, (200, 200, 255))
                    create_time = "已创建: 2001/10/12"  # 这里可以从地图数据中获取实际创建时间
                    time_surface = info_font.render(create_time, True, (200, 200, 255))
                    
                    # 绘制文本
                    self.buffer.blit(name_surface, (panel_x + 100, entry_y + 5))
                    self.buffer.blit(size_surface, (panel_x + 100, entry_y + 35))
                    self.buffer.blit(time_surface, (panel_x + panel_width - 300, entry_y + 20))
                    
                    # 绘制分隔线（除了最后一个条目）
                    if i < len(self.maps) - 1:
                        pygame.draw.line(
                            self.buffer,
                            (100, 100, 150, 128),  # 半透明的分隔线颜色
                            (panel_x + 20, entry_y + entry_height + 5),
                            (panel_x + panel_width - 20, entry_y + entry_height + 5),
                            1  # 线的宽度
                        )
        
        # 绘制底部按钮
        button_width = 200
        button_height = 60
        button_y = self.screen_height - 100
        
        # 返回按钮
        self.back_button = MapButton(
            panel_x,
            button_y,
            button_width,
            button_height,
            self.get_text("back"),
            color=(60, 60, 140),
            font_size=36
        )
        
        # 新建按钮
        self.new_map_button = MapButton(
            panel_x + panel_width - button_width,
            button_y,
            button_width,
            button_height,
            self.get_text("create_map"),
            color=(60, 60, 140),
            font_size=36
        )
        
        # 绘制按钮
        self.back_button.draw(self.buffer)
        self.new_map_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_map_select_events(self, event):
        """处理地图选择界面的事件"""
        # 处理鼠标按钮事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event):
                self.game_state = "character_select"
                self.needs_redraw = True
                return True
            
            # 检查新建按钮
            if self.new_map_button.handle_event(event):
                self.game_state = "map_create"  # 切换到地图创建状态
                self.needs_redraw = True
                return True
            
            # 检查地图列表点击
            if self.maps:
                panel_width = self.screen_width * 0.8
                panel_height = self.screen_height * 0.6
                panel_x = (self.screen_width - panel_width) // 2
                panel_y = 120
                
                for i, map_name in enumerate(self.maps):
                    entry_height = 80
                    entry_y = panel_y + 20 + i * (entry_height + 10)
                    entry_rect = pygame.Rect(panel_x + 20, entry_y, panel_width - 40, entry_height)
                    
                    if entry_rect.collidepoint(event.pos):
                        self.selected_map = map_name
                        self.initialize_game()
                        if hasattr(self, 'click_sound') and self.click_sound:
                            self.click_sound.play()
                        return True
        
        # 处理鼠标移动事件
        elif event.type == pygame.MOUSEMOTION:
            # 更新按钮状态
            if self.back_button.handle_event(event) or self.new_map_button.handle_event(event):
                self.needs_redraw = True
        
        # 处理鼠标按钮释放事件
        elif event.type == pygame.MOUSEBUTTONUP:
            # 更新按钮状态
            self.back_button.handle_event(event)
            self.new_map_button.handle_event(event)
        
        return False

    def handle_events(self, event):
        """处理游戏主界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查是否点击了设置按钮
            if hasattr(self, 'settings_button') and self.settings_button.handle_event(event):
                self.game_state = "settings"
                self.needs_redraw = True
                return
            
            # 如果背包可见，检查是否点击了背包槽位
            if hasattr(self, 'inventory') and self.inventory.visible:
                if self.inventory.handle_click(event.pos):
                    self.needs_redraw = True
                    return
                    
            # 左键放置方块，右键破坏方块
            if event.button == 1:  # 左键
                self.place_block(event.pos)
            elif event.button == 3:  # 右键
                self.break_block(event.pos)
                
        # 处理按键事件
        elif event.type == pygame.KEYDOWN:
            # ESC 键打开/关闭背包
            if event.key == pygame.K_ESCAPE:
                if self.game_state == "settings":
                    self.game_state = "playing"
                else:
                    self.inventory.visible = not self.inventory.visible
                self.needs_redraw = True
                return
                
            # 数字键选择物品栏
            elif pygame.K_1 <= event.key <= pygame.K_9:
                self.inventory.selected_slot = event.key - pygame.K_1
                self.needs_redraw = True
            elif event.key == pygame.K_0:
                self.inventory.selected_slot = 9
                self.needs_redraw = True
                
            # F11 切换全屏
            elif event.key == pygame.K_F11:
                self.is_fullscreen = not self.is_fullscreen
                if self.is_fullscreen:
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                self.needs_redraw = True
                return

    def handle_menu_events(self, event):
        """处理主菜单事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.menu_buttons):
                if button.rect.collidepoint(event.pos):
                    if hasattr(self, 'click_sound') and self.click_sound:
                        self.click_sound.play()
                    
                    # 根据按钮索引处理不同的点击事件
                    if i == 0:  # 开始游戏
                        self.game_state = "character_select"
                    elif i == 1:  # 成就按钮
                        self.show_message_box("系统开发中", "成就系统正在开发中，敬请期待！")
                    elif i == 2:  # 设置
                        self.previous_state = "main_menu"
                        self.game_state = "settings"
                    elif i == 3:  # 制作人员
                        self.show_message_box("系统开发中", "制作人员名单正在整理中，敬请期待！")
                    elif i == 4:  # 退出
                        self.running = False
                    
                    self.needs_redraw = True
                    return True
        return False

    def show_message_box(self, title, message):
        """显示消息框"""
        # 保存当前缓冲区
        old_buffer = self.buffer.copy()
        
        # 创建消息框surface
        box_width = int(400 * self.scale_x)
        box_height = int(200 * self.scale_y)
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2
        
        # 创建半透明背景
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # 半透明黑色
        
        # 创建消息框
        message_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(message_box, (40, 40, 60, 255), (0, 0, box_width, box_height))
        pygame.draw.rect(message_box, (184, 134, 11, 255), (0, 0, box_width, box_height), 2)  # 暗金色边框
        
        # 绘制标题
        title_font = get_font(int(36 * min(self.scale_x, self.scale_y)))
        title_surface = title_font.render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(centerx=box_width//2, y=int(20 * self.scale_y))
        message_box.blit(title_surface, title_rect)
        
        # 绘制消息
        message_font = get_font(int(24 * min(self.scale_x, self.scale_y)))
        message_surface = message_font.render(message, True, (200, 200, 200))
        message_rect = message_surface.get_rect(centerx=box_width//2, centery=box_height//2)
        message_box.blit(message_surface, message_rect)
        
        # 创建关闭按钮（×）
        close_size = int(30 * min(self.scale_x, self.scale_y))
        close_x = box_width - close_size - int(10 * self.scale_x)
        close_y = int(10 * self.scale_y)
        
        # 保存关闭按钮的位置（相对于屏幕）
        self.message_box_close_rect = pygame.Rect(
            box_x + close_x,
            box_y + close_y,
            close_size,
            close_size
        )
        
        def draw_message_box(hover=False):
            # 重新绘制整个界面
            self.buffer.blit(old_buffer, (0, 0))
            self.buffer.blit(overlay, (0, 0))
            
            # 绘制关闭按钮
            close_font = get_font(int(24 * min(self.scale_x, self.scale_y)))
            close_text = close_font.render("×", True, (255, 255, 255) if hover else (200, 200, 200))
            close_text_rect = close_text.get_rect(center=(close_x + close_size//2, close_y + close_size//2))
            message_box.blit(close_text, close_text_rect)
            
            # 绘制消息框
            self.buffer.blit(message_box, (box_x, box_y))
            self.screen.blit(self.buffer, (0, 0))
            pygame.display.flip()
        
        # 初始绘制
        draw_message_box(False)
        
        # 等待用户点击关闭按钮
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.message_box_close_rect.collidepoint(event.pos):
                        if hasattr(self, 'click_sound') and self.click_sound:
                            self.click_sound.play()
                        waiting = False
                elif event.type == pygame.MOUSEMOTION:
                    # 更新关闭按钮的悬停效果
                    is_hovering = self.message_box_close_rect.collidepoint(event.pos)
                    draw_message_box(is_hovering)
        
        # 恢复原始缓冲区
        self.buffer = old_buffer
        self.needs_redraw = True

    def draw_character_create(self):
        """绘制角色创建界面"""
        # 清空并填充背景
        self.buffer.fill((0, 20, 50))  # 深蓝色背景
        
        # 如果在发型选择界面，绘制发型选择界面
        if self.in_hairstyle_selection:
            self.draw_hairstyle_selection()
            return
        
        # 创建半透明面板
        panel_width = 1000  # 增加面板宽度
        panel_height = 600  # 增加面板高度
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2
        
        # 绘制标题
        title = self.title_font.render(self.get_text("create_character"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, panel_y - 30))
        self.buffer.blit(title, title_rect)
        
        # 绘制面板背景
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 128))
        self.buffer.blit(panel, (panel_x, panel_y))
        
        # 分割线
        pygame.draw.line(self.buffer, (100, 100, 150), 
                        (panel_x + 700, panel_y + 20),  # 调整分割线位置
                        (panel_x + 700, panel_y + panel_height - 20), 2)
        
        # 绘制输入框和标签
        input_y = panel_y + 40  # 稍微增加顶部间距
        label_x = panel_x + 80  # 标签左移
        input_x = panel_x + 180  # 输入框和按钮左移
        spacing = 80  # 增加垂直间距
        
        # 角色名称输入
        name_label = self.font.render("角色名称:", True, (255, 255, 255))
        self.buffer.blit(name_label, (label_x, input_y))
        
        # 绘制输入框和文本
        pygame.draw.rect(self.buffer, (255, 255, 255) if self.input_active else (150, 150, 150),
                        (input_x, input_y, 200, 30), 2)
        if hasattr(self, 'character_name'):
            name_text = self.font.render(self.character_name, True, (255, 255, 255))
            self.buffer.blit(name_text, (input_x + 5, input_y + 5))
        
        # 如果输入框处于活动状态，绘制光标
        if self.input_active and hasattr(self, 'character_name'):
            cursor_x = input_x + 5 + self.font.size(self.character_name)[0]
            if pygame.time.get_ticks() % 1000 < 500:  # 光标闪烁效果
                pygame.draw.line(self.buffer, (255, 255, 255),
                               (cursor_x, input_y + 5),
                               (cursor_x, input_y + 25), 2)
        
        # 性别选择
        input_y += spacing
        gender_label = self.font.render("性别:", True, (255, 255, 255))
        self.buffer.blit(gender_label, (label_x, input_y))
        
        # 性别按钮
        gender_button_width = 100  # 增加按钮宽度
        gender_spacing = 60  # 增加按钮间距
        for i, gender in enumerate(["男", "女"]):
            button_x = input_x + i * (gender_button_width + gender_spacing)
            button = SimpleButton(
                button_x,
                input_y,
                gender_button_width,
                35,  # 增加按钮高度
                gender,
                color=(240, 240, 255) if self.selected_gender == gender else (220, 220, 240)
            )
            button.draw(self.buffer)
            if gender == "男":
                self.male_button_rect = button.rect
            else:
                self.female_button_rect = button.rect
        
        # 发型选择
        input_y += spacing
        hair_label = self.font.render("发型:", True, (255, 255, 255))
        self.buffer.blit(hair_label, (label_x, input_y))
        
        # 发型按钮
        hair_button = SimpleButton(
            input_x,
            input_y,
            250,  # 增加按钮宽度
            35,   # 增加按钮高度
            "选择发型",
            color=(220, 220, 240)
        )
        hair_button.draw(self.buffer)
        self.hair_button_rect = hair_button.rect
        
        # 体型选择
        input_y += spacing
        body_label = self.font.render("体型:", True, (255, 255, 255))
        self.buffer.blit(body_label, (label_x, input_y))
        
        # 体型按钮
        body_button_width = 100  # 增加按钮宽度
        body_spacing = 50  # 增加按钮间距
        for i, body_type in enumerate(BODY_TYPES):
            button_x = input_x + i * (body_button_width + body_spacing)
            button = SimpleButton(
                button_x,
                input_y,
                body_button_width,
                35,  # 增加按钮高度
                body_type,
                color=(240, 240, 255) if self.selected_body_type == body_type else (220, 220, 240)
            )
            button.draw(self.buffer)
            if i == 0:
                self.thin_button_rect = button.rect
            elif i == 1:
                self.normal_button_rect = button.rect
            else:
                self.fat_button_rect = button.rect
        
        # 职业选择
        input_y += spacing
        class_label = self.font.render("职业:", True, (255, 255, 255))
        self.buffer.blit(class_label, (label_x, input_y))
        
        # 职业按钮
        class_button_width = 90  # 减小按钮宽度
        class_spacing = 40  # 减小按钮间距
        total_width = (class_button_width * len(CLASSES)) + (class_spacing * (len(CLASSES) - 1))
        start_x = input_x  # 起始位置
        
        for i, class_type in enumerate(CLASSES):
            button_x = start_x + i * (class_button_width + class_spacing)
            button = SimpleButton(
                button_x,
                input_y,
                class_button_width,
                35,  # 保持按钮高度
                class_type,
                color=(240, 240, 255) if self.selected_class == class_type else (220, 220, 240)
            )
            button.draw(self.buffer)
            if i == 0:
                self.warrior_button_rect = button.rect
            elif i == 1:
                self.mage_button_rect = button.rect
            elif i == 2:
                self.archer_button_rect = button.rect
            else:
                self.thief_button_rect = button.rect
        
        # 底部按钮
        button_y = panel_y + panel_height - 60  # 调整底部按钮位置
        button_height = 45  # 增加按钮高度
        
        # 返回按钮
        back_button = SimpleButton(
            panel_x + 80,  # 左移
            button_y,
            120,  # 增加按钮宽度
            button_height,
            "返回",
            color=(220, 220, 240)
        )
        back_button.draw(self.buffer)
        self.back_button_rect = back_button.rect
        
        # 创建按钮
        create_button = SimpleButton(
            panel_x + panel_width - 200,  # 调整位置
            button_y,
            120,  # 增加按钮宽度
            button_height,
            "创建",
            color=(220, 240, 220)
        )
        create_button.draw(self.buffer)
        self.create_button_rect = create_button.rect
        
        # 绘制角色预览
        preview_x = panel_x + 750  # 调整预览区域位置
        preview_y = panel_y + 50
        preview_width = 200
        preview_height = 400  # 增加预览区域高度
        
        # 绘制预览区域标题
        preview_title = self.font.render("角色预览", True, (255, 255, 255))
        preview_title_rect = preview_title.get_rect(center=(preview_x + preview_width//2, preview_y - 20))
        self.buffer.blit(preview_title, preview_title_rect)
        
        # 绘制预览区域背景
        pygame.draw.rect(self.buffer, (40, 40, 80), 
                        (preview_x, preview_y, preview_width, preview_height))
        
        # 绘制角色预览
        if hasattr(self, 'selected_gender') and hasattr(self, 'selected_body_type'):
            preview_data = {
                'name': '预览',
                'gender': self.selected_gender,
                'body_type': self.selected_body_type,
                'hairstyle': getattr(self, 'selected_hairstyle', {'style': '1', 'color': (0, 0, 0)}),
                'class': getattr(self, 'selected_class', '战士'),
                'skin_color': (255, 223, 196) if self.selected_gender == '女' else (240, 200, 160),
                'health': 100,
                'mana': 100
            }
            self.draw_character_preview(preview_data, preview_x, preview_y, (preview_width, preview_height))
        
        # 如果有弹出框，绘制弹出框
        if hasattr(self, 'popup') and self.popup and self.popup.visible:
            if not self.popup.should_hide():
                self.buffer.blit(self.popup.surface, self.popup.rect)
            else:
                self.popup = None
                self.needs_redraw = True
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_character_create_events(self, event):
        """处理角色创建界面的事件"""
        if self.in_hairstyle_selection:
            # 处理发型选择界面的事件
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # 检查发型预览网格的点击
                panel_width = 900
                panel_height = 500
                panel_x = (self.screen_width - panel_width) // 2
                panel_y = (self.screen_height - panel_height) // 2
                
                preview_size = (100, 100)
                grid_spacing = 20
                grid_cols = 4
                grid_rows = 2
                start_x = panel_x + (panel_width - (preview_size[0] + grid_spacing) * grid_cols + grid_spacing) // 2
                start_y = panel_y + 50
                
                # 计算当前页的发型范围
                start_index = self.hairstyle_page * (grid_cols * grid_rows)
                end_index = min(start_index + (grid_cols * grid_rows), 20)
                
                # 检查每个发型预览框
                for i in range(start_index, end_index):
                    row = (i - start_index) // grid_cols
                    col = (i - start_index) % grid_cols
                    x = start_x + col * (preview_size[0] + grid_spacing)
                    y = start_y + row * (preview_size[1] + grid_spacing)
                    
                    preview_rect = pygame.Rect(x, y, preview_size[0], preview_size[1])
                    if preview_rect.collidepoint(mouse_pos):
                        if self.click_sound:
                            self.click_sound.play()
                        self.selected_hairstyle = str(i + 1)
                        self.in_hairstyle_selection = False
                        self.needs_redraw = True
                        return True
            return True
        
        # 处理输入框点击
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # 获取输入框位置
            panel_width = 1000
            panel_height = 600
            panel_x = (self.screen_width - panel_width) // 2
            panel_y = (self.screen_height - panel_height) // 2
            input_x = panel_x + 180
            input_y = panel_y + 40
            
            # 检查输入框点击
            input_rect = pygame.Rect(input_x, input_y, 200, 30)
            if input_rect.collidepoint(mouse_pos):
                self.input_active = True
                if not hasattr(self, 'character_name'):
                    self.character_name = ""
                return True
            else:
                self.input_active = False
            
            # 检查发型按钮
            if hasattr(self, 'hair_button_rect') and self.hair_button_rect.collidepoint(mouse_pos):
                if hasattr(self, 'click_sound') and self.click_sound:
                    self.click_sound.play()
                self.in_hairstyle_selection = True
                self.needs_redraw = True
                return True
            
            # 获取所有按钮
            buttons = {
                'male': SimpleButton(self.male_button_rect.x, self.male_button_rect.y, 
                                   self.male_button_rect.width, self.male_button_rect.height, 
                                   "男", color=(240, 240, 255) if self.selected_gender == "男" else (220, 220, 240)),
                'female': SimpleButton(self.female_button_rect.x, self.female_button_rect.y, 
                                     self.female_button_rect.width, self.female_button_rect.height, 
                                     "女", color=(240, 240, 255) if self.selected_gender == "女" else (220, 220, 240)),
                'hair': SimpleButton(self.hair_button_rect.x, self.hair_button_rect.y, 
                                   self.hair_button_rect.width, self.hair_button_rect.height, 
                                   "选择发型", color=(220, 220, 240)),
                'thin': SimpleButton(self.thin_button_rect.x, self.thin_button_rect.y, 
                                   self.thin_button_rect.width, self.thin_button_rect.height, 
                                   "瘦小", color=(240, 240, 255) if self.selected_body_type == "瘦小" else (220, 220, 240)),
                'normal': SimpleButton(self.normal_button_rect.x, self.normal_button_rect.y, 
                                     self.normal_button_rect.width, self.normal_button_rect.height, 
                                     "标准", color=(240, 240, 255) if self.selected_body_type == "标准" else (220, 220, 240)),
                'fat': SimpleButton(self.fat_button_rect.x, self.fat_button_rect.y, 
                                  self.fat_button_rect.width, self.fat_button_rect.height, 
                                  "魁梧", color=(240, 240, 255) if self.selected_body_type == "魁梧" else (220, 220, 240)),
                'warrior': SimpleButton(self.warrior_button_rect.x, self.warrior_button_rect.y, 
                                      self.warrior_button_rect.width, self.warrior_button_rect.height, 
                                      "战士", color=(240, 240, 255) if self.selected_class == "战士" else (220, 220, 240)),
                'mage': SimpleButton(self.mage_button_rect.x, self.mage_button_rect.y, 
                                   self.mage_button_rect.width, self.mage_button_rect.height, 
                                   "法师", color=(240, 240, 255) if self.selected_class == "法师" else (220, 220, 240)),
                'archer': SimpleButton(self.archer_button_rect.x, self.archer_button_rect.y, 
                                     self.archer_button_rect.width, self.archer_button_rect.height, 
                                     "弓箭手", color=(240, 240, 255) if self.selected_class == "弓箭手" else (220, 220, 240)),
                'thief': SimpleButton(self.thief_button_rect.x, self.thief_button_rect.y, 
                                    self.thief_button_rect.width, self.thief_button_rect.height, 
                                    "盗贼", color=(240, 240, 255) if self.selected_class == "盗贼" else (220, 220, 240)),
                'back': SimpleButton(self.back_button_rect.x, self.back_button_rect.y, 
                                   self.back_button_rect.width, self.back_button_rect.height, 
                                   "返回", color=(220, 220, 240)),
                'create': SimpleButton(self.create_button_rect.x, self.create_button_rect.y, 
                                     self.create_button_rect.width, self.create_button_rect.height, 
                                     "创建", color=(220, 240, 220))
            }
            
            # 处理按钮点击
            for button_name, button in buttons.items():
                if button.rect.collidepoint(mouse_pos):
                    if self.click_sound:
                        self.click_sound.play()
                    
                    if button_name == 'male':
                        self.selected_gender = "男"
                        self.needs_redraw = True
                    elif button_name == 'female':
                        self.selected_gender = "女"
                        self.needs_redraw = True
                    elif button_name == 'hair':
                        self.in_hairstyle_selection = True
                        self.needs_redraw = True
                    elif button_name in ['thin', 'normal', 'fat']:
                        self.selected_body_type = {"thin": "瘦小", "normal": "标准", "fat": "魁梧"}[button_name]
                        self.needs_redraw = True
                    elif button_name in ['warrior', 'mage', 'archer', 'thief']:
                        self.selected_class = {"warrior": "战士", "mage": "法师", 
                                            "archer": "弓箭手", "thief": "盗贼"}[button_name]
                        self.needs_redraw = True
                    elif button_name == 'back':
                        self.game_state = "character_select"
                        self.needs_redraw = True
                    elif button_name == 'create':
                        if not hasattr(self, 'character_name') or not self.character_name:
                            self.show_message("请输入角色名称")
                        else:
                            self.create_character()
                    return True
        
        # 处理键盘输入
        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                self.input_active = False
            elif event.key == pygame.K_BACKSPACE:
                if hasattr(self, 'character_name'):
                    self.character_name = self.character_name[:-1]
            else:
                if not hasattr(self, 'character_name'):
                    self.character_name = ""
                if len(self.character_name) < 20 and event.unicode.isprintable():  # 限制名称长度
                    self.character_name += event.unicode
            self.needs_redraw = True
            return True
        
        return False

    def draw_settings(self):
        """绘制设置界面"""
        # 创建一个临时surface来绘制设置界面
        settings_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        # 绘制半透明背景
        settings_surface.fill((0, 0, 0, 180))
        
        # 设置面板尺寸和位置（根据屏幕大小缩放）
        settings_width = int(800 * self.scale_x)
        settings_height = int(600 * self.scale_y)
        settings_x = (self.screen_width - settings_width) // 2
        settings_y = (self.screen_height - settings_height) // 2
        
        # 创建一个surface来绘制所有设置选项
        options_surface = pygame.Surface((settings_width, int(1000 * self.scale_y)), pygame.SRCALPHA)
        
        # 绘制设置面板背景
        pygame.draw.rect(options_surface, (40, 40, 60, 255), (0, 0, settings_width, int(1000 * self.scale_y)))
        pygame.draw.rect(options_surface, (100, 100, 150, 255), (0, 0, settings_width, int(1000 * self.scale_y)), 2)
        
        # 绘制标题
        title_font = get_font(int(48 * min(self.scale_x, self.scale_y)))
        title = title_font.render(self.get_text("settings"), True, (255, 255, 255))
        title_rect = title.get_rect(centerx=settings_width//2, y=int(20 * self.scale_y))
        options_surface.blit(title, title_rect)
        
        # 设置选项的起始位置和间距（根据缩放调整）
        option_x = int(50 * self.scale_x)
        option_y = int(100 * self.scale_y)
        option_spacing = int(80 * self.scale_y)
        font = get_font(int(32 * min(self.scale_x, self.scale_y)))
        
        # 音效音量控制
        sound_text = font.render(f"{self.get_text('sound_volume')}: {int(self.sound_volume * 100)}%", True, (255, 255, 255))
        options_surface.blit(sound_text, (option_x, option_y))
        
        # 音效音量滑块
        slider_width = int(300 * self.scale_x)
        slider_height = int(10 * self.scale_y)
        slider_x = option_x + int(50 * self.scale_x)
        slider_y = option_y + int(50 * self.scale_y)
        pygame.draw.rect(options_surface, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height))
        pygame.draw.rect(options_surface, (200, 200, 200),
                        (slider_x + self.sound_volume * slider_width - int(5 * self.scale_x), 
                         slider_y - int(5 * self.scale_y), 
                         int(10 * self.scale_x), 
                         int(20 * self.scale_y)))
        
        # 音乐音量控制
        option_y += option_spacing
        music_text = font.render(f"{self.get_text('music_volume')}: {int(self.music_volume * 100)}%", True, (255, 255, 255))
        options_surface.blit(music_text, (option_x, option_y))
        
        # 音乐音量滑块
        slider_y = option_y + int(50 * self.scale_y)
        pygame.draw.rect(options_surface, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height))
        pygame.draw.rect(options_surface, (200, 200, 200),
                        (slider_x + self.music_volume * slider_width - int(5 * self.scale_x), 
                         slider_y - int(5 * self.scale_y), 
                         int(10 * self.scale_x), 
                         int(20 * self.scale_y)))
        
        # 图形质量设置
        option_y += option_spacing
        graphics_text = font.render(self.get_text("graphics_quality"), True, (255, 255, 255))
        options_surface.blit(graphics_text, (option_x, option_y))
        
        # 图形质量按钮
        quality_options = ["低", "中", "高"]
        button_width = int(80 * self.scale_x)
        button_spacing = int(20 * self.scale_x)
        total_width = len(quality_options) * button_width + (len(quality_options) - 1) * button_spacing
        start_x = (settings_width - total_width) // 2
        self.quality_buttons = []
        for i, quality in enumerate(quality_options):
            button_x = start_x + i * (button_width + button_spacing)
            button = SettingsButton(
                button_x,
                option_y + int(5 * self.scale_y),
                button_width,
                int(30 * self.scale_y),
                quality,
                is_selected=(self.graphics_quality == quality),
                font_size=int(32 * min(self.scale_x, self.scale_y))
            )
            button.draw(options_surface)
            self.quality_buttons.append(button)
        
        # 分辨率设置
        option_y += option_spacing
        resolution_text = font.render(self.get_text("resolution"), True, (255, 255, 255))
        options_surface.blit(resolution_text, (option_x, option_y))
        
        # 分辨率按钮 - 两行布局
        button_width = int(120 * self.scale_x)
        button_spacing = int(20 * self.scale_x)
        buttons_per_row = 3  # 每行3个按钮
        row_spacing = int(40 * self.scale_y)  # 行间距
        
        # 计算每行的总宽度
        total_width = buttons_per_row * button_width + (buttons_per_row - 1) * button_spacing
        start_x = (settings_width - total_width) // 2
        self.resolution_buttons = []
        
        for i, res in enumerate(self.resolutions):
            row = i // buttons_per_row  # 当前行号
            col = i % buttons_per_row   # 当前列号
            
            button_x = start_x + col * (button_width + button_spacing)
            button_y = option_y + int(40 * self.scale_y) + row * (int(30 * self.scale_y) + row_spacing)
            
            button = SettingsButton(
                button_x,
                button_y,
                button_width,
                int(30 * self.scale_y),
                res,
                is_selected=(self.current_resolution == res),
                font_size=int(32 * min(self.scale_x, self.scale_y))
            )
            button.draw(options_surface)
            self.resolution_buttons.append(button)
        
        # 更新下一个选项的起始位置
        option_y += int(150 * self.scale_y)  # 为两行按钮预留足够空间
        
        # 显示模式设置
        option_y += option_spacing
        display_text = font.render(self.get_text("display_mode"), True, (255, 255, 255))
        options_surface.blit(display_text, (option_x, option_y))
        
        # 显示模式按钮
        button_width = int(150 * self.scale_x)
        button_spacing = int(20 * self.scale_x)
        total_width = len(self.display_modes) * button_width + (len(self.display_modes) - 1) * button_spacing
        start_x = (settings_width - total_width) // 2
        self.display_mode_buttons = []
        for i, mode in enumerate(self.display_modes):
            button_x = start_x + i * (button_width + button_spacing)
            button = SettingsButton(
                button_x,
                option_y + int(5 * self.scale_y),
                button_width,
                int(30 * self.scale_y),
                self.get_text(mode),
                is_selected=(self.display_mode == mode),
                font_size=int(32 * min(self.scale_x, self.scale_y))
            )
            button.draw(options_surface)
            self.display_mode_buttons.append(button)
        
        # 语言设置
        option_y += option_spacing
        language_text = font.render(self.get_text("language"), True, (255, 255, 255))
        options_surface.blit(language_text, (option_x, option_y))
        
        # 语言选择按钮
        languages = ["简体中文", "繁體中文", "日本語", "English"]
        button_width = int(120 * self.scale_x)
        button_spacing = int(20 * self.scale_x)
        total_width = len(languages) * button_width + (len(languages) - 1) * button_spacing
        start_x = (settings_width - total_width) // 2
        self.language_buttons = []
        for i, lang in enumerate(languages):
            button_x = start_x + i * (button_width + button_spacing)
            button = SettingsButton(
                button_x,
                option_y + int(5 * self.scale_y),
                button_width,
                int(30 * self.scale_y),
                lang,
                is_selected=(self.language == lang),
                font_size=int(32 * min(self.scale_x, self.scale_y))
            )
            button.draw(options_surface)
            self.language_buttons.append(button)
        
        # 计算内容总高度和最大滚动距离
        total_content_height = option_y + int(100 * self.scale_y)
        visible_height = settings_height - int(120 * self.scale_y)
        self.settings_max_scroll = max(0, total_content_height - visible_height)
        
        # 确保滚动位置在有效范围内
        self.settings_scroll_y = max(0, min(self.settings_scroll_y, self.settings_max_scroll))
        
        # 创建一个裁剪后的surface
        visible_surface = pygame.Surface((settings_width, settings_height - int(100 * self.scale_y)), pygame.SRCALPHA)
        visible_surface.blit(options_surface, (0, 0), (0, self.settings_scroll_y, settings_width, settings_height - int(100 * self.scale_y)))
        
        # 将裁剪后的surface绘制到主surface上
        settings_surface.blit(visible_surface, (settings_x, settings_y))
        
        # 如果有滚动条
        if self.settings_max_scroll > 0:
            scroll_bar_width = int(10 * self.scale_x)
            scroll_bar_height = ((settings_height - int(100 * self.scale_y)) / total_content_height) * (settings_height - int(100 * self.scale_y))
            scroll_bar_x = settings_x + settings_width - scroll_bar_width - int(5 * self.scale_x)
            scroll_bar_y = settings_y + (self.settings_scroll_y / total_content_height) * (settings_height - int(100 * self.scale_y))
            
            # 绘制滚动条背景
            pygame.draw.rect(settings_surface, (60, 60, 60), 
                           (scroll_bar_x, settings_y, scroll_bar_width, settings_height - int(100 * self.scale_y)))
            # 绘制滚动条
            pygame.draw.rect(settings_surface, (150, 150, 150),
                           (scroll_bar_x, scroll_bar_y, scroll_bar_width, scroll_bar_height))
        
        # 绘制保存和返回按钮（这些按钮不受滚动影响）
        button_width = int(200 * self.scale_x)
        button_height = int(50 * self.scale_y)
        button_y = settings_y + settings_height - int(80 * self.scale_y)
        
        # 返回按钮（居中）
        self.back_button = SimpleButton(
            settings_x + (settings_width - button_width) // 2,  # 居中放置
            button_y,
            button_width,
            button_height,
            self.get_text("back"),
            color=(150, 0, 0),
            font_size=int(32 * min(self.scale_x, self.scale_y))
        )
        
        # 设置按钮的声音
        if hasattr(self, 'hover_sound'):
            self.back_button.hover_sound = self.hover_sound
        if hasattr(self, 'click_sound'):
            self.back_button.click_sound = self.click_sound
        
        # 绘制按钮
        self.back_button.draw(settings_surface)
        
        # 如果有消息需要显示
        if hasattr(self, 'settings_message') and self.settings_message:
            # 创建消息框
            message_font = get_font(int(24 * min(self.scale_x, self.scale_y)))
            message = message_font.render(self.settings_message, True, (255, 255, 255))
            message_rect = message.get_rect(centerx=settings_x + settings_width//2, y=settings_y + settings_height - int(30 * self.scale_y))
            # 绘制半透明背景
            msg_bg = pygame.Surface((message.get_width() + int(20 * self.scale_x), message.get_height() + int(10 * self.scale_y)), pygame.SRCALPHA)
            msg_bg.fill((0, 0, 0, 150))
            settings_surface.blit(msg_bg, (message_rect.x - int(10 * self.scale_x), message_rect.y - int(5 * self.scale_y)))
            settings_surface.blit(message, message_rect)
        
        # 将设置界面绘制到屏幕上
        self.screen.blit(settings_surface, (0, 0))
        pygame.display.flip()

    def handle_settings_events(self, event):
        """处理设置界面的事件"""
        if event.type == pygame.MOUSEWHEEL:
            # 处理滚轮事件
            self.settings_scroll_y -= event.y * 30  # 30是滚动速度
            # 确保滚动位置在有效范围内
            self.settings_scroll_y = max(0, min(self.settings_scroll_y, self.settings_max_scroll))
            self.needs_redraw = True
            return True
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # 获取设置面板的位置和尺寸
            settings_width = int(800 * self.scale_x)
            settings_height = int(600 * self.scale_y)
            settings_x = (self.screen_width - settings_width) // 2
            settings_y = (self.screen_height - settings_height) // 2
            
            # 检查是否点击在可滚动区域内
            scroll_area_rect = pygame.Rect(settings_x, settings_y, settings_width, settings_height - int(100 * self.scale_y))
            if scroll_area_rect.collidepoint(mouse_pos):
                # 调整鼠标位置以考虑滚动和缩放
                adjusted_mouse_pos = (
                    mouse_pos[0] - settings_x,
                    mouse_pos[1] - settings_y + self.settings_scroll_y
                )
                
                # 检查各种按钮
                if hasattr(self, 'quality_buttons'):
                    for button in self.quality_buttons:
                        if button.rect.collidepoint(adjusted_mouse_pos):
                            for btn in self.quality_buttons:
                                btn.is_selected = (btn == button)
                            self.graphics_quality = button.text
                            if hasattr(self, 'click_sound') and self.click_sound:
                                self.click_sound.play()
                            self.save_settings()  # 自动保存设置
                            self.needs_redraw = True
                            return True
                
                if hasattr(self, 'resolution_buttons'):
                    for button in self.resolution_buttons:
                        if button.rect.collidepoint(adjusted_mouse_pos):
                            for btn in self.resolution_buttons:
                                btn.is_selected = (btn == button)
                            self.current_resolution = button.text
                            if hasattr(self, 'click_sound') and self.click_sound:
                                self.click_sound.play()
                            self.apply_display_settings()
                            self.save_settings()  # 自动保存设置
                            self.show_settings_message(self.get_text("resolution_changed"))
                            return True
                
                if hasattr(self, 'display_mode_buttons'):
                    for i, button in enumerate(self.display_mode_buttons):
                        if button.rect.collidepoint(adjusted_mouse_pos):
                            for btn in self.display_mode_buttons:
                                btn.is_selected = (btn == button)
                            old_mode = self.display_mode
                            self.display_mode = self.display_modes[i]
                            
                            # 如果切换到全屏或无边框模式，先保存当前分辨率
                            if self.display_mode in ["fullscreen", "borderless"]:
                                display_info = pygame.display.Info()
                                max_width = display_info.current_w
                                max_height = display_info.current_h
                                current_width, current_height = map(int, self.current_resolution.split('x'))
                                
                                # 如果当前分辨率超过显示器支持的最大分辨率，使用最大分辨率
                                if current_width > max_width or current_height > max_height:
                                    self.current_resolution = f"{max_width}x{max_height}"
                            
                            if hasattr(self, 'click_sound') and self.click_sound:
                                self.click_sound.play()
                            self.apply_display_settings()
                            self.save_settings()  # 自动保存设置
                            return True
                
                if hasattr(self, 'language_buttons'):
                    for button in self.language_buttons:
                        if button.rect.collidepoint(adjusted_mouse_pos):
                            for btn in self.language_buttons:
                                btn.is_selected = (btn == button)
                            self.language = button.text
                            if hasattr(self, 'click_sound') and self.click_sound:
                                self.click_sound.play()
                            self.initialize_buttons()
                            self.save_settings()  # 自动保存设置
                            self.needs_redraw = True
                            return True
            
            # 检查返回按钮
            if hasattr(self, 'back_button') and self.back_button.rect.collidepoint(mouse_pos):
                self.game_state = self.previous_state if hasattr(self, 'previous_state') else "main_menu"
                if hasattr(self, 'click_sound') and self.click_sound:
                    self.click_sound.play()
                self.needs_redraw = True
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            # 获取设置面板的位置
            settings_width = int(800 * self.scale_x)
            settings_x = (self.screen_width - settings_width) // 2
            settings_y = (self.screen_height - int(600 * self.scale_y)) // 2
            
            # 调整鼠标位置以考虑滚动和缩放
            adjusted_mouse_pos = (
                event.pos[0] - settings_x,
                event.pos[1] - settings_y + self.settings_scroll_y
            )
            
            # 更新所有按钮的悬停状态
            for button_group in ['quality_buttons', 'resolution_buttons', 
                               'display_mode_buttons', 'language_buttons']:
                if hasattr(self, button_group):
                    for button in getattr(self, button_group):
                        # 创建一个临时的事件对象
                        temp_event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': adjusted_mouse_pos})
                        button.handle_event(temp_event)
            
            # 返回按钮不需要调整位置
            if hasattr(self, 'back_button'):
                self.back_button.handle_event(event)
        
        return False

    def apply_language_change(self):
        """应用语言更改"""
        # 重新初始化所有按钮和文本
        self.initialize_buttons()
        # 更新设置界面的文本
        if hasattr(self, 'save_button'):
            self.save_button.text = self.get_text("save_settings")
        if hasattr(self, 'back_button'):
            self.back_button.text = self.get_text("back")
        # 标记需要重绘
        self.needs_redraw = True

    def save_settings(self):
        """保存设置到文件"""
        settings = {
            'sound_volume': self.sound_volume,
            'music_volume': self.music_volume,
            'graphics_quality': self.graphics_quality,
            'language': self.language,
            'resolution': self.current_resolution,
            'display_mode': self.display_mode
        }
        
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存设置时出错: {e}")
            self.show_message("保存设置失败")

    def load_characters_and_maps(self):
        """加载角色和地图列表"""
        # 加载角色
        self.characters = []
        try:
            if not os.path.exists(self.player_path):
                os.makedirs(self.player_path)
            for file in os.listdir(self.player_path):
                if file.endswith('.plr'):
                    self.characters.append(file[:-4])  # 移除.plr后缀
            self.characters.sort()  # 按字母顺序排序
        except Exception as e:
            print(f"加载角色时出错: {e}")
            self.characters = []
        
        # 加载地图
        self.maps = []
        try:
            if not os.path.exists(self.world_path):
                os.makedirs(self.world_path)
            for file in os.listdir(self.world_path):
                if file.endswith('.wld'):
                    self.maps.append(file[:-4])  # 移除.wld后缀
            self.maps.sort()  # 按字母顺序排序
        except Exception as e:
            print(f"加载地图时出错: {e}")
            self.maps = []
        
        print(f"已加载角色: {self.characters}")  # 调试信息
        print(f"已加载地图: {self.maps}")  # 调试信息

    def draw_game(self):
        """绘制游戏主界面"""
        # 清空缓冲区
        self.buffer.fill((135, 206, 235))  # 天空蓝色背景
        
        # 绘制世界
        if hasattr(self, 'world'):
            self.world.draw(self.buffer, self.camera_x, self.camera_y)
        
        # 绘制玩家
        if hasattr(self, 'player'):
            self.player.draw(self.buffer, self.camera_x, self.camera_y)
        
        # 绘制背包
        if hasattr(self, 'inventory'):
            if self.inventory.visible:
                self.inventory.draw(self.buffer, get_font(20))
                # 只在背包打开时显示设置按钮
                if hasattr(self, 'settings_button'):
                    self.settings_button.draw(self.buffer)
            self.inventory.draw_hotbar(self.buffer, get_font(20))  # 始终显示物品栏
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        
        # 如果在设置状态，绘制设置界面
        if self.game_state == "settings":
            self.draw_settings()
        
        self.needs_redraw = False

    def draw_menu(self):
        """绘制主菜单"""
        # 清空缓冲区
        self.buffer.fill((0, 0, 0))
        
        # 绘制背景图片
        if hasattr(self, 'menu_background') and self.menu_background:
            # 计算需要的缩放比例，确保图片覆盖整个屏幕
            bg_width = self.menu_background.get_width()
            bg_height = self.menu_background.get_height()
            scale_x = self.screen_width / bg_width
            scale_y = self.screen_height / bg_height
            scale = max(scale_x, scale_y)  # 使用较大的缩放比例以确保覆盖
            
            # 缩放背景图片
            new_width = int(bg_width * scale)
            new_height = int(bg_height * scale)
            scaled_bg = pygame.transform.scale(self.menu_background, (new_width, new_height))
            
            # 计算绘制位置，使图片居中并完全覆盖屏幕
            x = (self.screen_width - new_width) // 2
            y = (self.screen_height - new_height) // 2
            
            # 绘制背景
            self.buffer.blit(scaled_bg, (x, y))
            
            # 添加轻微的暗色遮罩使文字更清晰
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # 半透明黑色遮罩
            self.buffer.blit(overlay, (0, 0))
        
        # 绘制游戏标题
        title_font = get_font(int(64 * min(self.scale_x, self.scale_y)))
        title = title_font.render("幻境世界", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=int(50 * self.scale_y))
        self.buffer.blit(title, title_rect)
        
        # 绘制所有按钮
        for button in self.menu_buttons:
            button.draw(self.buffer)
        
        # 将缓冲区内容绘制到屏幕上
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()

    def draw_character_preview(self, char_data, x, y, preview_size):
        """绘制角色预览"""
        preview_player = Player(x + preview_size[0]//2, y + preview_size[1]//2, char_data)
        preview_player.preview_mode = True
        preview_player.update_appearance()
        
        # 调整预览图像的位置
        preview_rect = preview_player.image.get_rect(center=(x + preview_size[0]//2, y + preview_size[1]//2))
        self.buffer.blit(preview_player.image, preview_rect)

    def draw_character_select(self):
        """绘制角色选择界面"""
        # 清空缓冲区并填充背景
        self.buffer.fill((0, 0, 50))
        
        # 计算面板尺寸和位置
        panel_width = 800
        panel_height = 500
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2  # 修改为垂直居中
        
        # 绘制标题
        title = self.title_font.render(self.get_text("select_character"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, panel_y - 30))
        self.buffer.blit(title, title_rect)
        
        # 创建半透明的面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 128))
        self.buffer.blit(panel, (panel_x, panel_y))
        
        # 创建裁剪区域
        clip_rect = pygame.Rect(panel_x, panel_y, panel_width - 20, panel_height)  # 减去滚动条宽度
        self.buffer.set_clip(clip_rect)
        
        # 显示现有角色（从上到下排列）
        char_spacing_y = 220  # 垂直间距
        start_x = panel_x + 20  # 移到左边
        start_y = panel_y + 30 - self.scroll_y  # 应用滚动偏移
        preview_size = (180, 180)  # 改为方形预览框
        
        # 初始化删除按钮字典
        self.delete_buttons = {}
        
        # 计算内容总高度
        total_height = len(self.characters) * char_spacing_y
        visible_height = panel_height - 60
        
        for i, char_name in enumerate(self.characters):
            y = start_y + i * char_spacing_y
            
            # 只绘制可见区域内的角色
            if panel_y - preview_size[1] <= y <= panel_y + panel_height:
                x = start_x
                
                # 创建预览区域背景
                preview_bg = pygame.Surface(preview_size, pygame.SRCALPHA)
                preview_bg.fill((50, 50, 50, 128))
                self.buffer.blit(preview_bg, (x, y))
                
                # 加载并显示角色预览和信息
                try:
                    character_file = os.path.join(self.player_path, f"{char_name}.plr")
                    with open(character_file, 'r', encoding='utf-8') as f:
                        char_data = json.load(f)
                        # 确保有皮肤颜色属性
                        if 'skin_color' not in char_data:
                            char_data['skin_color'] = (255, 223, 196) if char_data.get('gender') == '女' else (240, 200, 160)
                        
                        # 绘制角色预览
                        self.draw_character_preview(char_data, x, y, preview_size)
                        
                        # 绘制角色信息面板
                        info_x = x + preview_size[0] + 20
                        info_y = y + 10
                        info_spacing = 30  # 增加行间距
                        
                        # 绘制角色名称和职业（并列）
                        name_text = self.font.render(char_name, True, (255, 255, 255))
                        class_text = self.font.render(f"{self.get_text('class')}: {char_data.get('class', '战士')}", True, (200, 200, 100))
                        self.buffer.blit(name_text, (info_x, info_y))
                        self.buffer.blit(class_text, (info_x + 150, info_y))  # 减小偏移量
                        
                        # 绘制生命值和魔法值（并列）
                        max_hp = char_data.get('max_hp', 100)
                        max_mp = char_data.get('max_mp', 100)
                        hp_text = self.font.render(f"{self.get_text('health')}: {max_hp}", True, (255, 100, 100))
                        mp_text = self.font.render(f"{self.get_text('mana')}: {max_mp}", True, (100, 100, 255))
                        self.buffer.blit(hp_text, (info_x, info_y + info_spacing))
                        self.buffer.blit(mp_text, (info_x + 150, info_y + info_spacing))  # 减小偏移量
                        
                        # 绘制游戏时间和删除按钮（同一行）
                        playtime = char_data.get('playtime', 0)
                        hours = playtime // 3600
                        minutes = (playtime % 3600) // 60
                        seconds = playtime % 60
                        time_text = self.font.render(f"{self.get_text('playtime')}: {hours:02d}:{minutes:02d}:{seconds:02d}", True, (200, 200, 200))
                        self.buffer.blit(time_text, (info_x, info_y + info_spacing * 2))
                        
                        # 添加删除按钮（与游戏时间同一行）
                        delete_btn_width = 80
                        delete_btn_height = 30
                        delete_btn_x = panel_x + panel_width - delete_btn_width - 40  # 距离右边界40像素
                        delete_btn_y = info_y + info_spacing * 2  # 与游戏时间同一行
                        
                        # 绘制删除按钮
                        delete_btn = SimpleButton(
                            delete_btn_x,
                            delete_btn_y,
                            delete_btn_width,
                            delete_btn_height,
                            self.get_text("delete"),
                            color=(200, 50, 50),
                            font_size=24
                        )
                        delete_btn.draw(self.buffer)
                        
                        # 存储删除按钮的位置
                        self.delete_buttons[char_name] = pygame.Rect(delete_btn_x, delete_btn_y, delete_btn_width, delete_btn_height)
                        
                        # 如果不是最后一个角色，添加分隔线
                        if i < len(self.characters) - 1:
                            pygame.draw.line(
                                self.buffer,
                                (100, 100, 150),  # 分隔线颜色
                                (panel_x + 20, y + preview_size[1] + 10),  # 起点
                                (panel_x + panel_width - 20, y + preview_size[1] + 10),  # 终点
                                2  # 线宽
                            )
                        
                except Exception as e:
                    print(f"加载角色预览时出错: {e}")
        
        # 重置裁剪区域
        self.buffer.set_clip(None)
        
        # 绘制滚动条
        if total_height > visible_height:
            scroll_bar_width = 16
            scroll_bar_height = max(50, (visible_height / total_height) * visible_height)
            scroll_bar_x = panel_x + panel_width - scroll_bar_width - 4
            scroll_bar_y = panel_y + (self.scroll_y / total_height) * visible_height
            
            # 绘制滚动条背景
            pygame.draw.rect(self.buffer, (50, 50, 50, 128),
                           (scroll_bar_x, panel_y, scroll_bar_width, panel_height))
            
            # 绘制滚动条
            pygame.draw.rect(self.buffer, (150, 150, 150, 200),
                           (scroll_bar_x, scroll_bar_y, scroll_bar_width, scroll_bar_height))
            
            # 存储滚动条区域
            self.scroll_bar_rect = pygame.Rect(scroll_bar_x, scroll_bar_y, scroll_bar_width, scroll_bar_height)
            self.scroll_area_rect = pygame.Rect(scroll_bar_x, panel_y, scroll_bar_width, panel_height)
        
        # 添加新建角色按钮
        new_btn_width = 200
        new_btn_height = 40
        new_btn_x = (self.screen_width - new_btn_width) // 2
        new_btn_y = panel_y + panel_height - 60
        
        new_btn = SimpleButton(
            new_btn_x,
            new_btn_y,
            new_btn_width,
            new_btn_height,
            self.get_text("create_character"),
            color=(0, 150, 0),
            font_size=32
        )
        new_btn.draw(self.buffer)
        
        # 添加返回按钮
        back_btn_width = 100
        back_btn_height = 40
        back_btn_x = panel_x + 50
        back_btn_y = panel_y + panel_height - 60
        
        back_btn = SimpleButton(
            back_btn_x,
            back_btn_y,
            back_btn_width,
            back_btn_height,
            self.get_text("back"),
            color=(100, 100, 200),
            font_size=32
        )
        back_btn.draw(self.buffer)
        
        # 存储按钮位置
        self.new_char_button = pygame.Rect(new_btn_x, new_btn_y, new_btn_width, new_btn_height)
        self.back_button = pygame.Rect(back_btn_x, back_btn_y, back_btn_width, back_btn_height)
        
        # 更新屏幕
        self.screen.blit(self.buffer, (0, 0))
        
        # 如果有确认对话框，绘制它
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
            self.buffer.blit(self.confirm_dialog.surface, self.confirm_dialog.rect)
            self.screen.blit(self.buffer, (0, 0))
        
        pygame.display.flip()
        self.needs_redraw = False

    def handle_character_select_events(self, event):
        """处理角色选择界面的事件"""
        # 如果有确认对话框，优先处理它的事件
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
            if self.confirm_dialog.handle_event(event):
                if self.confirm_dialog.result:
                    # 用户确认删除
                    char_name = self.confirm_dialog.char_name
                    try:
                        os.remove(os.path.join(self.player_path, f"{char_name}.plr"))
                        self.characters.remove(char_name)
                        if hasattr(self, 'click_sound') and self.click_sound:
                            self.click_sound.play()
                    except Exception as e:
                        print(f"删除角色时出错: {e}")
                self.needs_redraw = True
                return True
            return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 只响应左键点击
            mouse_pos = pygame.mouse.get_pos()
            
            # 检查滚动条拖动
            if hasattr(self, 'scroll_bar_rect') and self.scroll_bar_rect.collidepoint(mouse_pos):
                self.is_dragging = True
                self.drag_start_y = mouse_pos[1]
                self.scroll_start = self.scroll_y
                return True
            
            # 检查滚动区域点击
            elif hasattr(self, 'scroll_area_rect') and self.scroll_area_rect.collidepoint(mouse_pos):
                panel_y = (self.screen_height - 500) // 2  # 使用动态计算的panel_y
                visible_height = 500 - 60
                total_height = len(self.characters) * 220
                click_pos = (mouse_pos[1] - panel_y) / visible_height
                self.scroll_y = click_pos * total_height
                self.scroll_y = max(0, min(self.scroll_y, total_height - visible_height))
                self.needs_redraw = True
                return True
            
            # 检查返回按钮点击
            if hasattr(self, 'back_button') and self.back_button.collidepoint(mouse_pos):
                self.game_state = "main_menu"
                if hasattr(self, 'click_sound') and self.click_sound:
                    self.click_sound.play()
                self.needs_redraw = True
                return True
            
            # 检查删除按钮点击
            if hasattr(self, 'delete_buttons'):
                panel_y = (self.screen_height - 500) // 2  # 使用动态计算的panel_y
                start_y = panel_y + 30
                char_spacing_y = 220
                preview_size = (150, 200)
                delete_btn_height = 30
                
                for i, (char_name, delete_rect) in enumerate(self.delete_buttons.items()):
                    # 计算当前角色条目的实际Y坐标（考虑滚动）
                    current_y = start_y + i * char_spacing_y - self.scroll_y
                    
                    # 创建一个新的矩形，使用当前实际位置
                    current_rect = pygame.Rect(
                        delete_rect.x,
                        current_y + preview_size[1] - delete_btn_height - 10,
                        delete_rect.width,
                        delete_rect.height
                    )
                    
                    if current_rect.collidepoint(mouse_pos):
                        # 播放点击音效
                        if hasattr(self, 'click_sound') and self.click_sound:
                            self.click_sound.play()
                        # 显示确认对话框
                        self.show_confirm_dialog(f"{self.get_text('confirm_delete')} {char_name}?")
                        self.confirm_dialog.char_name = char_name
                        return True
            
            # 检查新建角色按钮点击
            if hasattr(self, 'new_char_button') and self.new_char_button.collidepoint(mouse_pos):
                self.game_state = "character_create"
                if hasattr(self, 'click_sound') and self.click_sound:
                    self.click_sound.play()
                self.needs_redraw = True
                return True
            
            # 检查角色选择（垂直布局）
            panel_width = 800
            panel_x = (self.screen_width - panel_width) // 2
            panel_y = (self.screen_height - 500) // 2  # 使用动态计算的panel_y
            preview_size = (150, 200)
            char_spacing_y = 220
            start_x = panel_x + 20  # 与绘制时保持一致
            
            for i, char_name in enumerate(self.characters):
                x = start_x
                y = panel_y + 30 + i * char_spacing_y - self.scroll_y
                # 扩大点击区域以包含角色信息
                char_rect = pygame.Rect(x, y, panel_width - 100, preview_size[1])
                
                if char_rect.collidepoint(mouse_pos):
                    self.selected_character = char_name
                    self.game_state = "map_select"
                    if hasattr(self, 'click_sound') and self.click_sound:
                        self.click_sound.play()
                    self.needs_redraw = True
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键释放
                self.is_dragging = False
            return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                # 计算滚动距离
                delta_y = event.pos[1] - self.drag_start_y
                visible_height = 500 - 60
                total_height = len(self.characters) * 220
                self.scroll_y = self.scroll_start + (delta_y / visible_height) * total_height
                # 限制滚动范围
                self.scroll_y = max(0, min(self.scroll_y, total_height - visible_height))
                self.needs_redraw = True
                return True
        
        elif event.type == pygame.MOUSEWHEEL:
            # 处理鼠标滚轮事件，只用于滚动列表
            self.scroll_y -= event.y * self.scroll_speed
            # 限制滚动范围
            visible_height = 500 - 60
            total_height = len(self.characters) * 220
            self.scroll_y = max(0, min(self.scroll_y, total_height - visible_height))
            self.needs_redraw = True
            return True
        
        return False

    def show_confirm_dialog(self, message):
        """显示确认对话框"""
        dialog_width = 400
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        # 创建一个带有透明度的表面
        dialog = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
        dialog.fill((0, 0, 0, 230))
        
        # 绘制消息
        text = self.font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(dialog_width//2, dialog_height//3))
        dialog.blit(text, text_rect)
        
        # 按钮尺寸和位置
        btn_width = 100
        btn_height = 40
        btn_y = dialog_height - 60
        
        # 确认按钮
        confirm_btn = SimpleButton(
            dialog_width//4 - btn_width//2,
            btn_y,
            btn_width,
            btn_height,
            self.get_text("yes"),
            color=(0, 150, 0),
            font_size=24
        )
        confirm_btn.draw(dialog)
        
        # 取消按钮
        cancel_btn = SimpleButton(
            3*dialog_width//4 - btn_width//2,
            btn_y,
            btn_width,
            btn_height,
            self.get_text("no"),
            color=(200, 50, 50),
            font_size=24
        )
        cancel_btn.draw(dialog)
        
        # 创建确认对话框对象
        class ConfirmDialog:
            def __init__(self, surface, rect, confirm_rect, cancel_rect, message):
                self.surface = surface
                self.rect = rect
                self.confirm_rect = confirm_rect
                self.cancel_rect = cancel_rect
                self.message = message
                self.visible = True
                self.result = None
            
            def handle_event(self, event):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    # 调整鼠标位置到对话框坐标系
                    dialog_mouse_pos = (mouse_pos[0] - self.rect.x, mouse_pos[1] - self.rect.y)
                    if self.confirm_rect.collidepoint(dialog_mouse_pos):
                        self.result = True
                        self.visible = False
                        return True
                    elif self.cancel_rect.collidepoint(dialog_mouse_pos):
                        self.result = False
                        self.visible = False
                        return True
                return False
        
        # 保存确认对话框的按钮位置
        confirm_rect = pygame.Rect(dialog_width//4 - btn_width//2, btn_y, btn_width, btn_height)
        cancel_rect = pygame.Rect(3*dialog_width//4 - btn_width//2, btn_y, btn_width, btn_height)
        
        # 创建并保存确认对话框
        self.confirm_dialog = ConfirmDialog(
            dialog,
            pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height),
            confirm_rect,
            cancel_rect,
            message
        )
        
        # 强制重绘
        self.needs_redraw = True

    def update_camera(self):
        """更新摄像机位置以跟随玩家"""
        if not hasattr(self, 'player') or not hasattr(self, 'world'):
            return
            
        # 计算目标摄像机位置（使玩家保持在屏幕中心）
        target_x = self.player.rect.centerx - self.screen_width // 2
        target_y = self.player.rect.centery - self.screen_height // 2
        
        # 限制摄像机不会超出世界边界
        target_x = max(0, min(target_x, self.world.width * self.world.grid_size - self.screen_width))
        target_y = max(0, min(target_y, self.world.height * self.world.grid_size - self.screen_height))
        
        # 平滑移动摄像机（简单线性插值）
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        # 如果摄像机移动，需要重绘
        if abs(self.camera_x - target_x) > 0.1 or abs(self.camera_y - target_y) > 0.1:
            self.needs_redraw = True

    def save_character(self, name, data):
        """保存角色数据到文件"""
        # 确保目录存在
        os.makedirs(self.player_path, exist_ok=True)
        
        # 保存角色数据
        character_file = os.path.join(self.player_path, f"{name}.plr")
        with open(character_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_maps(self):
        """加载现有的地图"""
        try:
            # 确保世界目录存在
            if not os.path.exists(self.world_path):
                os.makedirs(self.world_path)
                return
            
            # 获取所有地图文件
            self.maps = []
            for entry in os.listdir(self.world_path):
                if os.path.isdir(os.path.join(self.world_path, entry)):
                    self.maps.append(entry)
            
            # 按字母顺序排序地图列表
            self.maps.sort()
        except Exception as e:
            print(f"加载地图时出错: {e}")
            self.maps = []

    def create_new_map(self, width, height, grid_size, map_name):
        """创建新的地图"""
        try:
            # 创建地图目录
            map_dir = os.path.join(self.world_path, map_name)
            if not os.path.exists(map_dir):
                os.makedirs(map_dir)
            
            # 创建地图数据
            map_data = {
                'width': width,
                'height': height,
                'grid_size': grid_size,
                'grid': [[0 for _ in range(width)] for _ in range(height)],  # 初始化为空地图
                'spawn_point': [width // 2, 0]  # 设置出生点在地图中央顶部
            }
            
            # 生成基本地形（示例：在底部生成一些地面）
            ground_height = height - 10
            for x in range(width):
                for y in range(ground_height, height):
                    map_data['grid'][y][x] = 1  # 1 代表地面方块
            
            # 保存地图数据
            with open(os.path.join(map_dir, 'world.json'), 'w', encoding='utf-8') as f:
                json.dump(map_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"创建地图时出错: {e}")

    def generate_terrain(self, grid):
        """生成基础地形"""
        height = len(grid)
        width = len(grid[0])
        
        # 生成基础地形高度
        terrain_height = [height // 2] * width
        for i in range(1, width):
            terrain_height[i] = terrain_height[i-1] + random.randint(-1, 1)
            terrain_height[i] = max(height // 4, min(terrain_height[i], height * 3 // 4))
        
        # 填充地形
        for x in range(width):
            for y in range(height):
                if y > terrain_height[x]:
                    if y > terrain_height[x] + 1:
                        grid[y][x] = 2  # 石头
                    else:
                        grid[y][x] = 1  # 泥土

    def initialize_game(self):
        """初始化游戏，创建世界和玩家"""
        # 加载或创建世界
        if self.selected_map:
            world_file = os.path.join(self.world_path, f"{self.selected_map}.wld")
            if os.path.exists(world_file):
                with open(world_file, 'r', encoding='utf-8') as f:
                    world_data = json.load(f)
                self.world = World(
                    world_data['width'],
                    world_data['height'],
                    world_data['grid_size']
                )
                self.world.grid = world_data['grid']
            else:
                self.show_message(f"找不到地图文件: {world_file}")
                return
        
        # 加载或创建玩家
        if self.selected_character:
            player_file = os.path.join(self.player_path, f"{self.selected_character}.plr")
            if os.path.exists(player_file):
                with open(player_file, 'r', encoding='utf-8') as f:
                    player_data = json.load(f)
                # 创建玩家实例，将其放置在世界中心的地面上
                spawn_x = (self.world.width * self.world.grid_size) // 2
                spawn_y = 0
                for y in range(self.world.height):
                    if self.world.grid[y][spawn_x // self.world.grid_size] != self.world.EMPTY:
                        spawn_y = y * self.world.grid_size - 64  # 64是玩家高度
                        break
                
                # 使用正确的参数创建玩家实例
                self.player = Player(spawn_x, spawn_y, player_data)
            else:
                self.show_message(f"找不到角色文件: {player_file}")
                return
        
        # 初始化摄像机位置
        self.camera_x = 0
        self.camera_y = 0
        
        # 创建物品栏（位置改为左上方）
        inventory_x = 10  # 距离左边界10像素
        inventory_y = 10  # 距离顶部10像素
        self.inventory = Inventory(inventory_x, inventory_y)
        
        self.game_state = "playing"
        self.needs_redraw = True

    def draw_credits(self):
        """绘制制作人员界面"""
        # 清空缓冲区
        self.buffer.fill(SKY_BLUE)
        
        # 绘制标题
        title_font = get_font(64)
        title = title_font.render(self.get_text("credits"), True, WHITE)
        title_rect = title.get_rect(centerx=self.screen_width//2, y=100)
        self.buffer.blit(title, title_rect)
        
        # 制作人员列表
        credits_font = get_font(36)
        credits_list = [
            f"{self.get_text('game_design')}: TrFk{self.get_text('team')}",
            f"{self.get_text('programming')}: TrFk{self.get_text('team')}",
            f"{self.get_text('art_design')}: TrFk{self.get_text('team')}",
            f"{self.get_text('sound_design')}: TrFk{self.get_text('team')}",
            f"{self.get_text('testing_team')}: TrFk{self.get_text('team')}"
        ]
        
        # 绘制制作人员列表
        y_pos = 250
        for credit in credits_list:
            text = credits_font.render(credit, True, WHITE)
            text_rect = text.get_rect(centerx=self.screen_width//2, y=y_pos)
            self.buffer.blit(text, text_rect)
            y_pos += 70
        
        # 绘制返回按钮
        self.back_button = SimpleButton(
            50,
            self.screen_height - 100,
            200,
            60,
            self.get_text("back"),
            color=(200, 100, 0),
            font_size=36
        )
        self.back_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_credits_events(self, event):
        """处理制作人员界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event):
                self.game_state = "main_menu"
                self.needs_redraw = True
                return

    def delete_map(self, map_name):
        """删除指定的地图"""
        map_file = os.path.join(self.world_path, f"{map_name}.wld")
        if os.path.exists(map_file):
            os.remove(map_file)
            self.maps.remove(map_name)
            print(f"已删除地图: {map_name}")
        else:
            print(f"找不到地图文件: {map_name}")

    def show_message(self, message):
        """显示消息框"""
        # 创建消息框
        box_width = 400
        box_height = 200
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2
        
        self.message_box = MessageBox(box_x, box_y, box_width, box_height, message)
        self.needs_redraw = True

    def place_block(self, pos):
        """在指定位置放置方块"""
        if not hasattr(self, 'world') or not hasattr(self, 'inventory'):
            return
            
        # 将屏幕坐标转换为世界坐标
        world_x = pos[0] + int(self.camera_x)
        world_y = pos[1] + int(self.camera_y)
        
        # 将世界坐标转换为网格坐标
        grid_x = int(world_x // self.world.grid_size)
        grid_y = int(world_y // self.world.grid_size)
        
        # 检查坐标是否在世界范围内
        if 0 <= grid_x < self.world.width and 0 <= grid_y < self.world.height:
            # 检查是否有选中的方块
            if self.inventory.selected_slot is not None:
                # 在此处添加放置方块的逻辑
                self.world.grid[grid_y][grid_x] = 1  # 暂时固定放置普通方块
                self.needs_redraw = True
    
    def break_block(self, pos):
        """在指定位置破坏方块"""
        if not hasattr(self, 'world'):
            return
            
        # 将屏幕坐标转换为世界坐标
        world_x = pos[0] + int(self.camera_x)
        world_y = pos[1] + int(self.camera_y)
        
        # 将世界坐标转换为网格坐标
        grid_x = int(world_x // self.world.grid_size)
        grid_y = int(world_y // self.world.grid_size)
        
        # 检查坐标是否在世界范围内
        if 0 <= grid_x < self.world.width and 0 <= grid_y < self.world.height:
            # 检查该位置是否有方块
            if self.world.grid[grid_y][grid_x] != 0:
                # 移除方块
                self.world.grid[grid_y][grid_x] = 0
                self.needs_redraw = True

    def draw_map_create(self):
        """绘制地图创建界面"""
        # 填充深蓝色背景
        self.buffer.fill((20, 20, 40))  # 深蓝色背景
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render(self.get_text("create_world"), True, (200, 200, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 创建地图创建区域（蓝色半透明面板）
        panel_width = self.screen_width * 0.8
        panel_height = self.screen_height * 0.7
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 120
        
        # 绘制面板背景
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (50, 50, 120, 200), (0, 0, panel_width, panel_height), border_radius=10)
        self.buffer.blit(panel_surface, (panel_x, panel_y))
        
        # 绘制地图名称输入框
        name_font = get_font(32)
        name_label = name_font.render(self.get_text("name") + ":", True, (255, 255, 255))
        self.buffer.blit(name_label, (panel_x + 50, panel_y + 30))
        
        # 绘制输入框
        input_rect = pygame.Rect(panel_x + 150, panel_y + 30, 300, 40)
        pygame.draw.rect(self.buffer, (255, 255, 255) if self.map_name_active else (150, 150, 150),
                        input_rect, 2, border_radius=5)
        
        # 绘制输入的文本
        if hasattr(self, 'map_name_input'):
            text_surface = name_font.render(self.map_name_input, True, (255, 255, 255))
            text_rect = text_surface.get_rect(x=input_rect.x + 5, centery=input_rect.centery)
            self.buffer.blit(text_surface, text_rect)
        
        # 绘制地图大小选项
        size_y = panel_y + 100
        size_spacing = 60
        sizes = [self.get_text("small"), self.get_text("medium"), self.get_text("large")]
        descriptions = [
            self.get_text("fast_game_exploration"),
            self.get_text("balanced_gameplay"),
            self.get_text("epic_adventure")
        ]
        grids = ["40x23", "80x45", "120x68"]
        
        for i, (size, desc, grid) in enumerate(zip(sizes, descriptions, grids)):
            # 绘制选项背景
            option_rect = pygame.Rect(panel_x + 50, size_y + i * size_spacing, panel_width - 100, 50)
            if self.selected_map_size == size:
                pygame.draw.rect(self.buffer, (80, 80, 150, 200), option_rect, border_radius=5)
            else:
                pygame.draw.rect(self.buffer, (60, 60, 120, 200), option_rect, border_radius=5)
            
            # 绘制选项文本
            size_text = name_font.render(f"{size} ({grid} {self.get_text('grid')})", True, (255, 255, 255))
            desc_font = get_font(24)
            desc_text = desc_font.render(desc, True, (200, 200, 255))
            
            self.buffer.blit(size_text, (option_rect.x + 20, option_rect.y + 5))
            self.buffer.blit(desc_text, (option_rect.x + 20, option_rect.y + 30))
        
        # 绘制底部按钮
        button_width = 200
        button_height = 60
        button_y = panel_y + panel_height + 20
        
        # 返回按钮
        self.back_button = MapButton(
            panel_x,
            button_y,
            button_width,
            button_height,
            self.get_text("back"),
            color=(60, 60, 140),
            font_size=36
        )
        
        # 创建按钮
        self.create_button = MapButton(
            panel_x + panel_width - button_width,
            button_y,
            button_width,
            button_height,
            self.get_text("create"),
            color=(60, 140, 60),
            font_size=36
        )
        
        # 绘制按钮
        self.back_button.draw(self.buffer)
        self.create_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_map_create_events(self, event):
        """处理地图创建界面的事件"""
        # 处理鼠标按钮事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event):
                self.game_state = "map_select"
                if hasattr(self, 'click_sound') and self.click_sound:
                    self.click_sound.play()
                self.needs_redraw = True
                return True
            
            # 检查创建按钮
            if self.create_button.handle_event(event):
                if not hasattr(self, 'map_name_input') or not self.map_name_input:
                    self.show_message("请输入地图名称")
                    return True
                
                    # 根据选择的大小创建地图
                    if self.selected_map_size == self.get_text("small"):
                        width, height = 40, 23
                    elif self.selected_map_size == self.get_text("medium"):
                        width, height = 80, 45
                    else:
                        width, height = 120, 68
                    
                    # 创建新地图
                    self.create_new_map(width, height, 32, self.map_name_input)
                    # 将新地图添加到列表中
                    self.maps.append(self.map_name_input)
                    # 返回地图选择界面
                    self.game_state = "map_select"
                if hasattr(self, 'click_sound') and self.click_sound:
                    self.click_sound.play()
                    self.needs_redraw = True
                return True
            
            # 检查名称输入框
            panel_width = self.screen_width * 0.8
            panel_x = (self.screen_width - panel_width) // 2
            panel_y = 120
            input_rect = pygame.Rect(panel_x + 150, panel_y + 30, 300, 40)
            self.map_name_active = input_rect.collidepoint(event.pos)
            
            # 检查大小选项按钮
            size_y = panel_y + 100
            size_spacing = 60
            sizes = [self.get_text("small"), self.get_text("medium"), self.get_text("large")]
            
            for i, size in enumerate(sizes):
                option_rect = pygame.Rect(panel_x + 50, size_y + i * size_spacing, panel_width - 100, 50)
                if option_rect.collidepoint(event.pos):
                    self.selected_map_size = size
                    if hasattr(self, 'click_sound') and self.click_sound:
                        self.click_sound.play()
                    self.needs_redraw = True
                    return True
            
        # 处理键盘输入
        elif event.type == pygame.KEYDOWN and self.map_name_active:
            return self.handle_map_name_input(event)
        
        # 处理鼠标移动事件
        elif event.type == pygame.MOUSEMOTION:
            # 更新按钮状态
            if self.back_button.handle_event(event) or self.create_button.handle_event(event):
                self.needs_redraw = True
        
        # 处理鼠标按钮释放事件
        elif event.type == pygame.MOUSEBUTTONUP:
            # 更新按钮状态
            self.back_button.handle_event(event)
            self.create_button.handle_event(event)
        
        return False

    def show_popup(self, message):
        """显示弹出消息"""
        # 创建弹出框
        popup_width = 300
        popup_height = 100
        popup_x = (self.screen_width - popup_width) // 2
        popup_y = (self.screen_height - popup_height) // 2
        
        # 创建一个带有透明度的表面
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        popup_surface.fill((0, 0, 0, 200))  # 半透明黑色背景
        
        # 渲染消息文本
        text = self.font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(popup_width//2, popup_height//2))
        popup_surface.blit(text, text_rect)
        
        # 创建一个简单的弹出框对象
        class PopupBox:
            def __init__(self, surface, rect):
                self.surface = surface
                self.rect = rect
                self.visible = True
                self.creation_time = pygame.time.get_ticks()
                self.duration = 2000  # 显示2秒
            
            def should_hide(self):
                return pygame.time.get_ticks() - self.creation_time > self.duration
        
        # 保存弹出框
        self.popup = PopupBox(popup_surface, pygame.Rect(popup_x, popup_y, popup_width, popup_height))
        self.needs_redraw = True

    def draw_hairstyle_selection(self):
        """绘制发型选择界面"""
        # 清空并填充背景
        self.buffer.fill((0, 20, 50))  # 深蓝色背景
        
        # 绘制标题
        title = self.title_font.render(self.get_text("select_hairstyle"), True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, 50))
        self.buffer.blit(title, title_rect)
        
        # 创建半透明面板
        panel_width = 900
        panel_height = 500
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2  # 修改为垂直居中
        
        # 绘制面板背景
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 128))
        self.buffer.blit(panel, (panel_x, panel_y))
        
        # 发型预览网格
        preview_size = (100, 100)  # 缩小预览框大小
        grid_spacing = 20
        grid_cols = 4  # 每行4个发型
        grid_rows = 2  # 每页2行
        start_x = panel_x + (panel_width - (preview_size[0] + grid_spacing) * grid_cols + grid_spacing) // 2
        start_y = panel_y + 50
        
        # 计算当前页的发型范围
        start_index = self.hairstyle_page * (grid_cols * grid_rows)
        end_index = min(start_index + (grid_cols * grid_rows), 20)  # 最多20种发型
        
        # 绘制发型预览网格
        for i in range(start_index, end_index):
            row = (i - start_index) // grid_cols
            col = (i - start_index) % grid_cols
            x = start_x + col * (preview_size[0] + grid_spacing)
            y = start_y + row * (preview_size[1] + grid_spacing)
            
            # 创建预览框背景
            preview_bg = pygame.Surface(preview_size, pygame.SRCALPHA)
            preview_bg.fill((50, 50, 50, 128))
            if str(i + 1) == self.selected_hairstyle['style']:
                pygame.draw.rect(preview_bg, (100, 100, 200, 128), (0, 0, preview_size[0], preview_size[1]), 3)
            self.buffer.blit(preview_bg, (x, y))
            
            # 创建临时角色数据用于预览
            preview_data = {
                'name': self.get_text("preview"),
                'gender': self.selected_gender,
                'hairstyle': {'style': str(i + 1), 'color': self.selected_hairstyle['color']},
                'body_type': self.get_text("normal"),
                'class': self.get_text("warrior"),
                'skin_color': (255, 220, 180),
                'health': 100,
                'mana': 100
            }
            
            # 绘制发型预览
            preview_player = Player(preview_size[0]//2, preview_size[1]//2, preview_data)
            preview_player.preview_mode = True
            preview_player.update_appearance()
            preview_rect = preview_player.image.get_rect(center=(x + preview_size[0]//2, y + preview_size[1]//2))
            self.buffer.blit(preview_player.image, preview_rect)
        
        # 发色选择（RGB滑块）
        color_y = start_y + (grid_rows * (preview_size[1] + grid_spacing)) + 30  # 发色控制区域的起始y坐标
        
        # 更新滑块位置
        slider_width = 200
        slider_spacing = 40
        slider_x = panel_x + (panel_width - slider_width) // 2
        
        for i, (color, slider) in enumerate(self.hair_color_sliders.items()):
            slider.rect.x = slider_x
            slider.rect.y = color_y + i * slider_spacing
            slider.draw(self.buffer)
            
            # 绘制颜色标签
            label = self.font.render(color, True, (255, 255, 255))
            label_rect = label.get_rect(right=slider.rect.left - 10, centery=slider.rect.centery)
            self.buffer.blit(label, label_rect)
        
        # 绘制翻页按钮
        button_width = 100
        button_height = 40
        button_y = panel_y + panel_height - 60
        
        # 上一页按钮
        prev_button = SimpleButton(
            panel_x + 50,
            button_y,
            button_width,
            button_height,
            self.get_text("prev_page"),
            color=(220, 220, 240)
        )
        prev_button.draw(self.buffer)
        self.prev_btn_rect = prev_button.rect
        
        # 下一页按钮
        next_button = SimpleButton(
            panel_x + panel_width - button_width - 50,
            button_y,
            button_width,
            button_height,
            self.get_text("next_page"),
            color=(220, 220, 240)
        )
        next_button.draw(self.buffer)
        self.next_btn_rect = next_button.rect
        
        # 确认按钮
        confirm_button = SimpleButton(
            panel_x + (panel_width - button_width) // 2,
            button_y,
            button_width,
            button_height,
            self.get_text("confirm"),
            color=(220, 240, 220)
        )
        confirm_button.draw(self.buffer)
        self.confirm_btn_rect = confirm_button.rect
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        self.needs_redraw = False

    def load_settings(self):
        """从文件加载设置"""
        # 默认设置
        self.sound_volume = 0.5
        self.music_volume = 0.5
        self.graphics_quality = "中"
        self.language = "简体中文"
        self.current_resolution = "1280x720"
        self.display_mode = "windowed"
        
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.sound_volume = settings.get('sound_volume', 0.5)
                    self.music_volume = settings.get('music_volume', 0.5)
                    self.graphics_quality = settings.get('graphics_quality', "中")
                    self.language = settings.get('language', "简体中文")
                    self.current_resolution = settings.get('resolution', "1280x720")
                    self.display_mode = settings.get('display_mode', "windowed")
        except Exception as e:
            print(f"加载设置时出错: {e}")

    def show_settings_message(self, message):
        """在设置界面显示消息"""
        self.settings_message = message
        self.settings_message_time = pygame.time.get_ticks()
        self.needs_redraw = True

    def get_text(self, key):
        """获取当前语言的文本"""
        if not hasattr(self, 'language'):
            self.language = "简体中文"
        return self.translations[self.language].get(key, key)

    def apply_display_settings(self):
        """应用显示设置"""
        # 获取当前显示器信息
        display_info = pygame.display.Info()
        
        # 设置新的分辨率
        if self.display_mode in ["fullscreen", "borderless"]:
            # 获取当前选择的分辨率
            width, height = map(int, self.current_resolution.split('x'))
            
            # 如果是全屏或无边框模式，使用当前选择的分辨率
            # 不再强制使用最大分辨率
            self.screen_width = width
            self.screen_height = height
        else:
            # 窗口模式使用选择的分辨率
            width, height = map(int, self.current_resolution.split('x'))
            self.screen_width = width
            self.screen_height = height
        
        # 更新缩放比例
        self.scale_x = width / 1280  # 基准分辨率宽度
        self.scale_y = height / 720  # 基准分辨率高度
        
        # 设置显示模式
        if self.display_mode == "fullscreen":
            self.screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        elif self.display_mode == "borderless":
            # 在Windows上，无边框模式需要特殊处理以确保全屏
            if os.name == 'nt':
                self.screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
            else:
                self.screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
        else:  # windowed
            # 使用默认标志（带边框的窗口模式）
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            
            # 在窗口模式下，将窗口居中显示
            if os.name == 'nt':  # Windows系统
                import ctypes
                hwnd = pygame.display.get_wm_info()['window']
                # 获取屏幕尺寸
                user32 = ctypes.windll.user32
                screen_width = user32.GetSystemMetrics(0)
                screen_height = user32.GetSystemMetrics(1)
                # 计算窗口位置使其居中
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                # 设置窗口位置
                user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001)
            else:  # 其他系统
                # 对于其他系统，可以尝试使用 SDL 的方法设置窗口位置
                os.environ['SDL_VIDEO_CENTERED'] = '1'
        
        # 重新创建缓冲区以匹配新的分辨率
        self.buffer = pygame.Surface((width, height))
        
        # 重新初始化按钮以适应新的分辨率
        self.initialize_buttons()
        
        # 标记需要重绘
        self.needs_redraw = True

    def create_character(self):
        """创建新角色"""
        # 创建角色数据
        character_data = {
            'name': self.character_name,
            'gender': self.selected_gender,
            'hairstyle': self.selected_hairstyle,
            'body_type': self.selected_body_type,
            'class': self.selected_class,
            'health': 100,
            'mana': 100,
            'inventory': []
        }
        # 保存角色
        self.save_character(self.character_name, character_data)
        # 返回角色选择界面
        self.game_state = "character_select"
        self.load_characters_and_maps()  # 重新加载角色列表
        if self.click_sound:
            self.click_sound.play()
        self.needs_redraw = True

    def handle_map_name_input(self, event):
        """处理地图名称的键盘输入"""
        if event.key == pygame.K_RETURN:
            self.map_name_active = False
            self.needs_redraw = True
            return True
        
        if event.key == pygame.K_BACKSPACE:
            if hasattr(self, 'map_name_input') and self.map_name_input:
                self.map_name_input = self.map_name_input[:-1]
                self.needs_redraw = True
            return True
        
        if event.unicode.isprintable():
            if not hasattr(self, 'map_name_input'):
                self.map_name_input = ""
            if len(self.map_name_input) < 20:  # 限制名称长度
                self.map_name_input += event.unicode
                self.needs_redraw = True
            return True
        
        return False

class SettingsButton(SimpleButton):
    def __init__(self, x, y, width, height, text, color=(200, 200, 220), font_size=32, is_selected=False):
        super().__init__(x, y, width, height, text, color, font_size)
        self.is_selected = is_selected
        self.base_color = color
        self.original_y = y  # 保存原始y坐标
    
    def draw(self, screen):
        # 根据选中状态决定颜色
        if self.is_selected:
            current_color = (100, 150, 200)  # 选中时的蓝色
        else:
            current_color = (60, 60, 140)  # 未选中时的深蓝色
            if self.is_hovered:
                current_color = tuple(min(255, c + 30) for c in current_color)  # 悬停时略微变亮
        
        # 绘制按钮背景
        pygame.draw.rect(screen, current_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=5)  # 添加白色边框
        
        # 绘制文本
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update_position(self, scroll_y):
        """更新按钮位置以适应滚动"""
        self.rect.y = self.original_y - scroll_y

class MapButton:
    def __init__(self, x, y, width, height, text, color=(60, 60, 140), font_size=36):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = get_font(font_size)
        self.color = color
        self.hovered = False
        self.is_clicked = False
        
        # 加载音效
        self.hover_sound = None
        self.click_sound = None
        try:
            self.hover_sound = pygame.mixer.Sound("assets/sounds/ui/hover.wav")
            self.hover_sound.set_volume(0.15)
            
            self.click_sound = pygame.mixer.Sound("assets/sounds/ui/click.wav")
            self.click_sound.set_volume(0.3)
        except Exception as e:
            print(f"Warning: Could not load button sounds: {e}")
    
    def draw(self, screen):
        # 根据悬停和点击状态确定颜色
        current_color = self.color
        if self.is_clicked:
            current_color = tuple(max(0, c - 30) for c in self.color)
        elif self.hovered:
            current_color = tuple(min(255, c + 30) for c in self.color)
        
        # 绘制圆角矩形
        pygame.draw.rect(screen, current_color, self.rect, border_radius=10)
        
        # 绘制边框
        border_color = (255, 215, 0) if self.hovered else (218, 165, 32)
        border_width = 3 if self.hovered else 2
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=10)
        
        # 绘制文本
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        """处理按钮事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_clicked = True
                if self.click_sound:
                    self.click_sound.play()
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_clicked = self.is_clicked
            self.is_clicked = False
            if was_clicked and self.rect.collidepoint(event.pos):
                return True
        elif event.type == pygame.MOUSEMOTION:
            previous_hover = self.hovered
            self.hovered = self.rect.collidepoint(event.pos)
            if not previous_hover and self.hovered and self.hover_sound:
                self.hover_sound.play()
        return False

if __name__ == "__main__":
    game = Game()
    game.run()