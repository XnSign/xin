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

# 职业选项
CLASSES = ["战士", "法师", "弓箭手", "盗贼"]

# 发型选项
HAIRSTYLES = ["短发", "长发", "马尾", "双马尾", "波波头", "蓬松卷发", "直发", "莫西干", "寸头", "板寸", 
             "爆炸头", "辫子", "丸子头", "中分", "偏分", "飞机头", "锅盖头", "脏辫", "编织辫", "秃头"]

# 体型选项
BODY_TYPES = ["瘦小", "标准", "魁梧"]

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
LIGHT_GRAY = (200, 200, 200)
LIGHT_RED = (255, 100, 100)
DARK_GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)

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
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = get_font(font_size)  # 使用font_size参数创建字体
        self.color = color
        self.is_hovered = False
        self.is_clicked = False
        
    def draw(self, screen):
        # 根据悬停和点击状态确定颜色
        current_color = self.color
        if self.is_clicked:
            # 点击时颜色变暗
            current_color = tuple(max(0, c - 50) for c in self.color)
        elif self.is_hovered:
            # 悬停时颜色变亮
            current_color = tuple(min(255, c + 30) for c in self.color)
            
        # 绘制按钮背景
        pygame.draw.rect(screen, current_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=5)  # 白色边框
        
        # 绘制文本
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        # 只处理鼠标按下和抬起事件，忽略滚轮事件
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 只响应左键点击
            if self.rect.collidepoint(event.pos):
                self.is_clicked = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_clicked = self.is_clicked
            self.is_clicked = False
            if self.rect.collidepoint(event.pos) and was_clicked:
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        return False

class Slider:
    def __init__(self, x, y, width, height, label, max_value, initial_value=128):
        """初始化滑块"""
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.max_value = max_value
        self.value = initial_value
        self.dragging = False
        
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
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and event.buttons[0]:  # 左键拖动
                # 更新值
                self.value = (event.pos[0] - self.rect.x) / self.rect.width * self.max_value
                self.value = max(0, min(self.max_value, self.value))
                return True
        return False
        
    def draw(self, screen):
        """绘制滑块"""
        # 绘制滑块背景
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        
        # 绘制滑块当前值
        value_rect = pygame.Rect(
            self.rect.x,
            self.rect.y,
            self.rect.width * (self.value / self.max_value),
            self.rect.height
        )
        pygame.draw.rect(screen, (200, 200, 200), value_rect)
        
        # 绘制边框
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 2)
        
        # 绘制标签
        font = get_font(24)
        label = font.render(f"{self.label}: {int(self.value)}", True, (255, 255, 255))
        screen.blit(label, (self.rect.x - 100, self.rect.y))

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
        # 绘制背景
        pygame.draw.rect(screen, (50, 50, 50), self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("创建角色", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.rect.centerx, y=self.rect.y + 20)
        screen.blit(title, title_rect)
        
        # 绘制名称输入框
        name_font = get_font(32)
        name_text = name_font.render("角色名称:", True, (255, 255, 255))
        screen.blit(name_text, (self.rect.x + 50, self.rect.y + 100))
        
        name_rect = pygame.Rect(self.rect.x + 50, self.rect.y + 150, 300, 40)
        pygame.draw.rect(screen, (60, 60, 60) if self.name_active else (40, 40, 40), name_rect)
        pygame.draw.rect(screen, (255, 255, 255), name_rect, 2)
        
        # 绘制名称文本
        display_text = self.name if self.name else ""
        cursor = "_" if self.name_active and pygame.time.get_ticks() % 1000 < 500 else ""
        name_surface = name_font.render(display_text + cursor, True, (255, 255, 255))
        screen.blit(name_surface, (name_rect.x + 10, name_rect.y + 5))
        
        # 绘制发型选择
        hairstyle_text = name_font.render(f"发型: {HAIRSTYLES[self.hairstyle_index]}", True, (255, 255, 255))
        text_rect = hairstyle_text.get_rect(midright=(self.rect.centerx - 20, self.rect.y + 220))
        screen.blit(hairstyle_text, text_rect)
        self.hairstyle_prev.draw(screen)
        self.hairstyle_next.draw(screen)
        
        # 绘制肤色滑动条
        color_text = name_font.render("肤色:", True, (255, 255, 255))
        screen.blit(color_text, (self.rect.x + 50, self.rect.y + 270))
        for slider in self.color_sliders:
            slider.draw(screen)
        
        # 绘制角色预览
        preview_rect = pygame.Rect(self.rect.right - 250, self.rect.y + 100, 200, 300)
        pygame.draw.rect(screen, (30, 30, 30), preview_rect)
        pygame.draw.rect(screen, (100, 100, 100), preview_rect, 2)
        
        # 绘制确认和取消按钮
        self.confirm_button.draw(screen)
        self.cancel_button.draw(screen)

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
        self.close_button = SimpleButton(
            x + width - 40,
            y + 10,
            30,
            30,
            "×",
            color=(200, 0, 0),
            font_size=24
        )
        
    def draw(self, surface):
        if not self.visible:
            return
            
        # 绘制半透明背景
        overlay = pygame.Surface((surface.get_width(), surface.get_height()))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        surface.blit(overlay, (0, 0))
        
        # 绘制消息框背景
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        
        # 绘制消息文本
        text = self.font.render(self.message, True, (255, 255, 255))
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)
        
        # 绘制关闭按钮
        self.close_button.draw(surface)
        
    def handle_event(self, event):
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.close_button.rect.collidepoint(event.pos):
                self.visible = False
                return True
        return False

