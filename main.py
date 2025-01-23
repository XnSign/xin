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
CLASSES = ["战士", "法师", "弓箭手"]

# 发型选项
HAIRSTYLES = [f"发型{i+1}" for i in range(10)]

# 体型选项
BODY_TYPES = ["瘦小", "普通", "魁梧"]

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
    def __init__(self, x, y, width, height, min_value, max_value, initial_value, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.label = label
        self.is_dragging = False
        
    def draw(self, screen):
        # 绘制滑动条标签
        label_font = get_font(28)
        label_text = label_font.render(f"{self.label}: {int(self.value)}", True, WHITE)
        screen.blit(label_text, (self.rect.x, self.rect.y - 30))
        
        # 绘制滑动条背景
        pygame.draw.rect(screen, (60, 60, 60), self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        
        # 计算滑块位置
        slider_x = self.rect.x + (self.value - self.min_value) / (self.max_value - self.min_value) * self.rect.width
        slider_rect = pygame.Rect(slider_x - 10, self.rect.y - 5, 20, self.rect.height + 10)
        
        # 绘制滑块
        if self.is_dragging:
            pygame.draw.rect(screen, (200, 200, 200), slider_rect, border_radius=5)
        else:
            pygame.draw.rect(screen, WHITE, slider_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100), slider_rect, 2, border_radius=5)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                # 检查是否点击了滑块区域
                slider_x = self.rect.x + (self.value - self.min_value) / (self.max_value - self.min_value) * self.rect.width
                slider_rect = pygame.Rect(slider_x - 10, self.rect.y - 5, 20, self.rect.height + 10)
                if slider_rect.collidepoint(event.pos):
                    self.is_dragging = True
                    return True
                # 检查是否点击了滑动条
                elif self.rect.collidepoint(event.pos):
                    self.update_value(event.pos[0])
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_dragging:  # 左键释放
                self.is_dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self.update_value(event.pos[0])
            return True
        return False
        
    def update_value(self, x_pos):
        # 确保x_pos在滑动条范围内
        x_pos = max(self.rect.left, min(x_pos, self.rect.right))
        # 计算新的值
        self.value = self.min_value + (x_pos - self.rect.x) / self.rect.width * (self.max_value - self.min_value)
        # 确保值在范围内
        self.value = max(self.min_value, min(self.value, self.max_value))

class CharacterCreator:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.name = None
        self.name_active = False
        self.current_input = ""
        
        # 初始化滑动条
        slider_width = 250
        slider_height = 30
        slider_x = x + 80
        slider_y = y + 300
        spacing = 60
        
        self.color_sliders = [
            Slider(slider_x, slider_y, slider_width, slider_height, 0, 255, 128, "红色"),
            Slider(slider_x, slider_y + spacing, slider_width, slider_height, 0, 255, 128, "绿色"),
            Slider(slider_x, slider_y + spacing * 2, slider_width, slider_height, 0, 255, 128, "蓝色")
        ]
        
        # 选择按钮
        button_width = 40
        button_height = 40
        text_width = 150
        button_spacing = 50
        
        # 发型选择按钮
        self.hairstyle_index = 0
        self.hairstyle_prev = SimpleButton(
            x + 180,
            y + 160,
            button_width,
            button_height,
            "<",
            font_size=32
        )
        self.hairstyle_next = SimpleButton(
            x + 180 + text_width + button_width,
            y + 160,
            button_width,
            button_height,
            ">",
            font_size=32
        )
        
        # 体型选择按钮
        self.body_type_index = 1
        self.body_prev = SimpleButton(
            x + 180,
            y + 160 + button_spacing,
            button_width,
            button_height,
            "<",
            font_size=32
        )
        self.body_next = SimpleButton(
            x + 180 + text_width + button_width,
            y + 160 + button_spacing,
            button_width,
            button_height,
            ">",
            font_size=32
        )
        
        # 职业选择按钮
        self.class_index = 0
        self.class_prev = SimpleButton(
            x + 180,
            y + 160 + button_spacing * 2,
            button_width,
            button_height,
            "<",
            font_size=32
        )
        self.class_next = SimpleButton(
            x + 180 + text_width + button_width,
            y + 160 + button_spacing * 2,
            button_width,
            button_height,
            ">",
            font_size=32
        )
        
        # 确认和取消按钮
        button_y = y + height - 80
        self.confirm_button = SimpleButton(
            x + width//4 - 60,
            button_y,
            120,
            50,
            "确认",
            color=(0, 200, 0),
            font_size=32
        )
        self.cancel_button = SimpleButton(
            x + width*3//4 - 60,
            button_y,
            120,
            50,
            "取消",
            color=(200, 0, 0),
            font_size=32
        )
        
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.KEYDOWN:
            if self.name is None:  # 只有当名称还未设置时才允许输入
                if event.key == pygame.K_RETURN:
                    # 确认名称输入，如果输入不为空则设置名称
                    if self.current_input:
                        self.name = self.current_input
                        self.current_input = ""
                        return True
                elif event.key == pygame.K_BACKSPACE:
                    self.current_input = self.current_input[:-1]
                    return True
                elif len(self.current_input) < 10:  # 限制名称长度
                    if event.unicode.isprintable():
                        self.current_input += event.unicode
                        return True
            return False
            
        # 处理按钮点击
        if self.confirm_button.handle_event(event):
            if self.name:  # 只有当名称已设置时才允许确认
                return "confirm"
            else:
                print("请先输入并确认角色名称（按回车键确认）")
        elif self.cancel_button.handle_event(event):
            return "cancel"
            
        # 处理滑块
        for slider in self.color_sliders:
            if slider.handle_event(event):
                return True
                
        # 处理其他按钮
        if self.hairstyle_prev.handle_event(event):
            self.hairstyle_index = (self.hairstyle_index - 1) % len(HAIRSTYLES)
            return True
        elif self.hairstyle_next.handle_event(event):
            self.hairstyle_index = (self.hairstyle_index + 1) % len(HAIRSTYLES)
            return True
        elif self.body_prev.handle_event(event):
            self.body_type_index = (self.body_type_index - 1) % len(BODY_TYPES)
            return True
        elif self.body_next.handle_event(event):
            self.body_type_index = (self.body_type_index + 1) % len(BODY_TYPES)
            return True
        elif self.class_prev.handle_event(event):
            self.class_index = (self.class_index - 1) % len(CLASSES)
            return True
        elif self.class_next.handle_event(event):
            self.class_index = (self.class_index + 1) % len(CLASSES)
            return True
            
        return False
        
    def draw(self, screen):
        """绘制角色创建界面"""
        # 创建预览玩家数据
        preview_data = {
            "name": self.name or "预览角色",
            "hairstyle": HAIRSTYLES[self.hairstyle_index],
            "body_type": BODY_TYPES[self.body_type_index],
            "class": CLASSES[self.class_index],
            "skin_color": [int(s.value) for s in self.color_sliders],
            "health": 100,  # 添加默认生命值
            "mana": 100,    # 添加默认魔法值
            "inventory": [] # 添加空物品栏
        }
        
        # 创建预览玩家
        preview_player = Player(
            self.rect.centerx,
            self.rect.centery,
            preview_data
        )
        
        # 创建半透明背景
        overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        overlay.fill((50, 50, 50, 200))  # 深灰色半透明背景
        screen.blit(overlay, self.rect)
        
        # 绘制标题
        title_font = get_font(48)
        title_text = title_font.render("创建角色", True, WHITE)
        title_rect = title_text.get_rect(center=(self.rect.centerx, self.rect.y + 40))
        screen.blit(title_text, title_rect)
        
        # 绘制名称输入框
        name_font = get_font(32)
        name_text = name_font.render("名称:", True, WHITE)
        screen.blit(name_text, (self.rect.x + 80, self.rect.y + 100))
        
        name_rect = pygame.Rect(self.rect.x + 180, self.rect.y + 100, 250, 40)
        pygame.draw.rect(screen, (60, 60, 60) if self.name_active else (40, 40, 40), name_rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, name_rect, 2, border_radius=5)
        
        # 绘制名称文本
        display_text = self.current_input if self.name is None else self.name
        cursor = "_" if self.name is None and pygame.time.get_ticks() % 1000 < 500 else ""
        name_surface = name_font.render(display_text + cursor, True, WHITE)
        screen.blit(name_surface, (name_rect.x + 10, name_rect.y + 5))
        
        # 绘制发型选择
        hairstyle_text = name_font.render(f"发型: {HAIRSTYLES[self.hairstyle_index]}", True, WHITE)
        text_rect = hairstyle_text.get_rect(midright=(self.hairstyle_prev.rect.left - 20, self.hairstyle_prev.rect.centery))
        screen.blit(hairstyle_text, text_rect)
        self.hairstyle_prev.draw(screen)
        self.hairstyle_next.draw(screen)
        
        # 绘制体型选择
        body_text = name_font.render(f"体型: {BODY_TYPES[self.body_type_index]}", True, WHITE)
        text_rect = body_text.get_rect(midright=(self.body_prev.rect.left - 20, self.body_prev.rect.centery))
        screen.blit(body_text, text_rect)
        self.body_prev.draw(screen)
        self.body_next.draw(screen)
        
        # 绘制职业选择
        class_text = name_font.render(f"职业: {CLASSES[self.class_index]}", True, WHITE)
        text_rect = class_text.get_rect(midright=(self.class_prev.rect.left - 20, self.class_prev.rect.centery))
        screen.blit(class_text, text_rect)
        self.class_prev.draw(screen)
        self.class_next.draw(screen)
        
        # 绘制肤色滑动条
        for slider in self.color_sliders:
            slider.draw(screen)
        
        # 绘制角色预览区域
        preview_rect = pygame.Rect(self.rect.right - 300, self.rect.y + 80, 250, 350)
        pygame.draw.rect(screen, (60, 60, 60), preview_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, preview_rect, 2, border_radius=10)
        
        # 绘制角色预览
        preview_player.preview_mode = True
        preview_player.draw_character()
        screen.blit(preview_player.image, preview_player.rect)
        
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

class Game:
    def __init__(self):
        """初始化游戏"""
        pygame.init()
        
        # 设置窗口
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("2D冒险游戏")
        
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
            'start': SimpleButton(
                self.screen_width//2 - 200,
                300,
                400,
                80,
                "开始游戏",
                color=(0, 200, 0),
                font_size=48
            ),
            'exit': SimpleButton(
                self.screen_width//2 - 200,
                400,
                400,
                80,
                "退出游戏",
                color=(200, 0, 0),
                font_size=48
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
            "小型": {"width": 1280, "height": 720, "grid_size": 32},
            "中型": {"width": 2560, "height": 1440, "grid_size": 32},
            "大型": {"width": 3840, "height": 2160, "grid_size": 32}
        }
        
        # 按键绑定
        self.key_bindings = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'jump': pygame.K_SPACE,
            'exit': pygame.K_ESCAPE
        }
        
        # 按键名称映射
        self.action_names = {
            'left': '向左移动',
            'right': '向右移动',
            'jump': '跳跃',
            'exit': '退出/背包'
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
        self.player_path = "players"
        self.world_path = "worlds"
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

    def run(self):
        """游戏主循环"""
        while self.running:
            # 处理事件
            if self.game_state == "main_menu":
                self.handle_events()
                if self.needs_redraw:
                    self.draw_menu()
            elif self.game_state == "character_select":
                self.handle_character_select_events()
                if self.needs_redraw:
                    self.draw_character_select()
            elif self.game_state == "character_create":
                self.handle_character_create_events()
                if self.needs_redraw:
                    self.draw_character_create()
            elif self.game_state == "map_select":
                self.handle_map_select_events()
                if self.needs_redraw:
                    self.draw_map_select()
            elif self.game_state == "playing":
                self.handle_events()
                # 更新游戏状态
                if hasattr(self, 'player'):
                    self.player.update(self.world, self.key_bindings)
                    self.update_camera()
                # 绘制游戏界面
                if self.needs_redraw:
                    self.draw_game()
            
            # 检查游戏状态变化
            if self.game_state != self.last_game_state:
                self.needs_redraw = True
                self.last_game_state = self.game_state
            
            # 控制帧率
            self.clock.tick(self.fps)

    def draw_map_select(self):
        """绘制地图选择界面"""
        # 填充背景
        self.buffer.fill(SKY_BLUE)
        
        # 绘制标题
        title = get_font(64).render("选择地图", True, BLACK)
        title_rect = title.get_rect(center=(self.screen_width//2, 100))
        self.buffer.blit(title, title_rect)
        
        if self.choosing_map_size:
            # 绘制地图名称输入框
            name_text = get_font(36).render("地图名称:", True, BLACK)
            name_rect = name_text.get_rect(center=(self.screen_width//2, 180))
            self.buffer.blit(name_text, name_rect)
            
            # 绘制输入框
            input_rect = pygame.Rect(self.screen_width//2 - 150, 220, 300, 40)
            pygame.draw.rect(self.buffer, (60, 60, 60) if self.map_name_active else (40, 40, 40), input_rect, border_radius=5)
            pygame.draw.rect(self.buffer, WHITE, input_rect, 2, border_radius=5)
            
            # 绘制输入的文本
            cursor = "_" if pygame.time.get_ticks() % 1000 < 500 and self.map_name_active else ""
            input_text = get_font(32).render(self.map_name_input + cursor, True, WHITE)
            self.buffer.blit(input_text, (input_rect.x + 10, input_rect.y + 5))
            
            # 如果有错误消息，显示它
            if self.map_name_error:
                error_text = get_font(24).render("请输入地图名称！", True, (255, 0, 0))
                error_rect = error_text.get_rect(center=(self.screen_width//2, 280))
                self.buffer.blit(error_text, error_rect)
            
            # 绘制地图大小选择区域
            size_text = get_font(36).render("选择地图大小:", True, BLACK)
            size_rect = size_text.get_rect(center=(self.screen_width//2, 320))
            self.buffer.blit(size_text, size_rect)
            
            # 绘制地图大小按钮
            button_y = 380
            for i, (size_name, size_data) in enumerate(self.map_sizes.items()):
                button = SimpleButton(
                    self.screen_width//2 - 150,
                    button_y + i*80,
                    300,
                    60,
                    size_name,
                    font_size=32
                )
                button.draw(self.buffer)
                if size_name == self.selected_map_size:
                    pygame.draw.rect(self.buffer, (0, 255, 0), button.rect, 3)
        else:
            # 绘制新建地图按钮
            self.new_map_button = SimpleButton(
                self.screen_width//2 - 150,
                200,
                300,
                60,
                "新建地图",
                color=(0, 200, 0),
                font_size=32
            )
            self.new_map_button.draw(self.buffer)
            
            # 绘制现有地图列表标题
            if self.maps:
                maps_title = get_font(36).render("现有地图:", True, BLACK)
                maps_title_rect = maps_title.get_rect(center=(self.screen_width//2, 300))
                self.buffer.blit(maps_title, maps_title_rect)
                
                # 绘制地图列表
                map_list_y = 350
                for i, map_name in enumerate(self.maps):
                    # 创建地图选择按钮
                    map_button = SimpleButton(
                        self.screen_width//2 - 200,
                        map_list_y + i*60,
                        300,
                        50,
                        f"地图 {i+1}",
                        color=(100, 100, 200),
                        font_size=32
                    )
                    map_button.draw(self.buffer)
                    
                    # 绘制删除按钮
                    if i < len(self.map_delete_buttons):
                        self.map_delete_buttons[i].draw(self.buffer)
        
        # 绘制返回按钮
        self.back_button = SimpleButton(
            50,
            self.screen_height - 100,
            200,
            80,
            "返回",
            color=(200, 100, 0),
            font_size=36
        )
        self.back_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_map_select_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                
                # 处理返回按钮
                if self.back_button.handle_event(event):
                    if self.choosing_map_size:
                        self.choosing_map_size = False
                        self.map_name_input = ""
                        self.map_name_error = False
                    else:
                        self.game_state = "character_select"
                    self.needs_redraw = True
                    return
                
                if not self.choosing_map_size:
                    # 处理新建地图按钮
                    if self.new_map_button.handle_event(event):
                        self.choosing_map_size = True
                        self.needs_redraw = True
                        return
                        
                    # 检查地图选择按钮
                    map_list_y = 350
                    for i, map_name in enumerate(self.maps):
                        map_button_rect = pygame.Rect(
                            self.screen_width//2 - 200,
                            map_list_y + i*60,
                            300,
                            50
                        )
                        if map_button_rect.collidepoint(mouse_pos):
                            print(f"选择了地图: {map_name}")
                            self.selected_map = map_name
                            self.initialize_game()
                            return
                        
                    # 检查地图删除按钮
                    for i, map_name in enumerate(self.maps):
                        if self.map_delete_buttons[i].handle_event(event):
                            self.delete_map(map_name)
                            self.needs_redraw = True
                            return
                else:
                    # 检查是否点击了输入框
                    input_rect = pygame.Rect(self.screen_width//2 - 150, 220, 300, 40)
                    self.map_name_active = input_rect.collidepoint(mouse_pos)
                    
                    # 检查地图大小选择按钮
                    button_y = 380
                    for i, (size_name, size_data) in enumerate(self.map_sizes.items()):
                        button_rect = pygame.Rect(
                            self.screen_width//2 - 150,
                            button_y + i*80,
                            300,
                            60
                        )
                        if button_rect.collidepoint(mouse_pos):
                            if not self.map_name_input.strip():
                                self.map_name_error = True
                                self.needs_redraw = True
                                return
                                
                            self.map_name_error = False
                            self.selected_map_size = size_name
                            # 创建新地图
                            new_map = self.create_new_map(
                                size_data["width"],
                                size_data["height"],
                                size_data["grid_size"],
                                self.map_name_input.strip()
                            )
                            self.maps.append(new_map)
                            self.selected_map = new_map
                            self.initialize_game()
                            return
            elif event.type == pygame.KEYDOWN:
                if self.choosing_map_size and self.map_name_active:
                    if event.key == pygame.K_RETURN:
                        self.map_name_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.map_name_input = self.map_name_input[:-1]
                        self.needs_redraw = True
                    elif len(self.map_name_input) < 20:  # 限制名称长度
                        if event.unicode.isprintable():
                            self.map_name_input += event.unicode
                            self.needs_redraw = True

    def handle_events(self):
        """处理游戏主界面的事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # 处理设置界面的事件
            if self.game_state == "settings":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game_state = "playing"
                    self.needs_redraw = True
                    return
                self.handle_settings_events(event)
            mouse_pos = pygame.mouse.get_pos()
                
            # 处理主菜单界面的事件
            if self.game_state == "main_menu":
                self.handle_menu_events(event)
                return
                
            # 处理按键事件
            if event.type == pygame.KEYDOWN:
                # ESC 键打开/关闭背包
                if event.key == self.key_bindings['exit']:
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
                    
            # 处理鼠标事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # 检查是否点击了设置按钮
                if self.settings_button.rect.collidepoint(mouse_pos):
                    self.game_state = "settings"
                    self.needs_redraw = True
                    return
                
                # 如果背包可见，检查是否点击了背包槽位
                if self.inventory.visible:
                    if self.inventory.handle_click(event.pos):
                        self.needs_redraw = True
                        return
                        
                # 左键放置方块，右键破坏方块
                if event.button == 1:  # 左键
                    self.place_block(event.pos)
                elif event.button == 3:  # 右键
                    self.break_block(event.pos)
                    
    def handle_menu_events(self, event):
        """处理主菜单界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # 检查开始游戏按钮
            if self.menu_buttons['start'].rect.collidepoint(mouse_pos):
                self.game_state = "character_select"
                self.needs_redraw = True
                return
            
            # 检查退出游戏按钮
            if self.menu_buttons['exit'].rect.collidepoint(mouse_pos):
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

    def handle_character_create_events(self):
        """处理角色创建界面的事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # 处理角色创建器的事件
            result = self.character_creator.handle_event(event)
            if result:
                if result == "confirm":
                    # 获取角色数据
                    character_data = self.character_creator.get_character_data()
                    if character_data:  # 如果角色数据有效
                        # 保存角色
                        self.save_character(character_data['name'], character_data)
                        
                        # 添加到角色列表
                        if character_data['name'] not in self.characters:
                            self.characters.append(character_data['name'])
                        
                        # 更新选择按钮
                        self.update_selection_buttons()
                        
                        # 返回角色选择界面
                        self.game_state = "character_select"
                        self.needs_redraw = True
                    
                elif result == "cancel":
                    # 返回角色选择界面
                    self.game_state = "character_select"
                    self.needs_redraw = True
                else:
                    # 其他事件导致需要重绘
                    self.needs_redraw = True

    def draw_settings(self):
        """绘制设置界面"""
        if self.game_state != "settings":
            return
            
        # 绘制半透明背景
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.buffer.blit(overlay, (0, 0))
        
        # 设置面板尺寸和位置
        settings_width = 500
        settings_height = 400
        settings_x = (self.screen_width - settings_width) // 2
        settings_y = (self.screen_height - settings_height) // 2
        
        # 绘制设置面板背景
        settings_rect = pygame.Rect(settings_x, settings_y, settings_width, settings_height)
        pygame.draw.rect(self.buffer, (50, 50, 50), settings_rect)
        pygame.draw.rect(self.buffer, (100, 100, 100), settings_rect, 2)
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("设置", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=settings_x + settings_width//2, y=settings_y + 20)
        self.buffer.blit(title, title_rect)
        
        # 绘制音量控制
        font = get_font(32)
        volume_text = font.render(f"音量: {int(self.volume * 100)}%", True, (255, 255, 255))
        self.buffer.blit(volume_text, (settings_x + 50, settings_y + 100))
        
        # 绘制音量滑块
        slider_width = 300
        slider_x = settings_x + 150
        slider_y = settings_y + 150
        pygame.draw.rect(self.buffer, (100, 100, 100), (slider_x, slider_y, slider_width, 10))
        pygame.draw.rect(self.buffer, (200, 200, 200), 
                        (slider_x + self.volume * slider_width - 5, slider_y - 5, 10, 20))
        
        # 绘制全屏按钮
        fullscreen_text = "全屏: " + ("开" if self.is_fullscreen else "关")
        fullscreen_color = (0, 255, 0) if self.is_fullscreen else (255, 0, 0)
        fullscreen_surface = font.render(fullscreen_text, True, fullscreen_color)
        self.settings_fullscreen_rect = fullscreen_surface.get_rect(
            centerx=settings_x + settings_width//2,
            centery=settings_y + 200
        )
        self.buffer.blit(fullscreen_surface, self.settings_fullscreen_rect)
        
        # 绘制退出游戏按钮
        exit_text = "退出游戏"
        exit_surface = font.render(exit_text, True, (255, 100, 100))
        self.settings_exit_rect = exit_surface.get_rect(
            centerx=settings_x + settings_width//2,
            centery=settings_y + 250
        )
        self.buffer.blit(exit_surface, self.settings_exit_rect)
        
        # 绘制退出到主菜单按钮
        menu_text = "返回主菜单"
        menu_surface = font.render(menu_text, True, (255, 200, 100))
        self.settings_menu_rect = menu_surface.get_rect(
            centerx=settings_x + settings_width//2,
            centery=settings_y + 300
        )
        self.buffer.blit(menu_surface, self.settings_menu_rect)
        
        # 绘制关闭按钮
        close_text = "×"
        close_surface = font.render(close_text, True, (255, 255, 255))
        self.settings_close_rect = close_surface.get_rect(
            topright=(settings_x + settings_width - 10, settings_y + 10)
        )
        self.buffer.blit(close_surface, self.settings_close_rect)

    def load_characters_and_maps(self):
        """加载已有的角色和地图"""
        # 加载角色
        self.characters = []
        if os.path.exists(self.player_path):
            for file in os.listdir(self.player_path):
                if file.endswith('.json'):
                    character_name = file[:-5]  # 移除 .json 后缀
                    self.characters.append(character_name)
        
        # 加载地图
        self.maps = []
        if os.path.exists(self.world_path):
            for file in os.listdir(self.world_path):
                if file.endswith('.json'):
                    map_name = file[:-5]  # 移除 .json 后缀
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
        
        # 绘制设置按钮（只在背包打开时显示）
        if hasattr(self, 'inventory') and self.inventory.visible:
            self.settings_button.draw(self.buffer)
        
        # 如果在设置状态，绘制设置菜单
        if self.game_state == "settings":
            self.draw_settings()
        
        # 绘制背包
        if hasattr(self, 'inventory'):
            if self.inventory.visible:
                self.inventory.draw(self.buffer, get_font(20))
            self.inventory.draw_hotbar(self.buffer, get_font(20))  # 始终显示物品栏
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def draw_menu(self):
        """绘制主菜单界面"""
        # 清空缓冲区
        self.buffer.fill((135, 206, 235))  # 天空蓝色背景
        
        # 绘制游戏标题
        title_font = get_font(72)
        title = title_font.render("2D冒险游戏", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=100)
        self.buffer.blit(title, title_rect)
        
        # 绘制所有主菜单按钮
        for button in self.menu_buttons.values():
            button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def draw_character_select(self):
        """绘制角色选择界面"""
        # 清空缓冲区
        self.buffer.fill((135, 206, 235))  # 天空蓝色背景
        
        # 绘制标题
        title_font = get_font(48)
        title = title_font.render("选择角色", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.screen_width//2, y=100)
        self.buffer.blit(title, title_rect)
        
        # 绘制新建角色按钮
        self.new_character_button.draw(self.buffer)
        
        # 绘制现有角色按钮
        for button in self.character_buttons:
            button.draw(self.buffer)
        
        # 绘制删除按钮
        for button in self.character_delete_buttons:
            button.draw(self.buffer)
        
        # 绘制返回按钮
        self.back_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_settings_events(self, event):
        """处理设置界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # 获取设置面板的位置
            settings_width = 500
            settings_height = 400
            settings_x = (self.screen_width - settings_width) // 2
            settings_y = (self.screen_height - settings_height) // 2
            
            # 检查是否点击了关闭按钮
            if hasattr(self, 'settings_close_rect') and self.settings_close_rect.collidepoint(mouse_pos):
                self.game_state = "playing"
                self.needs_redraw = True
                return
            
            # 检查是否点击了音量滑块
            slider_width = 300
            slider_rect = pygame.Rect(settings_x + 150, settings_y + 150, slider_width, 10)
            if slider_rect.collidepoint(mouse_pos):
                # 更新音量值
                self.volume = (mouse_pos[0] - (settings_x + 150)) / slider_width
                self.volume = max(0, min(1, self.volume))
                self.needs_redraw = True
                return
            
            # 检查是否点击了全屏按钮
            if hasattr(self, 'settings_fullscreen_rect') and self.settings_fullscreen_rect.collidepoint(mouse_pos):
                self.is_fullscreen = not self.is_fullscreen
                if self.is_fullscreen:
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                self.needs_redraw = True
                return
            
            # 检查是否点击了退出游戏按钮
            if hasattr(self, 'settings_exit_rect') and self.settings_exit_rect.collidepoint(mouse_pos):
                self.running = False
                return
            
            # 检查是否点击了返回主菜单按钮
            if hasattr(self, 'settings_menu_rect') and self.settings_menu_rect.collidepoint(mouse_pos):
                self.game_state = "main_menu"
                self.needs_redraw = True
                return
        
        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:  # 左键拖动
                mouse_pos = pygame.mouse.get_pos()
                settings_x = (self.screen_width - 500) // 2
                slider_width = 300
                slider_rect = pygame.Rect(settings_x + 150, settings_y + 150, slider_width, 10)
                if slider_rect.collidepoint(mouse_pos):
                    # 更新音量值
                    self.volume = (mouse_pos[0] - (settings_x + 150)) / slider_width
                    self.volume = max(0, min(1, self.volume))
                    self.needs_redraw = True

    def handle_character_select_events(self):
        """处理角色选择界面的事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # 检查返回按钮
                if self.back_button.rect.collidepoint(mouse_pos):
                    self.game_state = "main_menu"
                    self.needs_redraw = True
                    return
                
                # 检查新建角色按钮
                if self.new_character_button.rect.collidepoint(mouse_pos):
                    self.game_state = "character_create"
                    self.needs_redraw = True
                    return
                
                # 检查现有角色按钮
                for i, button in enumerate(self.character_buttons):
                    if button.rect.collidepoint(mouse_pos):
                        self.selected_character = self.characters[i]
                        self.game_state = "map_select"
                        self.needs_redraw = True
                        return
                
                # 检查删除按钮
                for i, button in enumerate(self.character_delete_buttons):
                    if button.rect.collidepoint(mouse_pos):
                        character_name = self.characters[i]
                        # 删除角色文件
                        character_file = os.path.join(self.player_path, f"{character_name}.json")
                        if os.path.exists(character_file):
                            os.remove(character_file)
                        # 从列表中移除
                        self.characters.remove(character_name)
                        # 更新按钮
                        self.update_selection_buttons()
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
        character_file = os.path.join(self.player_path, f"{name}.json")
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
        map_file = os.path.join(self.world_path, f"{name}.json")
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
            world_file = os.path.join(self.world_path, f"{self.selected_map}.json")
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
                print(f"找不到地图文件: {world_file}")
                return
        
        # 加载或创建玩家
        if self.selected_character:
            player_file = os.path.join(self.player_path, f"{self.selected_character}.json")
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
                print(f"找不到角色文件: {player_file}")
                return
        
        # 初始化摄像机位置
        self.camera_x = 0
        self.camera_y = 0
        
        # 创建物品栏
        inventory_x = 10  # 距离左边界10像素
        inventory_y = self.screen_height - 50  # 距离底部50像素
        self.inventory = Inventory(inventory_x, inventory_y)
        
        self.game_state = "playing"
        self.needs_redraw = True

if __name__ == "__main__":
    game = Game()
    game.run()