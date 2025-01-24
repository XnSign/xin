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
        self.color = color
        self.font = get_font(font_size)
        self.is_hovered = False
        
        # 渲染文本
        self.text_surface = self.font.render(text, True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
    
    def draw(self, surface):
        # 绘制按钮背景
        if self.is_hovered:
            hover_color = (min(self.color[0] + 30, 255),
                         min(self.color[1] + 30, 255),
                         min(self.color[2] + 30, 255))
            pygame.draw.rect(surface, hover_color, self.rect, border_radius=5)
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        
        # 绘制边框
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=5)
        
        # 绘制文本
        surface.blit(self.text_surface, self.text_rect)
    
    def handle_event(self, event, game=None):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                # 如果提供了游戏实例，播放点击音效
                if game and hasattr(game, 'click_sound'):
                    game.click_sound.play()
                return True
        return False

class Slider:
    def __init__(self, x, y, width, height, label, max_value, initial_value=128):
        """初始化滑块"""
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.max_value = max_value
        self.value = initial_value
        self.dragging = False
        
    def handle_event(self, event, game=None):
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                if self.rect.collidepoint(event.pos):
                    self.dragging = True
                    # 更新值
                    self.value = (event.pos[0] - self.rect.x) / self.rect.width * self.max_value
                    self.value = max(0, min(self.max_value, self.value))
                    # 播放音效
                    if game and hasattr(game, 'click_sound'):
                        game.click_sound.play()
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键释放
                if self.dragging and game and hasattr(game, 'click_sound'):
                    game.click_sound.play()
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and event.buttons[0]:  # 左键拖动
                # 更新值
                old_value = self.value
                self.value = (event.pos[0] - self.rect.x) / self.rect.width * self.max_value
                self.value = max(0, min(self.max_value, self.value))
                # 当值变化超过一定阈值时播放音效
                if game and hasattr(game, 'click_sound') and abs(self.value - old_value) > self.max_value * 0.05:
                    game.click_sound.play()
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
        self.running = True
        self.needs_redraw = True
        
        # 加载音效
        try:
            self.click_sound = pygame.mixer.Sound("assets/sounds/click.wav")
            self.click_sound.set_volume(0.5)  # 设置音量为50%
        except:
            print("无法加载音效文件，创建空音效")
            # 创建一个1毫秒的空白音效作为备用
            self.click_sound = pygame.mixer.Sound(buffer=bytes([0] * 44))
        
        # 游戏状态
        self.game_state = "main_menu"
        
        # 初始化游戏状态和变量
        self.game_state = "main_menu"  # 初始状态为主菜单
        self.needs_redraw = True
        self.running = True
        self.clock = pygame.time.Clock()
        
        # 地图创建界面的变量
        self.map_name_input = ""  # 地图名称输入
        self.map_name_active = False  # 名称输入框是否激活
        self.selected_map_size = "中型"  # 默认选择中型地图
        
        # 初始化其他游戏组件
        self.world = None
        self.player = None
        self.camera = None
        self.inventory = None
        self.hotbar = None
        self.block_menu = None
        self.maps = []  # 存储地图列表
        self.selected_map = None
        self.load_maps()  # 加载现有地图
        
        # 主菜单按钮
        self.menu_buttons = {
            'singleplayer': SimpleButton(
                self.screen_width//2 - 200,
                200,
                400,
                60,
                "单人模式",
                color=(0, 200, 0),
                font_size=36
            ),
            'multiplayer': SimpleButton(
                self.screen_width//2 - 200,
                280,
                400,
                60,
                "多人模式",
                color=(0, 150, 200),
                font_size=36
            ),
            'achievements': SimpleButton(
                self.screen_width//2 - 200,
                360,
                400,
                60,
                "成就",
                color=(200, 150, 0),
                font_size=36
            ),
            'workshop': SimpleButton(
                self.screen_width//2 - 200,
                440,
                400,
                60,
                "创意工坊",
                color=(150, 150, 150),
                font_size=36
            ),
            'settings': SimpleButton(
                self.screen_width//2 - 200,
                520,
                400,
                60,
                "设置",
                color=(100, 100, 100),
                font_size=36
            ),
            'credits': SimpleButton(
                self.screen_width//2 - 200,
                600,
                400,
                60,
                "制作人员",
                color=(150, 150, 150),
                font_size=36
            ),
            'exit': SimpleButton(
                self.screen_width//2 - 200,
                680,
                400,
                60,
                "退出游戏",
                color=(200, 0, 0),
                font_size=36
            )
        }
        
        # 角色和地图相关
        self.characters = []
        self.selected_character = None
        self.choosing_map_size = False
        self.selected_map_size = None
        
        # 初始化按钮列表
        self.character_buttons = []
        self.character_delete_buttons = []
        self.map_delete_buttons = []
        self.map_size_buttons = []
        
        # 地图大小选项
        self.map_sizes = {
            "小型": {
                "width": 1280, 
                "height": 720, 
                "grid_size": 32,
                "description": "小型地图 (40×23格) - 适合快速游戏和探索"
            },
            "中型": {
                "width": 2560, 
                "height": 1440, 
                "grid_size": 32,
                "description": "中型地图 (80×45格) - 平衡的游戏体验"
            },
            "大型": {
                "width": 3840, 
                "height": 2160, 
                "grid_size": 32,
                "description": "大型地图 (120×68格) - 史诗般的冒险之旅"
            }
        }
        
        # 按键绑定
        self.key_bindings = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'jump': pygame.K_SPACE,
            'inventory': pygame.K_ESCAPE  # 使用ESC键打开背包
        }
        
        # 按键名称映射
        self.action_names = {
            'left': '向左移动',
            'right': '向右移动',
            'jump': '跳跃',
            'inventory': '背包'
        }
        
        # 创建按钮
        self.settings_button = SimpleButton(
            self.screen_width - 150,
            self.screen_height - 70,
            120,
            50,
            "设置",
            color=(255, 0, 0),
            font_size=32
        )
        
        # 加载角色和地图
        docs_path = get_documents_path()
        base_path = os.path.join(docs_path, 'My Games', 'TrFk')
        self.player_path = os.path.join(base_path, 'Players')
        self.world_path = os.path.join(base_path, 'Worlds')
        os.makedirs(self.player_path, exist_ok=True)
        os.makedirs(self.world_path, exist_ok=True)
        self.load_characters_and_maps()
        
        # 创建角色创建器
        self.character_creator = CharacterCreator(
            self.screen_width//2 - 400,
            self.screen_height//2 - 300,
            800,
            600
        )
        
        # 地图创建相关
        self.map_name_input = ""
        self.map_name_active = False
        self.map_name_error = False
        
        # 消息框
        self.message_box = None
        
        # 添加提示窗口状态
        self.popup_message = None
        self.popup_timer = 0
        self.POPUP_DURATION = 2000  # 提示显示时间（毫秒）
        
    def run(self):
        """游戏主循环"""
        while self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                
                # 根据游戏状态处理事件
                if self.game_state == "main_menu":
                    self.handle_main_menu_events(event)
                elif self.game_state == "character_select":
                    self.handle_character_select_events(event)
                elif self.game_state == "character_create":
                    self.handle_character_create_events(event)
                elif self.game_state == "map_select":
                    self.handle_map_select_events(event)
                elif self.game_state == "map_create":
                    self.handle_map_create_events(event)
                elif self.game_state == "settings":
                    self.handle_settings_events(event)
                elif self.game_state == "playing":
                    self.handle_playing_events(event)
            
            # 根据游戏状态更新和绘制
            if self.game_state == "main_menu":
                if self.needs_redraw:
                    self.draw_main_menu()
            elif self.game_state == "character_select":
                if self.needs_redraw:
                    self.draw_character_select()
            elif self.game_state == "character_create":
                if self.needs_redraw:
                    self.draw_character_create()
            elif self.game_state == "map_select":
                if self.needs_redraw:
                    self.draw_map_select()
            elif self.game_state == "map_create":
                if self.needs_redraw:
                    self.draw_map_create()
            elif self.game_state == "settings":
                if self.needs_redraw:
                    self.draw_settings()
            elif self.game_state == "playing":
                self.update()
                if self.needs_redraw:
                    self.draw()
            
            # 限制帧率
            self.clock.tick(60)
            # 更新窗口标题显示FPS
            pygame.display.set_caption(f"2D沙盒游戏 - FPS: {int(self.clock.get_fps())}")
            
            # 更新显示
            pygame.display.flip()

    def draw_main_menu(self):
        """绘制主菜单"""
        # 清空缓冲区并填充天蓝色背景
        self.buffer.fill((135, 206, 235))  # 天蓝色背景
        
        # 绘制太阳
        sun_pos = (200, 200)
        sun_radius = 60
        sun_color = (255, 255, 200)  # 淡黄色
        pygame.draw.circle(self.buffer, sun_color, sun_pos, sun_radius)
        
        # 绘制白云
        cloud_color = (255, 255, 255)
        for cloud_pos in [(300, 150), (500, 180), (700, 160)]:
            # 绘制一朵云的多个圆形
            radius = 30
            pygame.draw.circle(self.buffer, cloud_color, cloud_pos, radius)
            pygame.draw.circle(self.buffer, cloud_color, (cloud_pos[0] - 20, cloud_pos[1] + 10), radius - 5)
            pygame.draw.circle(self.buffer, cloud_color, (cloud_pos[0] + 20, cloud_pos[1] + 10), radius - 5)
        
        # 绘制远处的山脉
        mountain_color = (100, 100, 100)
        points = [(0, 600), (200, 400), (400, 550), (600, 350), (800, 500), (1000, 450), (1200, 600)]
        pygame.draw.polygon(self.buffer, mountain_color, points)
        
        # 绘制树木
        tree_color = (34, 139, 34)  # 森林绿
        tree_pos = [(100, 500), (300, 480), (500, 490), (700, 470), (900, 485)]
        for pos in tree_pos:
            # 绘制树干
            trunk_color = (139, 69, 19)  # 棕色
            pygame.draw.rect(self.buffer, trunk_color, (pos[0]-10, pos[1], 20, 60))
            # 绘制树冠
            pygame.draw.polygon(self.buffer, tree_color, 
                [(pos[0]-30, pos[1]+20), (pos[0], pos[1]-40), (pos[0]+30, pos[1]+20)])
        
        # 绘制游戏标题
        title_font = get_font(72)
        title_text = "TrFk"
        title_shadow = title_font.render(title_text, True, (0, 0, 0))  # 阴影
        title = title_font.render(title_text, True, (34, 139, 34))  # 森林绿色
        
        # 计算标题位置
        title_x = self.screen_width // 2
        title_y = 100
        
        # 绘制带阴影的标题
        shadow_offset = 3
        title_shadow_rect = title_shadow.get_rect(center=(title_x + shadow_offset, title_y + shadow_offset))
        title_rect = title.get_rect(center=(title_x, title_y))
        self.buffer.blit(title_shadow, title_shadow_rect)
        self.buffer.blit(title, title_rect)
        
        # 绘制菜单选项
        menu_items = [
            "单人模式",
            "多人模式",
            "成就",
            "创意工坊",
            "设置",
            "制作人员",
            "退出"
        ]
        
        # 设置菜单样式
        menu_font = get_font(36)
        menu_spacing = 50  # 菜单项之间的间距
        menu_start_y = 300  # 菜单起始Y坐标
        
        # 绘制菜单项
        for i, item in enumerate(menu_items):
            text = menu_font.render(item, True, (50, 50, 50))  # 深灰色文字
            text_hover = menu_font.render(item, True, (255, 255, 255))  # 鼠标悬停时的白色
            
            # 计算文本位置
            text_rect = text.get_rect(center=(self.screen_width // 2, menu_start_y + i * menu_spacing))
            
            # 检查鼠标悬停
            if text_rect.collidepoint(pygame.mouse.get_pos()):
                # 绘制选中效果
                pygame.draw.rect(self.buffer, (100, 100, 100, 128), text_rect.inflate(20, 10))
                self.buffer.blit(text_hover, text_rect)
            else:
                self.buffer.blit(text, text_rect)
        
        # 在最后添加弹出提示的绘制
        self.draw_popup()
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_main_menu_events(self, event):
        """处理主菜单事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查是否点击了弹窗的关闭按钮
            if self.popup_message and hasattr(self, 'popup_close_rect') and self.popup_close_rect:
                if self.popup_close_rect.collidepoint(event.pos):
                    self.click_sound.play()  # 播放关闭按钮音效
                    self.popup_message = None
                    self.popup_close_rect = None
                    self.needs_redraw = True
                    return
            
            # 获取鼠标位置
            mouse_pos = pygame.mouse.get_pos()
            
            # 如果有弹窗，不处理其他点击
            if self.popup_message:
                return
            
            # 计算菜单项位置
            menu_items = [
                "单人模式",
                "多人模式",
                "成就",
                "创意工坊",
                "设置",
                "制作人员",
                "退出"
            ]
            menu_start_y = 300
            menu_spacing = 50
            
            # 检查每个菜单项
            for i, item in enumerate(menu_items):
                text_rect = get_font(36).render(item, True, (0, 0, 0)).get_rect(
                    center=(self.screen_width // 2, menu_start_y + i * menu_spacing)
                )
                
                if text_rect.collidepoint(mouse_pos):
                    self.click_sound.play()  # 播放菜单项点击音效
                    if item == "单人模式":
                        self.game_state = "character_select"
                        self.needs_redraw = True
                    elif item == "多人模式":
                        self.show_popup("多人模式正在开发中...")
                    elif item == "成就":
                        self.show_popup("成就系统正在开发中...")
                    elif item == "创意工坊":
                        self.show_popup("创意工坊正在开发中...")
                    elif item == "设置":
                        self.previous_state = self.game_state
                        self.game_state = "settings"
                        self.needs_redraw = True
                    elif item == "制作人员":
                        self.show_popup("制作人员名单正在整理中...")
                    elif item == "退出":
                        pygame.quit()
                        sys.exit()
                    return

    def draw_character_select(self):
        """绘制角色选择界面"""
        # 清空缓冲区并填充深蓝色背景
        self.buffer.fill((20, 20, 40))  # 深蓝色背景
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("选择玩家", True, (200, 200, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 创建角色列表区域（蓝色半透明面板）
        panel_width = self.screen_width * 0.8
        panel_height = self.screen_height * 0.6
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 120
        
        # 绘制角色列表面板背景
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (50, 50, 120, 200), (0, 0, panel_width, panel_height), border_radius=10)
        self.buffer.blit(panel_surface, (panel_x, panel_y))
        
        # 如果有角色，显示角色信息
        if self.characters:
            for i, character_name in enumerate(self.characters):
                # 读取角色数据
                character_file = os.path.join(self.player_path, f"{character_name}.plr")
                if os.path.exists(character_file):
                    with open(character_file, 'r', encoding='utf-8') as f:
                        character_data = json.load(f)
                    
                    # 创建角色信息条目
                    entry_height = 80
                    entry_y = panel_y + 20 + i * (entry_height + 10)
                    
                    # 绘制条目背景（半透明白色，用于hover效果）
                    entry_surface = pygame.Surface((panel_width - 40, entry_height), pygame.SRCALPHA)
                    pygame.draw.rect(entry_surface, (255, 255, 255, 10), (0, 0, panel_width - 40, entry_height))
                    self.buffer.blit(entry_surface, (panel_x + 20, entry_y))
                    
                    # 绘制角色图标（示例：简单的方形图标）
                    icon_rect = pygame.Rect(panel_x + 20, entry_y + 10, 60, 60)
                    pygame.draw.rect(self.buffer, (100, 100, 150), icon_rect)
                    
                    # 绘制角色信息
                    info_font = get_font(32)
                    # 显示生命值和魔法值
                    stats_text = f"{character_data.get('health', 100)}生命 {character_data.get('mana', 100)}魔力"
                    name_surface = info_font.render(character_name, True, (255, 255, 255))
                    stats_surface = info_font.render(stats_text, True, (200, 200, 255))
                    mode_surface = info_font.render("经典", True, (200, 200, 255))
                    
                    # 绘制文本
                    self.buffer.blit(name_surface, (panel_x + 100, entry_y + 5))
                    self.buffer.blit(stats_surface, (panel_x + 100, entry_y + 35))
                    self.buffer.blit(mode_surface, (panel_x + panel_width - 150, entry_y + 20))
                    
                    # 绘制分隔线（除了最后一个条目）
                    if i < len(self.characters) - 1:
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
        self.new_character_button = SimpleButton(
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
        self.new_character_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_character_select_events(self, event):
        """处理角色选择界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event, self):  # 添加self参数
                self.game_state = "main_menu"
                self.needs_redraw = True
                return
            
            # 检查新建按钮
            if self.new_character_button.handle_event(event, self):  # 添加self参数
                self.game_state = "character_create"
                self.needs_redraw = True
                return
            
            # 检查角色列表点击
            if self.characters:
                panel_width = self.screen_width * 0.8
                panel_height = self.screen_height * 0.6
                panel_x = (self.screen_width - panel_width) // 2
                panel_y = 120
                
                # 计算鼠标点击位置
                mouse_pos = event.pos
                
                for i, character_name in enumerate(self.characters):
                    entry_height = 80
                    entry_y = panel_y + 20 + i * (entry_height + 10)
                    entry_rect = pygame.Rect(panel_x + 20, entry_y, panel_width - 40, entry_height)
                    
                    if entry_rect.collidepoint(mouse_pos):
                        self.click_sound.play()  # 添加点击音效
                        self.selected_character = character_name
                        self.game_state = "map_select"
                        self.needs_redraw = True
                        return

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
            
            # 获取所有.wld文件
            self.maps = []
            for file in os.listdir(self.world_path):
                if file.endswith('.wld'):
                    map_name = file[:-4]  # 移除.wld后缀
                    self.maps.append(map_name)
            
            # 按字母顺序排序地图列表
            self.maps.sort()
        except Exception as e:
            print(f"加载地图时出错: {e}")
            self.maps = []

    def create_new_map(self, width, height, grid_size, map_name):
        """创建新的地图"""
        try:
            # 创建地图数据
            map_data = {
                'width': width,
                'height': height,
                'grid_size': grid_size,
                'grid': [[0 for _ in range(width)] for _ in range(height)]  # 初始化为空地图
            }
            
            # 生成地形
            self.generate_terrain(map_data['grid'])
            
            # 保存地图
            map_file = os.path.join(self.world_path, f"{map_name}.wld")
            with open(map_file, 'w', encoding='utf-8') as f:
                json.dump(map_data, f, ensure_ascii=False, indent=4)
            
            return map_name
            
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
                spawn_point = world_data.get('spawn_point', [world_data['width'] // 2, 0])
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
                spawn_x = spawn_point[0] * self.world.grid_size
                spawn_y = 0
                for y in range(self.world.height):
                    if self.world.grid[y][spawn_point[0]] != self.world.EMPTY:
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
        x = self.screen_width // 2 - 200
        y = self.screen_height // 2 - 100
        self.message_box = MessageBox(x, y, 400, 200, message)
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
            # 计算面板尺寸
            panel_width = self.screen_width * 0.8
            panel_x = (self.screen_width - panel_width) // 2
            panel_y = 120

            # 检查返回按钮
            if self.back_button.handle_event(event, self):  # 添加self参数
                self.game_state = "map_select"
                self.needs_redraw = True
                return
            
            # 检查创建按钮
            if self.create_button.handle_event(event, self):  # 添加self参数
                if self.map_name_input:  # 只有在有名字的情况下才创建
                    # 根据选择的大小创建地图
                    if self.selected_map_size == "小型":
                        width, height = 40, 23
                    elif self.selected_map_size == "中型":
                        width, height = 80, 45
                    else:  # 大型
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
                panel_x + 150,
                panel_y + 30,
                300,
                40
            )
            if name_rect.collidepoint(event.pos):
                self.click_sound.play()  # 添加点击音效
            self.map_name_active = name_rect.collidepoint(event.pos)
            
            # 检查大小选项按钮
            size_y = panel_y + 100
            size_spacing = 60
            sizes = ["小型", "中型", "大型"]
            
            for i, size in enumerate(sizes):
                button_rect = pygame.Rect(
                    panel_x + 50,
                    size_y + i * size_spacing,
                    panel_width - 100,
                    50
                )
                if button_rect.collidepoint(event.pos):
                    self.click_sound.play()  # 添加点击音效
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

    def load_characters_and_maps(self):
        """加载已有的角色和地图"""
        # 加载角色
        self.characters = []
        if os.path.exists(self.player_path):
            for file in os.listdir(self.player_path):
                if file.endswith('.plr'):
                    character_name = file[:-4]  # 移除 .plr 后缀
                    self.characters.append(character_name)
        
        # 加载地图
        self.maps = []
        if os.path.exists(self.world_path):
            for entry in os.listdir(self.world_path):
                if os.path.isdir(os.path.join(self.world_path, entry)):
                    self.maps.append(entry)
        
        # 按字母顺序排序列表
        self.characters.sort()
        self.maps.sort()
        
        print(f"已加载的角色: {self.characters}")
        print(f"已加载的地图: {self.maps}")
        
        # 更新选择按钮
        self.update_selection_buttons()

    def update_selection_buttons(self):
        """更新选择界面的按钮"""
        # 按钮尺寸和位置
        button_width = 500  # 增加宽度
        button_height = 100  # 增加高度
        button_spacing = 20  # 减小间距
        start_y = 200
        delete_button_width = 80  # 增加删除按钮宽度
        delete_button_spacing = 10
        
        # 初始化按钮列表
        self.character_buttons = []
        self.character_delete_buttons = []
        self.map_delete_buttons = []
        
        # 创建新建角色按钮
        self.new_character_button = SimpleButton(
            self.screen_width//2 - button_width//2,
            start_y,
            button_width,
            button_height,
            "新建角色",
            color=(0, 200, 0),
            font_size=48
        )
        
        # 如果有角色，创建对应的按钮
        if self.characters:
            for i, char_name in enumerate(self.characters):
                # 主按钮
                self.character_buttons.append(
                    SimpleButton(
                        self.screen_width//2 - button_width//2,
                        start_y + (i + 1) * (button_height + button_spacing),
                        button_width,
                        button_height,
                        char_name,
                        color=(100, 100, 200),
                        font_size=48
                    )
                )
                # 删除按钮
                self.character_delete_buttons.append(
                    SimpleButton(
                        self.screen_width//2 + button_width//2 + delete_button_spacing,
                        start_y + (i + 1) * (button_height + button_spacing),
                        delete_button_width,
                        button_height,
                        "×",
                        color=(200, 0, 0),
                        font_size=48
                    )
                )
        
        # 如果有地图，创建对应的删除按钮
        if self.maps:
            for i, map_name in enumerate(self.maps):
                self.map_delete_buttons.append(
                    SimpleButton(
                        self.screen_width//2 + button_width//2 + delete_button_spacing,
                        start_y + (i + 1) * (button_height + button_spacing),
                        delete_button_width,
                        button_height,
                        "×",
                        color=(200, 0, 0),
                        font_size=48
                    )
                )
        
        # 更新返回按钮
        self.back_button = SimpleButton(
            50,
            self.screen_height - 100,
            200,
            80,
            "返回",
            color=(200, 100, 0),
            font_size=36
        )

    def draw_map_select(self):
        """绘制地图选择界面"""
        # 清空缓冲区并填充深蓝色背景
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
                create_time = "已创建: 2024/03/21"  # 这里可以从地图数据中获取实际创建时间
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
            if self.back_button.handle_event(event, self):  # 添加self参数
                self.game_state = "character_select"
                self.needs_redraw = True
                return
            
            # 检查新建按钮
            if self.new_map_button.handle_event(event, self):  # 添加self参数
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
                        self.click_sound.play()  # 添加点击音效
                        self.selected_map = map_name
                        self.initialize_game()
                        return

    def draw_character_create(self):
        """绘制角色创建界面"""
        # 清空缓冲区并填充深蓝色背景
        self.buffer.fill((20, 20, 40))  # 深蓝色背景
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("创建角色", True, (200, 200, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 创建角色创建区域（蓝色半透明面板）
        panel_width = self.screen_width * 0.8
        panel_height = self.screen_height * 0.7
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 120
        
        # 绘制角色创建面板背景
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (50, 50, 120, 200), (0, 0, panel_width, panel_height), border_radius=10)
        self.buffer.blit(panel_surface, (panel_x, panel_y))
        
        # 绘制名称输入框标签
        name_font = get_font(32)
        name_text = name_font.render("名字:", True, (255, 255, 255))
        self.buffer.blit(name_text, (panel_x + 50, panel_y + 30))
        
        # 绘制名称输入框
        name_rect = pygame.Rect(panel_x + 150, panel_y + 30, 300, 40)
        pygame.draw.rect(self.buffer, (60, 60, 60) if self.character_creator.name_active else (40, 40, 40), name_rect)
        pygame.draw.rect(self.buffer, (255, 255, 255), name_rect, 2)
        
        # 绘制名称文本
        display_text = self.character_creator.name if self.character_creator.name else ""
        cursor = "_" if self.character_creator.name_active and pygame.time.get_ticks() % 1000 < 500 else ""
        name_surface = name_font.render(display_text + cursor, True, (255, 255, 255))
        self.buffer.blit(name_surface, (name_rect.x + 10, name_rect.y + 5))
        
        # 设置选项的起始位置和间距
        option_x = panel_x + 50
        option_y = panel_y + 100
        option_spacing = 80
        button_width = 60
        button_height = 40
        
        # 绘制职业选择
        class_text = name_font.render("职业:", True, (255, 255, 255))
        self.buffer.blit(class_text, (option_x, option_y))
        
        # 职业选择按钮
        self.prev_class_button = SimpleButton(
            option_x + 100,
            option_y,
            button_width,
            button_height,
            "<",
            color=(60, 60, 140),
            font_size=32
        )
        self.next_class_button = SimpleButton(
            option_x + 300,
            option_y,
            button_width,
            button_height,
            ">",
            color=(60, 60, 140),
            font_size=32
        )
        class_value = name_font.render(CLASSES[self.character_creator.class_index], True, (255, 255, 255))
        self.buffer.blit(class_value, (option_x + 180, option_y))
        self.prev_class_button.draw(self.buffer)
        self.next_class_button.draw(self.buffer)
        
        # 绘制发型选择
        option_y += option_spacing
        hair_text = name_font.render("发型:", True, (255, 255, 255))
        self.buffer.blit(hair_text, (option_x, option_y))
        
        # 发型选择按钮
        self.prev_hair_button = SimpleButton(
            option_x + 100,
            option_y,
            button_width,
            button_height,
            "<",
            color=(60, 60, 140),
            font_size=32
        )
        self.next_hair_button = SimpleButton(
            option_x + 300,
            option_y,
            button_width,
            button_height,
            ">",
            color=(60, 60, 140),
            font_size=32
        )
        hair_value = name_font.render(HAIRSTYLES[self.character_creator.hairstyle_index], True, (255, 255, 255))
        self.buffer.blit(hair_value, (option_x + 180, option_y))
        self.prev_hair_button.draw(self.buffer)
        self.next_hair_button.draw(self.buffer)
        
        # 绘制体型选择
        option_y += option_spacing
        body_text = name_font.render("体型:", True, (255, 255, 255))
        self.buffer.blit(body_text, (option_x, option_y))
        
        # 体型选择按钮
        self.prev_body_button = SimpleButton(
            option_x + 100,
            option_y,
            button_width,
            button_height,
            "<",
            color=(60, 60, 140),
            font_size=32
        )
        self.next_body_button = SimpleButton(
            option_x + 300,
            option_y,
            button_width,
            button_height,
            ">",
            color=(60, 60, 140),
            font_size=32
        )
        body_value = name_font.render(BODY_TYPES[self.character_creator.body_type_index], True, (255, 255, 255))
        self.buffer.blit(body_value, (option_x + 180, option_y))
        self.prev_body_button.draw(self.buffer)
        self.next_body_button.draw(self.buffer)
        
        # 绘制肤色选择
        option_y += option_spacing
        color_text = name_font.render("肤色:", True, (255, 255, 255))
        self.buffer.blit(color_text, (option_x, option_y))
        
        # 调整滑块位置
        slider_x = option_x + 100
        slider_y = option_y + 5
        slider_spacing = 50
        for i, slider in enumerate(self.character_creator.color_sliders):
            slider.rect.x = slider_x + i * slider_spacing
            slider.rect.y = slider_y
            slider.draw(self.buffer)
        
        # 绘制角色预览区域
        preview_rect = pygame.Rect(panel_x + panel_width - 250, panel_y + 50, 200, 300)
        pygame.draw.rect(self.buffer, (30, 30, 30), preview_rect)
        pygame.draw.rect(self.buffer, (100, 100, 100), preview_rect, 2)
        
        # 创建预览角色
        preview_data = {
            "name": self.character_creator.name or "预览角色",
            "hairstyle": HAIRSTYLES[self.character_creator.hairstyle_index],
            "body_type": BODY_TYPES[self.character_creator.body_type_index],
            "class": CLASSES[self.character_creator.class_index],
            "skin_color": [int(s.value) for s in self.character_creator.color_sliders],
            "health": 100,
            "mana": 100,
            "inventory": []  # 添加库存字段
        }
        
        # 如果没有预览角色或需要更新
        if not hasattr(self, 'preview_player') or self.needs_redraw:
            self.preview_player = Player(
                preview_rect.centerx - 24,
                preview_rect.centery - 32,
                preview_data
            )
            self.preview_player.preview_mode = True
        else:
            # 更新现有预览角色的属性
            self.preview_player.hairstyle = preview_data["hairstyle"]
            self.preview_player.body_type = preview_data["body_type"]
            self.preview_player.class_type = preview_data["class"]
            self.preview_player.skin_color = preview_data["skin_color"]
        
        # 强制更新外观
        self.preview_player.update_appearance()
        self.buffer.blit(self.preview_player.image, self.preview_player.rect)
        
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

    def handle_character_create_events(self, event):
        """处理角色创建界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event, self):
                self.game_state = "character_select"
                self.needs_redraw = True
                return
            
            # 检查创建按钮
            if self.create_button.handle_event(event, self):
                if self.character_creator.name:
                    character_data = {
                        "name": self.character_creator.name,
                        "hairstyle": HAIRSTYLES[self.character_creator.hairstyle_index],
                        "body_type": BODY_TYPES[self.character_creator.body_type_index],
                        "class": CLASSES[self.character_creator.class_index],
                        "skin_color": [int(s.value) for s in self.character_creator.color_sliders],
                        "health": 100,
                        "mana": 100,
                        "inventory": []
                    }
                    self.save_character(character_data["name"], character_data)
                    self.characters.append(character_data["name"])
                    self.game_state = "character_select"
                    self.needs_redraw = True
                return
            
            # 检查职业选择按钮
            if self.prev_class_button.handle_event(event, self):
                self.character_creator.class_index = (self.character_creator.class_index - 1) % len(CLASSES)
                self.needs_redraw = True
                return
            if self.next_class_button.handle_event(event, self):
                self.character_creator.class_index = (self.character_creator.class_index + 1) % len(CLASSES)
                self.needs_redraw = True
                return
            
            if self.prev_hair_button.handle_event(event, self):
                self.character_creator.hairstyle_index = (self.character_creator.hairstyle_index - 1) % len(HAIRSTYLES)
                self.needs_redraw = True
                return
            if self.next_hair_button.handle_event(event, self):
                self.character_creator.hairstyle_index = (self.character_creator.hairstyle_index + 1) % len(HAIRSTYLES)
                self.needs_redraw = True
                return
            
            if self.prev_body_button.handle_event(event, self):
                self.character_creator.body_type_index = (self.character_creator.body_type_index - 1) % len(BODY_TYPES)
                self.needs_redraw = True
                return
            if self.next_body_button.handle_event(event, self):
                self.character_creator.body_type_index = (self.character_creator.body_type_index + 1) % len(BODY_TYPES)
                self.needs_redraw = True
                return
            
            # 检查名称输入框
            name_rect = pygame.Rect(
                self.screen_width//2 - 400 + 150,
                120 + 30,
                300,
                40
            )
            self.character_creator.name_active = name_rect.collidepoint(event.pos)
            
            # 检查颜色滑块
            for slider in self.character_creator.color_sliders:
                if slider.handle_event(event, self):  # 传入self作为game参数
                    self.needs_redraw = True
                    return
            
        elif event.type == pygame.MOUSEBUTTONUP:
            # 处理滑块的鼠标释放事件
            for slider in self.character_creator.color_sliders:
                if slider.handle_event(event, self):
                    self.needs_redraw = True
                    return
            
        elif event.type == pygame.MOUSEMOTION:
            # 处理滑块的鼠标移动事件
            for slider in self.character_creator.color_sliders:
                if slider.handle_event(event, self):
                    self.needs_redraw = True
                    return
            
        elif event.type == pygame.KEYDOWN and self.character_creator.name_active:
            if event.key == pygame.K_RETURN:
                self.character_creator.name_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.character_creator.name = self.character_creator.name[:-1]
                self.needs_redraw = True
            elif len(self.character_creator.name) < 20:  # 限制名称长度
                if event.unicode.isprintable():
                    self.character_creator.name += event.unicode
                    self.needs_redraw = True

    def show_popup(self, message):
        """显示弹出提示"""
        self.popup_message = message
        self.needs_redraw = True
    
    def draw_popup(self):
        """绘制弹出提示"""
        if self.popup_message:
            # 创建半透明的背景
            popup_surface = pygame.Surface((400, 100), pygame.SRCALPHA)
            pygame.draw.rect(popup_surface, (0, 0, 0, 180), popup_surface.get_rect(), border_radius=10)
            
            # 渲染文本
            font = get_font(32)
            text = font.render(self.popup_message, True, (255, 255, 255))
            text_rect = text.get_rect(center=(200, 50))
            popup_surface.blit(text, text_rect)
            
            # 绘制关闭按钮（X）
            close_size = 20
            close_margin = 10
            close_x = 400 - close_size - close_margin
            close_y = close_margin
            
            # 绘制关闭按钮的圆形背景
            pygame.draw.circle(popup_surface, (80, 80, 80), (close_x + close_size//2, close_y + close_size//2), close_size//2)
            
            # 绘制X
            line_color = (200, 200, 200)
            line_margin = 6
            pygame.draw.line(popup_surface, line_color,
                (close_x + line_margin, close_y + line_margin),
                (close_x + close_size - line_margin, close_y + close_size - line_margin), 2)
            pygame.draw.line(popup_surface, line_color,
                (close_x + line_margin, close_y + close_size - line_margin),
                (close_x + close_size - line_margin, close_y + line_margin), 2)
            
            # 保存关闭按钮的位置信息用于点击检测
            popup_x = (self.screen_width - 400) // 2
            popup_y = (self.screen_height - 100) // 2
            self.popup_close_rect = pygame.Rect(
                popup_x + close_x,
                popup_y + close_y,
                close_size,
                close_size
            )
            
            # 在屏幕中央显示
            self.buffer.blit(popup_surface, (popup_x, popup_y))

    def draw_settings(self):
        """绘制设置界面"""
        # 清空缓冲区并填充深蓝色背景
        self.buffer.fill((20, 20, 40))
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("设置", True, (200, 200, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 创建设置面板（蓝色半透明面板）
        panel_width = self.screen_width * 0.8
        panel_height = self.screen_height * 0.7
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 120
        
        # 绘制设置面板背景
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (50, 50, 120, 200), (0, 0, panel_width, panel_height), border_radius=10)
        self.buffer.blit(panel_surface, (panel_x, panel_y))
        
        # 设置选项的起始位置和间距
        option_x = panel_x + 50
        option_y = panel_y + 50
        option_spacing = 60
        
        # 绘制按键设置标题
        settings_font = get_font(36)
        key_settings_title = settings_font.render("按键设置", True, (255, 255, 255))
        self.buffer.blit(key_settings_title, (option_x, option_y))
        
        # 绘制每个按键设置选项
        key_font = get_font(32)
        option_y += 50
        for action, key in self.key_bindings.items():
            # 绘制动作名称
            action_text = key_font.render(f"{self.action_names[action]}:", True, (200, 200, 255))
            self.buffer.blit(action_text, (option_x, option_y))
            
            # 绘制按键名称
            key_name = pygame.key.name(key).upper()
            key_text = key_font.render(key_name, True, (255, 255, 255))
            self.buffer.blit(key_text, (option_x + 200, option_y))
            
            option_y += option_spacing
        
        # 绘制返回按钮
        self.back_button = SimpleButton(
            panel_x,
            self.screen_height - 100,
            200,
            60,
            "返回",
            color=(60, 60, 140),
            font_size=36
        )
        self.back_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_settings_events(self, event):
        """处理设置界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button.handle_event(event, self):  # 传入self作为game参数
                self.game_state = self.previous_state if hasattr(self, 'previous_state') else "main_menu"
                self.needs_redraw = True
                return

if __name__ == "__main__":
    game = Game()
    game.run()