class Game:
    def __init__(self):
        """初始化游戏"""
        pygame.init()
        pygame.mixer.init()  # 初始化音频系统
        
        # 设置窗口
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("TrFk")
        
        # 创建缓冲区
        self.buffer = pygame.Surface((self.screen_width, self.screen_height))
        
        # 初始化时钟
        self.clock = pygame.time.Clock()
        
        # 游戏状态
        self.running = True
        self.game_state = "main_menu"
        self.needs_redraw = True
        
        # 加载字体
        self.title_font = get_font(48)
        self.font = get_font(24)
        self.small_font = get_font(16)
        
        # 设置路径
        self.player_path = "players"
        self.world_path = "worlds"
        os.makedirs(self.player_path, exist_ok=True)
        os.makedirs(self.world_path, exist_ok=True)
        
        # 加载音效
        try:
            self.click_sound = pygame.mixer.Sound("assets/sounds/click.wav")
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
        self.selected_hairstyle = "黑色_短发"
        self.selected_body_type = "普通"
        self.selected_class = "战士"
        
        # 初始化地图创建相关属性
        self.map_name_input = ""
        self.map_name_active = False
        self.selected_map_size = "中型"  # 默认选择中型地图
        
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
        # 主菜单按钮
        button_width = 300
        button_height = 50
        button_x = self.screen_width//2 - button_width//2
        button_y_start = 200
        button_spacing = 60
        
        self.menu_buttons = {}
        button_colors = {
            '单人模式': (0, 200, 0),
            '多人模式': (0, 150, 200),
            '成就': (200, 150, 0),
            '创意工坊': (150, 150, 150),
            '设置': (100, 100, 200),
            '制作人员': (200, 100, 100),
            '退出': (200, 50, 50)
        }
        
        for i, (key, color) in enumerate(button_colors.items()):
            self.menu_buttons[key] = SimpleButton(
                button_x,
                button_y_start + i * button_spacing,
                button_width,
                button_height,
                key,
                color=color,
                font_size=36
            )

    def run(self):
        """游戏主循环"""
        while self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                
                # 根据游戏状态处理事件
                event_handled = False
                if self.game_state == "main_menu":
                    event_handled = self.handle_menu_events(event)
                elif self.game_state == "character_select":
                    event_handled = self.handle_character_select_events(event)
                elif self.game_state == "character_create":
                    event_handled = self.handle_character_create_events(event)
                elif self.game_state == "map_select":
                    event_handled = self.handle_map_select_events(event)
                elif self.game_state == "map_create":
                    event_handled = self.handle_map_create_events(event)
                elif self.game_state == "playing":
                    event_handled = self.handle_playing_events(event)
            
            # 根据游戏状态更新和绘制
            current_state = self.game_state  # 保存当前状态
            
            if self.needs_redraw:
                if current_state == "main_menu":
                    self.draw_menu()
                elif current_state == "character_select":
                    self.draw_character_select()
                elif current_state == "character_create":
                    self.draw_character_create()
                elif current_state == "map_select":
                    self.draw_map_select()
                elif current_state == "map_create":
                    self.draw_map_create()
                elif current_state == "playing":
                    self.update()
                    self.draw_game()
                
                # 确保缓冲区内容被复制到屏幕
                self.screen.blit(self.buffer, (0, 0))
                pygame.display.flip()
                
                # 只有在状态没有改变的情况下才重置重绘标志
                if current_state == self.game_state:
                    self.needs_redraw = False
            
            # 限制帧率
            self.clock.tick(60)
            
            # 更新窗口标题显示FPS
            pygame.display.set_caption(f"TrFk - FPS: {int(self.clock.get_fps())}")

    def draw_map_select(self):
        """绘制地图选择界面"""
        # 填充深蓝色背景
        self.buffer.fill((20, 20, 40))  # 深蓝色背景
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("选择世界", True, (200, 200, 255))
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
        self.back_button = SimpleButton(
            panel_x,
            button_y,
            button_width,
            button_height,
            "返回",
            color=(60, 60, 140),
            font_size=36
        )
        
        # 新建按钮
        self.new_map_button = SimpleButton(
            panel_x + panel_width - button_width,
            button_y,
            button_width,
            button_height,
            "新建",
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
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event):
                self.game_state = "character_select"
                self.needs_redraw = True
                return
            
            # 检查新建按钮
            if self.new_map_button.handle_event(event):
                self.game_state = "map_create"  # 切换到地图创建状态
                self.needs_redraw = True
                return
            
            # 检查地图列表点击
            if self.maps:
                panel_width = self.screen_width * 0.8
                panel_height = self.screen_height * 0.6
                panel_x = (self.screen_width - panel_width) // 2
                panel_y = 120
                
                # 计算鼠标点击位置
                mouse_pos = event.pos
                
                for i, map_name in enumerate(self.maps):
                    entry_height = 80
                    entry_y = panel_y + 20 + i * (entry_height + 10)
                    entry_rect = pygame.Rect(panel_x, entry_y, panel_width, entry_height)
                    
                    if entry_rect.collidepoint(mouse_pos):
                        self.selected_map = map_name
                        self.initialize_game()
                        return

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
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查是否点击了任何按钮
            for key, button in self.menu_buttons.items():
                if button.handle_event(event):
                    print(f"点击了按钮: {key}")  # 调试信息
                    if key == '单人模式':
                        print("切换到角色选择界面")  # 调试信息
                        self.game_state = "character_select"
                        self.load_characters_and_maps()  # 重新加载角色列表
                        self.needs_redraw = True  # 确保重绘
                        if hasattr(self, 'click_sound') and self.click_sound:
                            self.click_sound.play()
                        return True
                    elif key == '多人模式':
                        self.show_message("多人模式正在开发中...")
                    elif key == '成就':
                        self.show_message("成就系统正在开发中...")
                    elif key == '创意工坊':
                        self.show_message("创意工坊正在开发中...")
                    elif key == '设置':
                        self.game_state = "settings"
                    elif key == '制作人员':
                        self.game_state = "credits"
                    elif key == '退出':
                        self.running = False
                    
                    if hasattr(self, 'click_sound') and self.click_sound:
                        self.click_sound.play()
                    self.needs_redraw = True
                    return True
        return False

    def draw_character_create(self):
        """绘制角色创建界面"""
        # 清空并填充背景
        self.buffer.fill((0, 20, 50))  # 深蓝色背景
        
        # 绘制标题
        title = self.title_font.render("创建角色", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, 50))
        self.buffer.blit(title, title_rect)
        
        # 创建半透明面板
        panel_width = 900  # 增加面板宽度以容纳预览区域
        panel_height = 500
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 100
        
        # 绘制面板背景
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 128))
        self.buffer.blit(panel, (panel_x, panel_y))
        
        # 分割线
        pygame.draw.line(self.buffer, (100, 100, 150), 
                        (panel_x + 600, panel_y + 20),
                        (panel_x + 600, panel_y + panel_height - 20), 2)
        
        # 绘制输入框和标签
        input_y = panel_y + 30
        label_x = panel_x + 50
        input_x = panel_x + 200
        spacing = 60
        
        # 角色名称输入
        name_label = self.font.render("角色名称:", True, (255, 255, 255))
        self.buffer.blit(name_label, (label_x, input_y))
        
        # 绘制输入框
        pygame.draw.rect(self.buffer, (255, 255, 255) if self.input_active else (150, 150, 150),
                        (input_x, input_y, 200, 30), 2)
        name_text = self.font.render(self.character_name, True, (255, 255, 255))
        self.buffer.blit(name_text, (input_x + 5, input_y))
        
        # 性别选择
        input_y += spacing
        gender_label = self.font.render("性别:", True, (255, 255, 255))
        self.buffer.blit(gender_label, (label_x, input_y))
        
        # 性别按钮
        gender_button_width = 80
        gender_spacing = 20
        for i, gender in enumerate(['男', '女']):
            button_x = input_x + i * (gender_button_width + gender_spacing)
            button_color = (100, 100, 200) if self.selected_gender == gender else (60, 60, 140)
            # 绘制按钮背景
            pygame.draw.rect(self.buffer, button_color, 
                           (button_x, input_y, gender_button_width, 30), border_radius=5)
            # 绘制按钮边框
            pygame.draw.rect(self.buffer, (255, 255, 255),
                           (button_x, input_y, gender_button_width, 30), 1, border_radius=5)
            # 绘制按钮文本
            gender_text = self.font.render(gender, True, (255, 255, 255))
            text_rect = gender_text.get_rect(center=(button_x + gender_button_width//2, input_y + 15))
            self.buffer.blit(gender_text, text_rect)
        
        # 发型选择
        input_y += spacing
        hair_label = self.font.render("发型:", True, (255, 255, 255))
        self.buffer.blit(hair_label, (label_x, input_y))
        
        # 发型按钮
        hair_button_width = 100
        hair_spacing = 10
        hair_styles = ["金色_短发", "褐色_短发", "黑色_短发", "金色_长发", "褐色_长发", "黑色_长发"]
        for i, style in enumerate(hair_styles):
            row = i // 3
            col = i % 3
            button_x = input_x + col * (hair_button_width + hair_spacing)
            button_y = input_y + row * 35
            button_color = (100, 100, 200) if self.selected_hairstyle == style else (60, 60, 140)
            pygame.draw.rect(self.buffer, button_color,
                           (button_x, button_y, hair_button_width, 30), border_radius=5)
            style_text = self.small_font.render(style.split('_')[0], True, (255, 255, 255))
            text_rect = style_text.get_rect(center=(button_x + hair_button_width//2, button_y + 15))
            self.buffer.blit(style_text, text_rect)
        
        # 体型选择
        input_y += spacing + 35
        body_label = self.font.render("体型:", True, (255, 255, 255))
        self.buffer.blit(body_label, (label_x, input_y))
        
        # 体型按钮
        body_button_width = 80
        body_spacing = 10
        body_types = ["瘦小", "普通", "魁梧"]
        for i, body_type in enumerate(body_types):
            button_x = input_x + i * (body_button_width + body_spacing)
            button_color = (100, 100, 200) if self.selected_body_type == body_type else (60, 60, 140)
            pygame.draw.rect(self.buffer, button_color,
                           (button_x, input_y, body_button_width, 30), border_radius=5)
            type_text = self.font.render(body_type, True, (255, 255, 255))
            text_rect = type_text.get_rect(center=(button_x + body_button_width//2, input_y + 15))
            self.buffer.blit(type_text, text_rect)
        
        # 职业选择
        input_y += spacing
        class_label = self.font.render("职业:", True, (255, 255, 255))
        self.buffer.blit(class_label, (label_x, input_y))
        
        # 职业按钮
        class_button_width = 80
        class_spacing = 10
        class_types = ["战士", "法师", "弓箭手"]
        for i, class_type in enumerate(class_types):
            button_x = input_x + i * (class_button_width + class_spacing)
            button_color = (100, 100, 200) if self.selected_class == class_type else (60, 60, 140)
            pygame.draw.rect(self.buffer, button_color,
                           (button_x, input_y, class_button_width, 30), border_radius=5)
            class_text = self.font.render(class_type, True, (255, 255, 255))
            text_rect = class_text.get_rect(center=(button_x + class_button_width//2, input_y + 15))
            self.buffer.blit(class_text, text_rect)
        
        # 绘制角色预览
        preview_x = panel_x + 650  # 预览区域的x坐标
        preview_y = panel_y + 50   # 预览区域的y坐标
        preview_width = 200        # 预览区域的宽度
        preview_height = 300       # 预览区域的高度
        
        # 绘制预览区域标题
        preview_title = self.font.render("角色预览", True, (255, 255, 255))
        preview_title_rect = preview_title.get_rect(center=(preview_x + preview_width//2, preview_y - 20))
        self.buffer.blit(preview_title, preview_title_rect)
        
        # 绘制预览区域背景
        pygame.draw.rect(self.buffer, (40, 40, 80), 
                        (preview_x, preview_y, preview_width, preview_height))
        pygame.draw.rect(self.buffer, (100, 100, 150),
                        (preview_x, preview_y, preview_width, preview_height), 2)
        
        # 绘制角色预览
        character_x = preview_x + preview_width // 2
        character_y = preview_y + preview_height // 2
        
        # 根据选择的体型调整大小
        if self.selected_body_type == "瘦小":
            body_width, body_height = 30, 60
        elif self.selected_body_type == "普通":
            body_width, body_height = 40, 70
        else:  # 魁梧
            body_width, body_height = 50, 80
        
        # 绘制身体
        body_color = (255, 220, 180)  # 肤色
        pygame.draw.ellipse(self.buffer, body_color,
                          (character_x - body_width//2,
                           character_y - body_height//2,
                           body_width, body_height))
        
        # 绘制头部
        head_size = body_width * 1.2
        pygame.draw.circle(self.buffer, body_color,
                         (character_x,
                          character_y - body_height//2 - head_size//2),
                         head_size//2)
        
        # 绘制发型
        hair_color = {
            "金色": (255, 215, 0),
            "褐色": (139, 69, 19),
            "黑色": (0, 0, 0)
        }[self.selected_hairstyle.split('_')[0]]
        
        if self.selected_hairstyle.endswith("短发"):
            pygame.draw.circle(self.buffer, hair_color,
                             (character_x,
                              character_y - body_height//2 - head_size//2),
                             head_size//2 + 2)
        else:  # 长发
            pygame.draw.ellipse(self.buffer, hair_color,
                              (character_x - head_size//2 - 5,
                               character_y - body_height//2 - head_size//2 - 5,
                               head_size + 10,
                               head_size * 1.5))
        
        # 根据职业添加装备
        if self.selected_class == "战士":
            # 绘制剑和盾牌
            pygame.draw.rect(self.buffer, (192, 192, 192),
                           (character_x + body_width//2,
                            character_y - body_height//4,
                            40, 8))  # 剑
            pygame.draw.circle(self.buffer, (139, 69, 19),
                             (character_x - body_width//2 - 15,
                              character_y),
                             15)  # 盾
        elif self.selected_class == "法师":
            # 绘制法杖
            pygame.draw.rect(self.buffer, (139, 69, 19),
                           (character_x + body_width//2,
                            character_y - body_height//2,
                            8, 60))  # 法杖
            pygame.draw.circle(self.buffer, (0, 191, 255),
                             (character_x + body_width//2 + 4,
                              character_y - body_height//2),
                             8)  # 法杖顶端
        else:  # 弓箭手
            # 绘制弓
            pygame.draw.arc(self.buffer, (139, 69, 19),
                          (character_x + body_width//2,
                           character_y - 30,
                           20, 60),
                          -1.57, 1.57, 3)
        
        # 底部按钮
        button_y = panel_y + panel_height - 50
        
        # 返回按钮
        pygame.draw.rect(self.buffer, (60, 60, 140),
                        (panel_x + 50, button_y, 100, 40), border_radius=5)
        back_text = self.font.render("返回", True, (255, 255, 255))
        back_rect = back_text.get_rect(center=(panel_x + 100, button_y + 20))
        self.buffer.blit(back_text, back_rect)
        
        # 创建按钮
        pygame.draw.rect(self.buffer, (60, 140, 60),
                        (panel_x + panel_width - 150, button_y, 100, 40), border_radius=5)
        create_text = self.font.render("创建", True, (255, 255, 255))
        create_rect = create_text.get_rect(center=(panel_x + panel_width - 100, button_y + 20))
        self.buffer.blit(create_text, create_rect)
        
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
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 获取面板位置
            panel_width = 900
            panel_height = 500
            panel_x = (self.screen_width - panel_width) // 2
            panel_y = 100
            
            # 计算输入区域位置
            input_x = panel_x + 200
            input_y = panel_y + 30
            spacing = 60
            
            # 检查名称输入框
            name_rect = pygame.Rect(input_x, input_y, 200, 30)
            self.input_active = name_rect.collidepoint(event.pos)
            
            # 检查性别按钮
            input_y += spacing
            gender_button_width = 80
            gender_spacing = 20
            for i, gender in enumerate(['男', '女']):
                button_x = input_x + i * (gender_button_width + gender_spacing)
                button_rect = pygame.Rect(button_x, input_y, gender_button_width, 30)
                if button_rect.collidepoint(event.pos):
                    if self.selected_gender != gender:  # 只在性别真正改变时更新
                        self.selected_gender = gender
                        if self.click_sound:
                            self.click_sound.play()
                        self.needs_redraw = True
                    return
            
            # 检查发型按钮
            input_y += 60
            hair_button_width = 100
            hair_spacing = 10
            hair_styles = ["金色_短发", "褐色_短发", "黑色_短发", "金色_长发", "褐色_长发", "黑色_长发"]
            for i, style in enumerate(hair_styles):
                row = i // 3
                col = i % 3
                button_x = input_x + col * (hair_button_width + hair_spacing)
                button_y = input_y + row * 35
                button_rect = pygame.Rect(button_x, button_y, hair_button_width, 30)
                if button_rect.collidepoint(event.pos):
                    self.selected_hairstyle = style
                    if self.click_sound:
                        self.click_sound.play()
                    self.needs_redraw = True
                    return
            
            # 检查体型按钮
            input_y += 95  # 60 + 35 (发型的两行)
            body_button_width = 80
            body_spacing = 10
            body_types = ["瘦小", "普通", "魁梧"]
            for i, body_type in enumerate(body_types):
                button_x = input_x + i * (body_button_width + body_spacing)
                button_rect = pygame.Rect(button_x, input_y, body_button_width, 30)
                if button_rect.collidepoint(event.pos):
                    self.selected_body_type = body_type
                    if self.click_sound:
                        self.click_sound.play()
                    self.needs_redraw = True
                    return
            
            # 检查职业按钮
            input_y += 60
            class_button_width = 80
            class_spacing = 10
            class_types = ["战士", "法师", "弓箭手"]
            for i, class_type in enumerate(class_types):
                button_x = input_x + i * (class_button_width + class_spacing)
                button_rect = pygame.Rect(button_x, input_y, class_button_width, 30)
                if button_rect.collidepoint(event.pos):
                    self.selected_class = class_type
                    if self.click_sound:
                        self.click_sound.play()
                    self.needs_redraw = True
                    return
            
            # 检查返回按钮
            button_y = panel_y + panel_height - 50
            back_button_rect = pygame.Rect(panel_x + 50, button_y, 100, 40)
            if back_button_rect.collidepoint(event.pos):
                self.game_state = "character_select"
                if self.click_sound:
                    self.click_sound.play()
                self.needs_redraw = True
                return
            
            # 检查创建按钮
            create_button_rect = pygame.Rect(panel_x + panel_width - 150, button_y, 100, 40)
            if create_button_rect.collidepoint(event.pos):
                if not self.character_name:
                    self.show_popup("请输入角色名称")
                    return
                    
                # 创建角色数据
                character_data = {
                    'name': self.character_name,
                    'gender': self.selected_gender,
                    'hairstyle': self.selected_hairstyle,
                    'body_type': self.selected_body_type,
                    'class': self.selected_class,
                    'skin_color': (255, 220, 180),  # 默认肤色
                    'health': 100,
                    'mana': 100,
                    'inventory': []  # 初始化空背包
                }
                
                # 保存角色数据
                self.save_character(self.character_name, character_data)
                
                # 重置选择
                self.character_name = ""
                self.selected_gender = '男'
                self.selected_hairstyle = "黑色_短发"
                self.selected_body_type = "普通"
                self.selected_class = "战士"
                
                # 返回角色选择界面
                self.game_state = "character_select"
                if self.click_sound:
                    self.click_sound.play()
                self.needs_redraw = True
                return
        
        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                self.input_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.character_name = self.character_name[:-1]
                self.needs_redraw = True
            else:
                # 限制名称长度为10个字符
                if len(self.character_name) < 10 and event.unicode.isprintable():
                    self.character_name += event.unicode
                    self.needs_redraw = True

    def draw_settings(self):
        """绘制设置界面"""
        # 创建一个临时surface来绘制设置界面
        settings_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        # 绘制半透明背景
        pygame.draw.rect(settings_surface, (0, 0, 0, 128), (0, 0, self.screen_width, self.screen_height))
        
        # 设置面板尺寸和位置
        settings_width = 500
        settings_height = 400
        settings_x = (self.screen_width - settings_width) // 2
        settings_y = (self.screen_height - settings_height) // 2
        
        # 绘制设置面板背景
        settings_rect = pygame.Rect(settings_x, settings_y, settings_width, settings_height)
        pygame.draw.rect(settings_surface, (50, 50, 50, 255), settings_rect)
        pygame.draw.rect(settings_surface, (100, 100, 100, 255), settings_rect, 2)
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("设置", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=settings_x + settings_width//2, y=settings_y + 20)
        settings_surface.blit(title, title_rect)
        
        # 绘制音量控制
        font = get_font(32)
        volume_text = font.render(f"音量: {int(self.volume * 100)}%", True, (255, 255, 255))
        settings_surface.blit(volume_text, (settings_x + 50, settings_y + 100))
        
        # 绘制音量滑块
        slider_width = 300
        slider_x = settings_x + 150
        slider_y = settings_y + 150
        pygame.draw.rect(settings_surface, (100, 100, 100, 255), (slider_x, slider_y, slider_width, 10))
        pygame.draw.rect(settings_surface, (200, 200, 200, 255), 
                        (slider_x + self.volume * slider_width - 5, slider_y - 5, 10, 20))
        
        # 创建和更新按钮
        button_width = 200
        button_height = 40
        button_x = settings_x + (settings_width - button_width) // 2
        
        # 全屏按钮
        self.fullscreen_button = SimpleButton(
            button_x,
            settings_y + 200,
            button_width,
            button_height,
            "全屏: " + ("开" if self.is_fullscreen else "关"),
            color=(0, 200, 0) if self.is_fullscreen else (200, 0, 0),
            font_size=32
        )
        self.fullscreen_button.draw(settings_surface)
        
        # 返回主菜单按钮
        self.menu_button = SimpleButton(
            button_x,
            settings_y + 250,
            button_width,
            button_height,
            "返回主菜单",
            color=(200, 150, 0),
            font_size=32
        )
        self.menu_button.draw(settings_surface)
        
        # 退出游戏按钮
        self.exit_button = SimpleButton(
            button_x,
            settings_y + 300,
            button_width,
            button_height,
            "退出游戏",
            color=(200, 0, 0),
            font_size=32
        )
        self.exit_button.draw(settings_surface)
        
        # 关闭按钮
        self.close_button = SimpleButton(
            settings_x + settings_width - 40,
            settings_y + 10,
            30,
            30,
            "×",
            color=(200, 0, 0),
            font_size=24
        )
        self.close_button.draw(settings_surface)
        
        # 将设置界面绘制到屏幕上
        self.screen.blit(settings_surface, (0, 0))
        pygame.display.flip()

    def handle_settings_events(self, event):
        """处理设置界面的事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # ESC键关闭设置界面
                self.game_state = "playing"
                self.needs_redraw = True
                return
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 检查是否点击了关闭按钮
            if hasattr(self, 'close_button') and self.close_button.handle_event(event):
                self.game_state = "playing"
                self.needs_redraw = True
                return
            
            # 检查是否点击了全屏按钮
            if hasattr(self, 'fullscreen_button') and self.fullscreen_button.handle_event(event):
                self.is_fullscreen = not self.is_fullscreen
                if self.is_fullscreen:
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                self.needs_redraw = True
                return
            
            # 检查是否点击了返回主菜单按钮
            if hasattr(self, 'menu_button') and self.menu_button.handle_event(event):
                self.game_state = "main_menu"
                self.needs_redraw = True
                return
            
            # 检查是否点击了退出游戏按钮
            if hasattr(self, 'exit_button') and self.exit_button.handle_event(event):
                self.running = False
                return
            
            # 检查是否点击了音量滑块区域
            settings_width = 500
            settings_height = 400
            settings_x = (self.screen_width - settings_width) // 2
            settings_y = (self.screen_height - settings_height) // 2
            slider_width = 300
            slider_rect = pygame.Rect(settings_x + 150, settings_y + 150, slider_width, 10)
            if slider_rect.collidepoint(event.pos):
                # 更新音量值
                self.volume = (event.pos[0] - (settings_x + 150)) / slider_width
                self.volume = max(0, min(1, self.volume))
                self.needs_redraw = True
                return
        
        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:  # 左键拖动
                settings_x = (self.screen_width - 500) // 2
                settings_y = (self.screen_height - 400) // 2
                slider_width = 300
                slider_rect = pygame.Rect(settings_x + 150, settings_y + 150, slider_width, 10)
                if slider_rect.collidepoint(event.pos):
                    # 更新音量值
                    self.volume = (event.pos[0] - (settings_x + 150)) / slider_width
                    self.volume = max(0, min(1, self.volume))
                    self.needs_redraw = True
                    return

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
            player_screen_x = self.player.rect.x - self.camera_x
            player_screen_y = self.player.rect.y - self.camera_y
            self.player.rect.x = player_screen_x
            self.player.rect.y = player_screen_y
            self.buffer.blit(self.player.image, self.player.rect)
            self.player.rect.x = self.player.rect.x + self.camera_x
            self.player.rect.y = self.player.rect.y + self.camera_y
        
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
        """绘制主菜单界面"""
        # 清空缓冲区并创建渐变背景
        for y in range(self.screen_height):
            # 从深蓝色渐变到浅蓝色
            progress = y / self.screen_height
            color = (
                int(20 + 115 * progress),  # R: 20 -> 135
                int(20 + 186 * progress),  # G: 20 -> 206
                int(40 + 195 * progress)   # B: 40 -> 235
            )
            pygame.draw.line(self.buffer, color, (0, y), (self.screen_width, y))
        
        # 绘制装饰性的云朵
        for i in range(5):
            cloud_x = (self.screen_width * (i + 1)) // 6
            cloud_y = 100 + (i % 2) * 50
            # 绘制白色半透明的云朵
            cloud_surface = pygame.Surface((120, 60), pygame.SRCALPHA)
            for j in range(3):
                pygame.draw.circle(cloud_surface, (255, 255, 255, 100),
                                 (20 + j * 40, 30), 30)
            self.buffer.blit(cloud_surface, (cloud_x - 60, cloud_y))
        
        # 绘制游戏标题（带阴影效果）
        title_font = get_font(72)
        # 阴影
        title_shadow = title_font.render("TrFk", True, (100, 50, 0))
        title_shadow_rect = title_shadow.get_rect(centerx=self.screen_width//2 + 4, y=54)
        self.buffer.blit(title_shadow, title_shadow_rect)
        # 主标题
        title = title_font.render("TrFk", True, (139, 69, 19))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 绘制装饰性的树
        for i in range(8):
            tree_x = (self.screen_width * i) // 7
            tree_y = self.screen_height - 100
            # 树干
            pygame.draw.rect(self.buffer, (101, 67, 33),
                           (tree_x - 10, tree_y - 40, 20, 60))
            # 树冠（多层渐变绿色）
            colors = [(40, 180, 40), (60, 200, 60), (80, 220, 80)]
            for j, color in enumerate(colors):
                pygame.draw.circle(self.buffer, color,
                                 (tree_x, tree_y - 60 + j * 10), 40 - j * 8)
        
        # 绘制所有按钮
        for button in self.menu_buttons.values():
            button.draw(self.buffer)
        
        # 如果有消息框，绘制消息框
        if self.message_box and self.message_box.visible:
            self.buffer.blit(self.message_box.surface, self.message_box.rect)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

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
        
        # 绘制标题
        title = self.title_font.render("选择角色", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, 50))
        self.buffer.blit(title, title_rect)
        
        # 创建半透明的面板
        panel_width = 800
        panel_height = 500
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 100
        
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
        preview_size = (150, 200)
        
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
                        
                        # 绘制角色预览
                        self.draw_character_preview(char_data, x, y, preview_size)
                        
                        # 绘制角色信息面板
                        info_x = x + preview_size[0] + 20
                        info_y = y + 10
                        info_spacing = 30  # 增加行间距
                        
                        # 绘制角色名称和职业（并列）
                        name_text = self.font.render(char_name, True, (255, 255, 255))
                        class_text = self.font.render(f"职业: {char_data.get('class', '战士')}", True, (200, 200, 100))
                        self.buffer.blit(name_text, (info_x, info_y))
                        self.buffer.blit(class_text, (info_x + 150, info_y))  # 减小偏移量
                        
                        # 绘制生命值和魔法值（并列）
                        max_hp = char_data.get('max_hp', 100)
                        max_mp = char_data.get('max_mp', 100)
                        hp_text = self.font.render(f"生命值: {max_hp}", True, (255, 100, 100))
                        mp_text = self.font.render(f"魔力值: {max_mp}", True, (100, 100, 255))
                        self.buffer.blit(hp_text, (info_x, info_y + info_spacing))
                        self.buffer.blit(mp_text, (info_x + 150, info_y + info_spacing))  # 减小偏移量
                        
                        # 绘制游戏时间
                        playtime = char_data.get('playtime', 0)
                        hours = playtime // 3600
                        minutes = (playtime % 3600) // 60
                        seconds = playtime % 60
                        time_text = self.font.render(f"游戏时间: {hours:02d}:{minutes:02d}:{seconds:02d}", True, (200, 200, 200))
                        self.buffer.blit(time_text, (info_x, info_y + info_spacing * 2))
                        
                        # 添加删除按钮（移到右下角）
                        delete_btn_width = 80
                        delete_btn_height = 30
                        delete_btn_x = info_x + 300  # 调整位置
                        delete_btn_y = y + preview_size[1] - delete_btn_height - 10  # 移到底部
                        
                        # 绘制删除按钮
                        delete_btn = SimpleButton(
                            delete_btn_x,
                            delete_btn_y,
                            delete_btn_width,
                            delete_btn_height,
                            "删除",
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
            "创建新角色",
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
            "返回",
            color=(100, 100, 200),
            font_size=32
        )
        back_btn.draw(self.buffer)
        
        # 存储按钮位置
        self.new_char_button = pygame.Rect(new_btn_x, new_btn_y, new_btn_width, new_btn_height)
        self.back_button = pygame.Rect(back_btn_x, back_btn_y, back_btn_width, back_btn_height)
        
        # 更新屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        self.needs_redraw = False

    def handle_character_select_events(self, event):
        """处理角色选择界面的事件"""
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
                panel_y = 100
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
                for char_name, delete_rect in self.delete_buttons.items():
                    # 调整按钮位置以考虑滚动
                    adjusted_rect = delete_rect.copy()
                    adjusted_rect.y -= self.scroll_y
                    if adjusted_rect.collidepoint(mouse_pos):
                        if self.show_confirm_dialog(f"确定要删除角色 {char_name} 吗？"):
                            try:
                                os.remove(os.path.join(self.player_path, f"{char_name}.plr"))
                                self.characters.remove(char_name)
                                if hasattr(self, 'click_sound') and self.click_sound:
                                    self.click_sound.play()
                                self.needs_redraw = True
                            except Exception as e:
                                print(f"删除角色时出错: {e}")
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
            panel_y = 100
            preview_size = (150, 200)
            char_spacing_y = 220
            start_x = panel_x + 20  # 与绘制时保持一致
            start_y = panel_y + 30 - self.scroll_y
            
            for i, char_name in enumerate(self.characters):
                x = start_x
                y = start_y + i * char_spacing_y
                # 扩大点击区域以包含角色信息
                char_rect = pygame.Rect(x, y, panel_width - 100, preview_size[1])
                
                # 调整点击区域以考虑滚动
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
        
        dialog = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
        dialog.fill((0, 0, 0, 230))
        
        # 绘制消息
        text = self.font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(dialog_width//2, dialog_height//3))
        dialog.blit(text, text_rect)
        
        # 按钮
        btn_width = 100
        btn_height = 40
        btn_y = dialog_height - 60
        
        # 确认按钮
        confirm_btn = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
        confirm_btn.fill((0, 150, 0, 200))
        confirm_rect = pygame.Rect(dialog_width//4 - btn_width//2, btn_y, btn_width, btn_height)
        dialog.blit(confirm_btn, confirm_rect)
        
        confirm_text = self.font.render("确认", True, (255, 255, 255))
        text_rect = confirm_text.get_rect(center=(dialog_width//4, btn_y + btn_height//2))
        dialog.blit(confirm_text, text_rect)
        
        # 取消按钮
        cancel_btn = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
        cancel_btn.fill((200, 50, 50, 200))
        cancel_rect = pygame.Rect(3*dialog_width//4 - btn_width//2, btn_y, btn_width, btn_height)
        dialog.blit(cancel_btn, cancel_rect)
        
        cancel_text = self.font.render("取消", True, (255, 255, 255))
        text_rect = cancel_text.get_rect(center=(3*dialog_width//4, btn_y + btn_height//2))
        dialog.blit(cancel_text, text_rect)
        
        # 显示对话框
        self.buffer.blit(dialog, (dialog_x, dialog_y))
        pygame.display.flip()
        
        # 等待用户响应
        while True:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    # 调整按钮位置到屏幕坐标
                    confirm_rect.move_ip(dialog_x, dialog_y)
                    cancel_rect.move_ip(dialog_x, dialog_y)
                    
                    if confirm_rect.collidepoint(mouse_pos):
                        if hasattr(self, 'click_sound'):
                            self.click_sound.play()
                        return True
                    elif cancel_rect.collidepoint(mouse_pos):
                        if hasattr(self, 'click_sound'):
                            self.click_sound.play()
                        return False
                elif event.type == pygame.QUIT:
                    return False

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
        title = title_font.render("制作人员", True, WHITE)
        title_rect = title.get_rect(centerx=self.screen_width//2, y=100)
        self.buffer.blit(title, title_rect)
        
        # 制作人员列表
        credits_font = get_font(36)
        credits_list = [
            "游戏设计：TrFk团队",
            "程序开发：TrFk团队",
            "美术设计：TrFk团队",
            "音效设计：TrFk团队",
            "测试团队：TrFk团队"
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
            "返回",
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
        
        # 创建一个带有透明度的表面
        message_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        message_surface.fill((0, 0, 0, 200))  # 半透明黑色背景
        
        # 渲染消息文本
        text = self.font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(box_width//2, box_height//2))
        message_surface.blit(text, text_rect)
        
        # 创建一个简单的消息框对象
        class MessageBox:
            def __init__(self, surface, rect):
                self.surface = surface
                self.rect = rect
                self.visible = True
        
        # 保存消息框
        self.message_box = MessageBox(message_surface, pygame.Rect(box_x, box_y, box_width, box_height))
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
        # 清空缓冲区并填充深蓝色背景
        self.buffer.fill((20, 20, 40))  # 深蓝色背景
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("创建世界", True, (200, 200, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 创建地图创建区域（蓝色半透明面板）
        panel_width = self.screen_width * 0.8
        panel_height = self.screen_height * 0.6
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 120
        
        # 绘制地图创建面板背景
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (50, 50, 120, 200), (0, 0, panel_width, panel_height), border_radius=10)
        self.buffer.blit(panel_surface, (panel_x, panel_y))
        
        # 绘制名称输入框标签
        name_font = get_font(32)
        name_text = name_font.render("名字:", True, (255, 255, 255))
        self.buffer.blit(name_text, (panel_x + 50, panel_y + 30))
        
        # 绘制名称输入框
        name_rect = pygame.Rect(panel_x + 150, panel_y + 30, 300, 40)
        pygame.draw.rect(self.buffer, (60, 60, 60) if self.map_name_active else (40, 40, 40), name_rect)
        pygame.draw.rect(self.buffer, (255, 255, 255), name_rect, 2)
        
        # 绘制名称文本
        display_text = self.map_name_input if self.map_name_input else ""
        cursor = "_" if self.map_name_active and pygame.time.get_ticks() % 1000 < 500 else ""
        name_surface = name_font.render(display_text + cursor, True, (255, 255, 255))
        self.buffer.blit(name_surface, (name_rect.x + 10, name_rect.y + 5))
        
        # 绘制地图大小选项
        size_y = panel_y + 100
        size_spacing = 60
        sizes = ["小型", "中型", "大型"]
        size_buttons = []
        
        for i, size in enumerate(sizes):
            button = SimpleButton(
                panel_x + 50,
                size_y + i * size_spacing,
                panel_width - 100,
                50,
                size,
                color=(100, 100, 150),
                font_size=32
            )
            button.draw(self.buffer)
            size_buttons.append(button)
            
            # 添加大小说明文本
            if size == "小型":
                desc_text = name_font.render("小型世界 (40×23格) - 适合快速游戏和探索", True, (200, 200, 255))
            elif size == "中型":
                desc_text = name_font.render("中型世界 (80×45格) - 平衡的游戏体验", True, (200, 200, 255))
            else:
                desc_text = name_font.render("大型世界 (120×68格) - 史诗般的冒险之旅", True, (200, 200, 255))
            desc_rect = desc_text.get_rect(x=panel_x + 50, y=size_y + i * size_spacing + 50)
            self.buffer.blit(desc_text, desc_rect)
        
        # 绘制底部按钮
        button_width = 200
        button_height = 60
        button_y = self.screen_height - 100
        
        # 返回按钮
        self.back_button = SimpleButton(
            panel_x,
            button_y,
            button_width,
            button_height,
            "返回",
            color=(60, 60, 140),
            font_size=36
        )
        
        # 创建按钮
        self.create_button = SimpleButton(
            panel_x + panel_width - button_width,
            button_y,
            button_width,
            button_height,
            "创建",
            color=(60, 60, 140),
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
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event):
                self.game_state = "map_select"
                self.needs_redraw = True
                return
            
            # 检查创建按钮
            if self.create_button.handle_event(event):
                if self.map_name_input:  # 只有在有名字的情况下才创建
                    # 根据选择的大小创建地图
                    if self.selected_map_size == "小型":
                        width, height = 40, 23
                    elif self.selected_map_size == "中型":
                        width, height = 80, 45
                    else:
                        width, height = 120, 68
                    
                    # 创建新地图
                    self.create_new_map(width, height, 32, self.map_name_input)
                    # 将新地图添加到列表中
                    self.maps.append(self.map_name_input)
                    # 返回地图选择界面
                    self.game_state = "map_select"
                    self.needs_redraw = True
                return
            
            # 检查名称输入框
            name_rect = pygame.Rect(
                self.screen_width//2 - 400 + 150,
                120 + 30,
                300,
                40
            )
            self.map_name_active = name_rect.collidepoint(event.pos)
            
            # 检查大小选项按钮
            panel_x = (self.screen_width - self.screen_width * 0.8) // 2
            size_y = 120 + 100
            size_spacing = 60
            sizes = ["小型", "中型", "大型"]
            
            for i, size in enumerate(sizes):
                button_rect = pygame.Rect(
                    panel_x + 50,
                    size_y + i * size_spacing,
                    self.screen_width * 0.8 - 100,
                    50
                )
                if button_rect.collidepoint(event.pos):
                    self.selected_map_size = size
                    self.needs_redraw = True
                    return
            
        elif event.type == pygame.KEYDOWN and self.map_name_active:
            if event.key == pygame.K_RETURN:
                self.map_name_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.map_name_input = self.map_name_input[:-1]
                self.needs_redraw = True
            elif len(self.map_name_input) < 20:  # 限制名称长度
                if event.unicode.isprintable():
                    self.map_name_input += event.unicode
                    self.needs_redraw = True

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

if __name__ == "__main__":
    game = Game()
    game.run()