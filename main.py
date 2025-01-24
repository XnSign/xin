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

# 字体设置
def get_font(size):
    try:
        return pygame.font.Font("msyh.ttc", size)  # 微软雅黑
    except:
        try:
            return pygame.font.Font("simhei.ttf", size)  # 黑体
        except:
            return pygame.font.SysFont("microsoftyaheui", size)  # 系统字体

def get_documents_path():
    """获取当前用户的文档文件夹路径"""
    if os.name == 'nt':  # Windows
        import ctypes.wintypes
        CSIDL_PERSONAL = 5  # My Documents
        SHGFP_TYPE_CURRENT = 0  # Get current, not default value
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
        return buf.value
    else:  # Linux/Mac
        return os.path.expanduser('~/Documents')

def ensure_game_directories():
    """确保游戏所需的目录存在"""
    docs_path = get_documents_path()
    base_path = os.path.join(docs_path, 'My Games', 'TrFk')
    player_path = os.path.join(base_path, 'Player')
    world_path = os.path.join(base_path, 'World')
    
    # 创建所需的目录
    os.makedirs(player_path, exist_ok=True)
    os.makedirs(world_path, exist_ok=True)
    
    return player_path, world_path

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
        if self.is_clicked:
            bg_color = tuple(max(c - 30, 0) for c in self.color)  # 点击时颜色变暗
        elif self.is_hovered:
            bg_color = tuple(min(c + 30, 255) for c in self.color)  # 悬停时颜色变亮
        else:
            bg_color = self.color
            
        # 绘制按钮背景（带圆角）
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        
        # 绘制文本
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            return False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
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
        
        # 设置窗口
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("TrFk")  # 修改窗口标题
        
        # 创建缓冲区
        self.buffer = pygame.Surface((self.screen_width, self.screen_height))
        
        # 初始化时钟和帧率
        self.clock = pygame.time.Clock()
        self.fps = 60  # 设置游戏帧率为60
        
        # 游戏状态
        self.game_state = "main_menu"  # main_menu, character_select, character_create, map_select, playing, settings
        self.last_game_state = "main_menu"
        self.running = True
        self.needs_redraw = True
        self.is_fullscreen = False
        self.volume = 1.0
        
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
        self.maps = []
        self.selected_character = None
        self.selected_map = None
        self.map_name_input = ""
        self.map_name_active = False
        self.map_name_error = False
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

    def run(self):
        """游戏主循环"""
        while self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                    
                # 根据游戏状态处理事件
                if self.game_state == "main_menu":
                    self.handle_menu_events(event)
                elif self.game_state == "character_select":
                    self.handle_character_select_events(event)
                elif self.game_state == "character_create":
                    self.handle_character_create_events(event)
                elif self.game_state == "map_select":
                    self.handle_map_select_events(event)
                elif self.game_state == "credits":
                    self.handle_credits_events(event)
                elif self.game_state == "settings":
                    self.handle_settings_events(event)
                elif self.game_state == "playing":
                    self.handle_events(event)
            
            # 更新游戏状态
            if self.game_state == "playing" and hasattr(self, 'player'):
                self.player.update(self.world, self.key_bindings)
                self.update_camera()
            
            # 绘制界面
            if self.needs_redraw:
                if self.game_state == "main_menu":
                    self.draw_menu()
                elif self.game_state == "character_select":
                    self.draw_character_select()
                elif self.game_state == "character_create":
                    self.draw_character_create()
                elif self.game_state == "map_select":
                    self.draw_map_select()
                elif self.game_state == "credits":
                    self.draw_credits()
                elif self.game_state == "settings":
                    self.draw_settings()
                elif self.game_state == "playing":
                    self.draw_game()
            
            # 控制帧率
            self.clock.tick(self.fps)
            # 更新窗口标题显示FPS
            pygame.display.set_caption(f"TrFk - FPS: {int(self.clock.get_fps())}")
            
            # 更新显示
            pygame.display.flip()

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
                self.choosing_map_size = True
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
                    entry_rect = pygame.Rect(panel_x, entry_y, panel_width - 40, entry_height)
                    
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
        """处理主菜单界面的事件"""
        # 如果消息框可见，优先处理消息框事件
        if self.message_box and self.message_box.visible:
            if self.message_box.handle_event(event):
                self.needs_redraw = True
                return
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查单人模式按钮
            if self.menu_buttons['singleplayer'].handle_event(event):
                self.game_state = "character_select"
                self.needs_redraw = True
                return
            
            # 检查多人模式按钮
            if self.menu_buttons['multiplayer'].handle_event(event):
                self.show_message("多人模式暂未开放")
                return
            
            # 检查成就按钮
            if self.menu_buttons['achievements'].handle_event(event):
                self.show_message("成就系统暂未开放")
                return
                
            # 检查创意工坊按钮
            if self.menu_buttons['workshop'].handle_event(event):
                self.show_message("创意工坊暂未开放")
                return
                
            # 检查设置按钮
            if self.menu_buttons['settings'].handle_event(event):
                self.game_state = "settings"
                self.needs_redraw = True
                return
            
            # 检查制作人员按钮
            if self.menu_buttons['credits'].handle_event(event):
                self.game_state = "credits"
                self.needs_redraw = True
                return
            
            # 检查退出游戏按钮
            if self.menu_buttons['exit'].handle_event(event):
                self.running = False
                return

    def draw_character_create(self):
        """绘制角色创建界面"""
        # 清空缓冲区
        self.buffer.fill(SKY_BLUE)
        
        # 绘制角色创建器
        self.character_creator.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_character_create_events(self, event):
        """处理角色创建界面的事件"""
        # 将事件传递给角色创建器
        if self.character_creator.handle_event(event):
            # 如果返回了角色数据，说明创建完成
            character_data = self.character_creator.get_character_data()
            if character_data:
                # 保存角色数据
                self.save_character(character_data["name"], character_data)
                # 将新角色添加到列表中
                self.characters.append(character_data["name"])
                # 更新选择按钮
                self.update_selection_buttons()
                # 返回角色选择界面
                self.game_state = "character_select"
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
            for file in os.listdir(self.world_path):
                if file.endswith('.wld'):
                    map_name = file[:-4]  # 移除 .wld 后缀
                    self.maps.append(map_name)
        
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
        
        # 更新地图大小选择按钮
        self.map_size_buttons = [
            SimpleButton(
                self.screen_width//2 - 150,
                200 + i*80,
                300,
                60,
                size,
                font_size=32
            ) for i, size in enumerate(self.map_sizes.keys())
        ]
        
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
        # 清空缓冲区并填充天空蓝色背景
        self.buffer.fill((135, 206, 235))  # 天空蓝色背景
        
        # 绘制游戏标题
        title_font = get_font(72)
        title = title_font.render("TrFk", True, (139, 69, 19))  # 使用棕色
        title_rect = title.get_rect(centerx=self.screen_width//2, y=50)
        self.buffer.blit(title, title_rect)
        
        # 设置按钮的基本属性
        button_width = 300
        button_height = 50
        button_x = self.screen_width//2 - button_width//2
        button_y_start = 200
        button_spacing = 60
        
        # 重新创建所有主菜单按钮
        self.menu_buttons = {
            'singleplayer': SimpleButton(
                button_x,
                button_y_start,
                button_width,
                button_height,
                "单人模式",
                color=(100, 100, 100),
                font_size=36
            ),
            'multiplayer': SimpleButton(
                button_x,
                button_y_start + button_spacing,
                button_width,
                button_height,
                "多人模式",
                color=(100, 100, 100),
                font_size=36
            ),
            'achievements': SimpleButton(
                button_x,
                button_y_start + button_spacing * 2,
                button_width,
                button_height,
                "成就",
                color=(100, 100, 100),
                font_size=36
            ),
            'workshop': SimpleButton(
                button_x,
                button_y_start + button_spacing * 3,
                button_width,
                button_height,
                "创意工坊",
                color=(100, 100, 100),
                font_size=36
            ),
            'settings': SimpleButton(
                button_x,
                button_y_start + button_spacing * 4,
                button_width,
                button_height,
                "设置",
                color=(100, 100, 100),
                font_size=36
            ),
            'credits': SimpleButton(
                button_x,
                button_y_start + button_spacing * 5,
                button_width,
                button_height,
                "制作人员",
                color=(100, 100, 100),
                font_size=36
            ),
            'exit': SimpleButton(
                button_x,
                button_y_start + button_spacing * 6,
                button_width,
                button_height,
                "退出",
                color=(100, 100, 100),
                font_size=36
            )
        }
        
        # 绘制所有主菜单按钮
        for button in self.menu_buttons.values():
            button.draw(self.buffer)
        
        # 如果有消息框，绘制消息框
        if self.message_box and self.message_box.visible:
            self.message_box.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

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
            if self.back_button.handle_event(event):
                self.game_state = "main_menu"
                self.needs_redraw = True
                return
            
            # 检查新建角色按钮
            if self.new_character_button.handle_event(event):
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
                    entry_rect = pygame.Rect(panel_x, entry_y, panel_width, entry_height)
                    
                    if entry_rect.collidepoint(mouse_pos):
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

    def create_new_map(self, width, height, grid_size, name):
        """创建新地图并保存"""
        # 创建新的世界数据
        world_data = {
            'width': width,
            'height': height,
            'grid_size': grid_size,
            'grid': [[0 for _ in range(width)] for _ in range(height)]
        }
        
        # 生成地形
        self.generate_terrain(world_data['grid'])
        
        # 保存地图
        os.makedirs(self.world_path, exist_ok=True)
        map_file = os.path.join(self.world_path, f"{name}.wld")
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(world_data, f, ensure_ascii=False, indent=4)
        
        return name
        
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

if __name__ == "__main__":
    game = Game()
    game.run()