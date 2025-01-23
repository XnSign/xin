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
        
        # 创建一个临时的Player对象来预览角色
        preview_player = Player(
            preview_rect.centerx - 16,
            preview_rect.centery - 24,
            {
                "name": self.name if self.name else self.current_input,
                "hairstyle": HAIRSTYLES[self.hairstyle_index],
                "body_type": BODY_TYPES[self.body_type_index],
                "class": CLASSES[self.class_index],
                "skin_color": [int(s.value) for s in self.color_sliders]
            }
        )
        
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
        # 初始化 pygame
        pygame.init()
        
        # 初始化时钟和FPS
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 设置窗口
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("2D冒险游戏")
        
        # 创建缓冲区
        self.buffer = pygame.Surface((self.screen_width, self.screen_height))
        
        # 初始化按键绑定
        self.key_bindings = {
            'left': pygame.K_a,    # A键
            'right': pygame.K_d,   # D键
            'jump': pygame.K_SPACE, # 空格键
            'exit': pygame.K_ESCAPE  # ESC键
        }
        
        # 按键动作的中文名称
        self.action_names = {
            'left': '向左移动',
            'right': '向右移动',
            'jump': '跳跃',
            'exit': '退出'
        }
        
        # 游戏状态
        self.game_state = "menu"
        self.last_game_state = None  # 添加状态跟踪变量
        self.running = True
        self.needs_redraw = True
        self.game_paused = False
        self.show_keybinds = False
        self.waiting_for_key = None
        self.is_fullscreen = False  # 添加全屏状态标志
        self.choosing_map_size = False  # 添加地图大小选择状态
        
        # 自动保存相关
        self.last_autosave_time = pygame.time.get_ticks()  # 添加自动保存时间初始化
        self.autosave_interval = 5 * 60 * 1000  # 5分钟，转换为毫秒
        self.save_manager = SaveManager()  # 创建存档管理器
        
        # 地图尺寸定义
        self.map_sizes = {
            "小地图": {"width": 9000, "height": 2400, "grid_size": 0.3},
            "中地图": {"width": 13500, "height": 3600, "grid_size": 0.3},
            "大地图": {"width": 20250, "height": 5400, "grid_size": 0.3}
        }
        self.selected_map_size = "小地图"
        
        # 确保游戏目录存在
        self.player_path, self.world_path = ensure_game_directories()
        
        # 加载角色和地图
        self.characters = []  # 存储已有角色
        self.maps = []  # 存储已有地图
        self.selected_character = None
        self.selected_map = None
        self.player = None
        self.world = None
        self.inventory = None
        self.camera_x = 0
        self.camera_y = 0
        
        # 设置相关变量
        self.volume = 1.0  # 音量值，范围0-1
        self.settings_close_rect = None  # 关闭按钮的碰撞区域
        self.settings_button = SimpleButton(
            self.screen_width - 150, 
            self.screen_height - 70,
            120,
            50,
            "设置",
            color=(255, 0, 0),
            font_size=32
        )
        
        # 创建主菜单按钮
        button_width = 400
        button_height = 80
        button_spacing = 40
        start_y = 300
        
        self.menu_buttons = [
            SimpleButton(
                self.screen_width//2 - button_width//2,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height,
                text,
                font_size=48
            ) for i, text in enumerate(["开始游戏", "按键设置", "退出游戏"])
        ]
        
        # 初始化选择界面的按钮
        self.character_buttons = []
        self.character_delete_buttons = []
        self.map_size_buttons = []
        self.map_delete_buttons = []
        self.new_character_button = None
        self.back_button = None
        
        # 更新选择界面的按钮
        self.update_selection_buttons()
        
        # 加载已有的角色和地图
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
        """运行游戏主循环"""
        while self.running:
            # 处理事件
            if self.game_state == "menu":
                self.handle_menu_events()
            elif self.game_state == "character_select":
                self.handle_character_select_events()
            elif self.game_state == "character_create":
                self.handle_character_create_events()
            elif self.game_state == "map_select":
                self.handle_map_select_events()
            else:
                self.handle_events()
            
            # 更新游戏状态
            if self.game_state == "playing" and not self.game_paused:
                self.update()
            
            # 渲染
            if self.needs_redraw:
                if self.game_state == "menu":
                    self.draw_menu()
                elif self.game_state == "character_select":
                    self.draw_character_select()
                elif self.game_state == "character_create":
                    self.draw_character_create()
                elif self.game_state == "map_select":
                    self.draw_map_select()
                else:
                    self.draw_game()
            
            # 检查游戏状态是否改变
            if self.game_state != self.last_game_state:
                print(f"当前游戏状态: {self.game_state}")
                self.last_game_state = self.game_state
            
            # 控制帧率
            self.clock.tick(self.fps)
            
            # 显示帧率和游戏状态
            pygame.display.set_caption(f"2D冒险游戏 - FPS: {int(self.clock.get_fps())} - 状态: {self.game_state}")
            
        # 退出前保存游戏
        if self.game_state == "playing":
            self.save_character(self.selected_character)
            self.save_map(self.selected_map)

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

    def handle_menu_events(self):
        """处理主菜单界面的事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            if event.type == pygame.MOUSEMOTION:
                # 检查按钮悬停状态
                needs_redraw = False
                for button in self.menu_buttons:
                    old_hovered = button.is_hovered
                    button.handle_event(event)
                    if old_hovered != button.is_hovered:
                        needs_redraw = True
                if needs_redraw:
                    self.needs_redraw = True
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 处理按钮点击
                for i, button in enumerate(self.menu_buttons):
                    if button.handle_event(event):
                        if i == 0:  # 开始游戏
                            print("点击了开始游戏按钮")
                            self.game_state = "character_select"
                            self.needs_redraw = True
                        elif i == 1:  # 按键设置
                            print("点击了按键设置按钮")
                            self.show_keybinds = True
                            self.needs_redraw = True
                        elif i == 2:  # 退出游戏
                            print("点击了退出游戏按钮")
                            self.running = False
                        return

    def draw_menu(self):
        """绘制主菜单界面"""
        # 清空缓冲区
        self.buffer.fill(SKY_BLUE)
        
        # 绘制标题
        title_font = get_font(74)
        title_text = title_font.render("2D冒险游戏", True, BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width//2, 150))
        self.buffer.blit(title_text, title_rect)
        
        # 绘制按钮
        for button in self.menu_buttons:
            button.draw(self.buffer)
            
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def draw_character_select(self):
        """绘制角色选择界面"""
        # 填充背景
        self.buffer.fill(SKY_BLUE)
        
        # 绘制标题
        title = get_font(64).render("选择角色", True, BLACK)
        title_rect = title.get_rect(center=(self.screen_width//2, 100))
        self.buffer.blit(title, title_rect)
        
        # 绘制新建角色按钮
        self.new_character_button.draw(self.buffer)
        
        # 绘制现有角色按钮和删除按钮
        for i, (char_button, del_button) in enumerate(zip(self.character_buttons, self.character_delete_buttons)):
            # 绘制角色按钮
            char_button.draw(self.buffer)
            # 绘制删除按钮
            del_button.draw(self.buffer)
        
        # 绘制返回按钮
        self.back_button.draw(self.buffer)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def handle_character_select_events(self):
        """处理角色选择界面的事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # 处理鼠标移动
            if event.type == pygame.MOUSEMOTION:
                needs_redraw = False
                if self.back_button.handle_event(event):
                    needs_redraw = True
                if self.new_character_button.handle_event(event):
                    needs_redraw = True
                for button in self.character_buttons:
                    if button.handle_event(event):
                        needs_redraw = True
                for button in self.character_delete_buttons:
                    if button.handle_event(event):
                        needs_redraw = True
                if needs_redraw:
                    self.needs_redraw = True
                    
            # 处理鼠标点击
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 返回按钮
                if self.back_button.handle_event(event):
                    self.game_state = "menu"
                    self.needs_redraw = True
                    return
                    
                # 新建角色按钮
                if self.new_character_button.handle_event(event):
                    print("点击了新建角色按钮")
                    self.game_state = "character_create"
                    self.needs_redraw = True
                    return
                    
                # 角色选择按钮
                for button in self.character_buttons:
                    if button.handle_event(event):
                        character_name = button.text  # 使用按钮上的文本作为角色名
                        print(f"选择了角色: {character_name}")
                        self.selected_character = character_name
                        self.game_state = "map_select"
                        self.needs_redraw = True
                        # 更新地图选择界面的按钮
                        self.map_delete_buttons = [
                            SimpleButton(
                                self.screen_width//2 + 150,
                                350 + i*60,
                                60,
                                40,
                                "×",
                                color=(200, 0, 0),
                                font_size=32
                            ) for i in range(len(self.maps))
                        ]
                        return
                        
                # 角色删除按钮
                for i, button in enumerate(self.character_delete_buttons):
                    if button.handle_event(event):
                        character_name = self.character_buttons[i].text  # 使用对应角色按钮的文本
                        print(f"删除角色: {character_name}")
                        self.delete_character(character_name)
                        self.needs_redraw = True
                        return

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

    def delete_character(self, character_name):
        """删除角色"""
        file_path = os.path.join(self.player_path, f"{character_name}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                if character_name in self.characters:
                    self.characters.remove(character_name)
                print(f"成功删除角色: {character_name}")
            except Exception as e:
                print(f"删除角色文件时出错: {e}")
            finally:
                self.update_selection_buttons()

    def delete_map(self, map_name):
        """删除地图"""
        file_path = os.path.join(self.world_path, f"{map_name}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                if map_name in self.maps:
                    self.maps.remove(map_name)
                print(f"成功删除地图: {map_name}")
            except Exception as e:
                print(f"删除地图文件时出错: {e}")
            finally:
                # 更新地图删除按钮
                self.map_delete_buttons = [
                    SimpleButton(
                        self.screen_width//2 + 150,
                        350 + i*60,
                        60,
                        40,
                        "×",
                        color=(200, 0, 0),
                        font_size=32
                    ) for i in range(len(self.maps))
                ]

    def create_new_map(self, width, height, grid_size, map_name):
        """创建新地图"""
        # 确保地图名称唯一
        base_name = map_name
        counter = 1
        while map_name in self.maps:
            map_name = f"{base_name}_{counter}"
            counter += 1
        
        # 创建新的世界实例
        new_world = World(width, height, TILE_SIZE)
        
        # 保存地图数据
        map_data = {
            'name': map_name,
            'grid': new_world.grid.tolist(),  # numpy数组转列表
            'width': width,
            'height': height,
            'grid_size': grid_size
        }
        
        # 保存到文件
        file_path = os.path.join(self.world_path, f"{map_name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        
        print(f"成功创建新地图: {map_name}")
        return map_name

    def initialize_game(self):
        """初始化游戏，包括世界、玩家和其他游戏组件"""
        print("正在初始化游戏...")
        
        # 加载地图数据
        map_file = os.path.join(self.world_path, f"{self.selected_map}.json")
        if os.path.exists(map_file):
            with open(map_file, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
                self.world = World(map_data['width'], map_data['height'], TILE_SIZE)
                self.world.grid = np.array(map_data['grid'])
        else:
            print(f"找不到地图文件: {map_file}")
            return
        
        # 获取世界尺寸
        world_width, world_height = self.world.get_world_size()
        print(f"世界大小: {world_width}x{world_height}")
        
        # 计算地图中央的地面位置
        center_x = world_width // 2
        center_grid_x = center_x // TILE_SIZE
        spawn_y = 0
        
        # 从上往下找到第一个地面方块
        for y in range(len(self.world.grid)):
            if self.world.grid[y][center_grid_x] != self.world.EMPTY:
                spawn_y = y * TILE_SIZE - TILE_SIZE  # 将玩家放在地面方块上方
                break
        
        print(f"玩家出生点: ({center_x}, {spawn_y})")
        
        # 加载角色数据
        character_data = None
        if self.selected_character:
            file_path = os.path.join(self.player_path, f"{self.selected_character}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    character_data = json.load(f)
                print(f"已加载角色数据: {self.selected_character}")
        
        # 初始化玩家在地图中央的地面上
        self.player = Player(center_x - TILE_SIZE // 2, spawn_y, character_data)
        
        # 初始化摄像机位置（以玩家为中心）
        self.camera_x = center_x - self.screen_width // 2
        self.camera_y = max(0, spawn_y - self.screen_height // 2)
        
        # 创建背包
        self.inventory = Inventory(10, 10)  # 位于左上角
        if character_data and 'inventory' in character_data:
            for i, item_data in enumerate(character_data['inventory']):
                if item_data:
                    self.inventory.slots[i].item = item_data['item']
        
        # 切换到游戏状态
        self.game_state = "playing"
        self.game_paused = False
        self.show_keybinds = False  # 确保按键绑定界面是关闭的
        self.inventory.visible = False  # 确保背包是关闭的
        self.needs_redraw = True
        
        print("游戏初始化完成")

    def update(self):
        """更新游戏状态"""
        # 只在游戏状态为 playing 且未暂停时更新
        if self.game_state == "playing" and not self.game_paused and not self.show_keybinds:
            # 更新玩家
            keys = pygame.key.get_pressed()
            dx = 0
            if keys[self.key_bindings['left']]:  # A键
                dx = -1
            if keys[self.key_bindings['right']]:  # D键
                dx = 1
                
            # 如果有移动输入，执行移动
            if dx != 0:
                self.player.move(dx, 0, self.world)
                
            # 跳跃
            if keys[self.key_bindings['jump']]:  # 空格键
                self.player.jump()
                
            # 应用重力和碰撞检测
            self.player.apply_gravity(self.world)
            
            # 更新摄像机位置（以玩家为中心）
            player_x, player_y = self.player.get_position()
            self.camera_x = player_x - self.screen_width // 2
            self.camera_y = player_y - self.screen_height // 2
            
            # 确保摄像机不会超出世界边界
            world_width, world_height = self.world.get_world_size()
            self.camera_x = max(0, min(self.camera_x, world_width - self.screen_width))
            self.camera_y = max(0, min(self.camera_y, world_height - self.screen_height))
            
            # 检查是否需要自动保存
            current_time = pygame.time.get_ticks()
            if current_time - self.last_autosave_time >= self.autosave_interval:
                self.auto_save()
                self.last_autosave_time = current_time
            
            # 设置需要重绘
            self.needs_redraw = True

    def auto_save(self):
        """执行自动保存"""
        self.save_manager.save_game({
            "player": self.player,
            "inventory": self.inventory,
            "camera_x": self.camera_x,
            "camera_y": self.camera_y,
            "key_bindings": self.key_bindings
        })
        print("游戏已自动保存")

    def save_character(self, character_name, character_data=None):
        """保存角色数据"""
        if character_data is None:
            character_data = {
                'name': character_name,
                'health': self.player.health,
                'mana': self.player.mana,
                'inventory': [
                    {'item': slot.item} if slot.item else None
                    for slot in self.inventory.slots
                ]
            }
        
        file_path = os.path.join(self.player_path, f"{character_name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, ensure_ascii=False, indent=2)
            
    def save_map(self, map_name):
        """保存地图数据"""
        map_data = {
            'name': map_name,
            'grid': self.world.grid.tolist(),  # numpy数组转列表
            'width': self.world.world_width,
            'height': self.world.world_height
        }
        
        file_path = os.path.join(self.world_path, f"{map_name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)

    def draw_game(self):
        """绘制游戏主界面"""
        # 清空缓冲区
        self.buffer.fill(SKY_BLUE)
        
        # 绘制世界
        self.world.draw(self.buffer, self.camera_x, self.camera_y)
        
        # 绘制玩家
        player_screen_x = self.player.rect.x - self.camera_x
        player_screen_y = self.player.rect.y - self.camera_y
        self.player.rect.x = player_screen_x
        self.player.rect.y = player_screen_y
        self.buffer.blit(self.player.image, self.player.rect)
        self.player.rect.x = self.player.rect.x + self.camera_x
        self.player.rect.y = self.player.rect.y + self.camera_y
        
        # 绘制小地图
        self.draw_minimap()
        
        # 绘制设置按钮（只在背包打开时显示）
        if self.inventory.visible:
            self.settings_button.draw(self.buffer)
        
        # 如果显示按键绑定界面
        if self.show_keybinds:
            self.draw_keybinds()
        
        # 如果游戏暂停，绘制设置菜单
        if self.game_state == "settings":
            self.draw_settings()
            
        # 绘制背包
        if self.inventory.visible:
            self.inventory.draw(self.buffer, get_font(20))  # 传入字体参数
            
        # 绘制物品栏
        self.inventory.draw_hotbar(self.buffer, get_font(20))  # 始终显示物品栏
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

    def draw_minimap(self):
        """绘制小地图"""
        # 计算缩放比例
        scale_x = self.screen_width / BASE_WIDTH
        scale_y = self.screen_height / BASE_HEIGHT
        
        # 小地图尺寸和位置
        base_minimap_width = 200
        base_minimap_height = 150
        base_margin = 10
        base_heart_size = 20
        base_heart_spacing = 2
        base_star_size = 20
        base_star_spacing = 2
        
        # 缩放尺寸
        minimap_width = int(base_minimap_width * scale_x)
        minimap_height = int(base_minimap_height * scale_y)
        margin = int(base_margin * scale_x)
        heart_size = int(base_heart_size * scale_y)
        heart_spacing = int(base_heart_spacing * scale_y)
        star_size = int(base_star_size * scale_y)
        star_spacing = int(base_star_spacing * scale_x)
        
        # 计算小地图位置
        minimap_x = self.screen_width - minimap_width - margin - (star_size + star_spacing + margin)
        minimap_y = margin + (heart_size + heart_spacing) * 2 + margin
        
        # 创建小地图表面
        minimap = pygame.Surface((minimap_width, minimap_height))
        minimap.fill((100, 100, 100))  # 灰色背景
        
        # 获取玩家的网格坐标
        player_grid_x = self.player.rect.centerx // TILE_SIZE
        player_grid_y = self.player.rect.centery // TILE_SIZE
        view_range = 25  # 上下左右各25格，总共50格
        
        # 计算可见区域的起始和结束位置
        start_x = max(0, player_grid_x - view_range)
        end_x = min(len(self.world.grid[0]), player_grid_x + view_range)
        start_y = max(0, player_grid_y - view_range)
        end_y = min(len(self.world.grid), player_grid_y + view_range)
        
        # 计算缩放比例（添加保护以防止除以零）
        visible_width = max(1, (end_x - start_x) * TILE_SIZE)
        visible_height = max(1, (end_y - start_y) * TILE_SIZE)
        minimap_scale_x = minimap_width / visible_width
        minimap_scale_y = minimap_height / visible_height
        
        # 绘制地形
        for y in range(int(start_y), int(end_y)):
            for x in range(int(start_x), int(end_x)):
                if 0 <= y < len(self.world.grid) and 0 <= x < len(self.world.grid[0]):
                    if self.world.grid[y][x] != self.world.EMPTY:
                        # 计算相对于可见区域的位置
                        rel_x = (x - start_x) * TILE_SIZE
                        rel_y = (y - start_y) * TILE_SIZE
                        block_x = int(rel_x * minimap_scale_x)
                        block_y = int(rel_y * minimap_scale_y)
                        block_size = max(1, int(TILE_SIZE * min(minimap_scale_x, minimap_scale_y)))
                        
                        # 使用方块对应的颜色
                        color = self.world.colors[self.world.grid[y][x]]
                        pygame.draw.rect(minimap, color, (block_x, block_y, block_size, block_size))
        
        # 绘制玩家位置（红点）
        player_rel_x = (self.player.rect.centerx // TILE_SIZE - start_x) * TILE_SIZE
        player_rel_y = (self.player.rect.centery // TILE_SIZE - start_y) * TILE_SIZE
        player_minimap_x = int(player_rel_x * minimap_scale_x)
        player_minimap_y = int(player_rel_y * minimap_scale_y)
        pygame.draw.circle(minimap, (255, 0, 0), (player_minimap_x, player_minimap_y), 
                         int(3 * min(scale_x, scale_y)))

    def break_block(self, mouse_pos):
        """破坏方块"""
        # 将屏幕坐标转换为世界坐标
        world_x = mouse_pos[0] + self.camera_x
        world_y = mouse_pos[1] + self.camera_y
        
        # 将世界坐标转换为网格坐标
        grid_x = world_x // TILE_SIZE
        grid_y = world_y // TILE_SIZE
        
        # 检查坐标是否在世界范围内
        if 0 <= grid_y < len(self.world.grid) and 0 <= grid_x < len(self.world.grid[0]):
            # 检查是否在玩家可及范围内（5个方块的距离）
            player_grid_x = self.player.rect.centerx // TILE_SIZE
            player_grid_y = self.player.rect.centery // TILE_SIZE
            distance = ((grid_x - player_grid_x) ** 2 + (grid_y - player_grid_y) ** 2) ** 0.5
            
            if distance <= 5:  # 5个方块的距离
                # 如果该位置有方块，则移除它
                if self.world.grid[grid_y][grid_x] != self.world.EMPTY:
                    # 获取被破坏的方块类型
                    block_type = self.world.grid[grid_y][grid_x]
                    # 移除方块
                    self.world.grid[grid_y][grid_x] = self.world.EMPTY
                    # 将方块添加到背包
                    self.inventory.add_item(block_type)
                    self.needs_redraw = True

    def place_block(self, mouse_pos):
        """放置方块"""
        # 获取当前选中的物品栏
        selected_slot = self.inventory.slots[self.inventory.selected_slot]
        if not selected_slot or not selected_slot.item:
            return
            
        # 将屏幕坐标转换为世界坐标
        world_x = mouse_pos[0] + self.camera_x
        world_y = mouse_pos[1] + self.camera_y
        
        # 将世界坐标转换为网格坐标
        grid_x = world_x // TILE_SIZE
        grid_y = world_y // TILE_SIZE
        
        # 检查坐标是否在世界范围内
        if 0 <= grid_y < len(self.world.grid) and 0 <= grid_x < len(self.world.grid[0]):
            # 检查是否在玩家可及范围内（5个方块的距离）
            player_grid_x = self.player.rect.centerx // TILE_SIZE
            player_grid_y = self.player.rect.centery // TILE_SIZE
            distance = ((grid_x - player_grid_x) ** 2 + (grid_y - player_grid_y) ** 2) ** 0.5
            
            if distance <= 5:  # 5个方块的距离
                # 检查目标位置是否为空
                if self.world.grid[grid_y][grid_x] == self.world.EMPTY:
                    # 检查是否不会与玩家碰撞
                    block_rect = pygame.Rect(grid_x * TILE_SIZE, grid_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if not block_rect.colliderect(self.player.rect):
                        # 放置方块
                        self.world.grid[grid_y][grid_x] = selected_slot.item
                        # 从背包中移除一个方块
                        selected_slot.remove_one()
                        self.needs_redraw = True

    def handle_events(self):
        """处理游戏主界面的事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # 处理设置界面的事件
            self.handle_settings_events(event)
                
            # 处理按键事件
            if event.type == pygame.KEYDOWN:
                # ESC 键暂停游戏
                if event.key == self.key_bindings['exit']:
                    self.game_paused = not self.game_paused
                    if self.game_paused:
                        self.game_state = "settings"
                    else:
                        self.game_state = "playing"
                    self.needs_redraw = True
                    return
                    
                # E 键打开/关闭背包
                elif event.key == pygame.K_e:
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
                    self.settings_button.is_clicked = not self.settings_button.is_clicked
                    self.needs_redraw = True
                    return
                
                # 如果设置面板打开，不处理其他点击
                if self.settings_button.is_clicked:
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
                    
            # 处理鼠标移动
            elif event.type == pygame.MOUSEMOTION:
                if self.inventory.visible:
                    # 更新设置按钮的悬停状态
                    if self.settings_button.handle_event(event):
                        self.needs_redraw = True

    def handle_settings_events(self, event):
        """处理设置界面的事件"""
        if not self.settings_button.is_clicked:
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 获取鼠标位置
            mouse_pos = pygame.mouse.get_pos()
            
            # 检查是否点击了关闭按钮
            if self.settings_close_rect and self.settings_close_rect.collidepoint(mouse_pos):
                self.settings_button.is_clicked = False
                return
            
            # 检查是否点击了音量滑块区域
            settings_pos = (self.screen.get_width() - 320, 100)
            slider_rect = pygame.Rect(settings_pos[0] + 20, settings_pos[1] + 105, 260, 20)
            if slider_rect.collidepoint(mouse_pos):
                # 计算新的音量值
                self.volume = (mouse_pos[0] - (settings_pos[0] + 20)) / 260
                self.volume = max(0, min(1, self.volume))
                
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            # 如果正在拖动音量滑块
            mouse_pos = pygame.mouse.get_pos()
            settings_pos = (self.screen.get_width() - 320, 100)
            slider_rect = pygame.Rect(settings_pos[0] + 20, settings_pos[1] + 105, 260, 20)
            if slider_rect.collidepoint(mouse_pos):
                # 更新音量值
                self.volume = (mouse_pos[0] - (settings_pos[0] + 20)) / 260
                self.volume = max(0, min(1, self.volume))

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
                    character_data = {
                        'name': self.character_creator.name,
                        'hairstyle': HAIRSTYLES[self.character_creator.hairstyle_index],
                        'body_type': BODY_TYPES[self.character_creator.body_type_index],
                        'class': CLASSES[self.character_creator.class_index],
                        'skin_color': [int(s.value) for s in self.character_creator.color_sliders]
                    }
                    
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
        # 如果设置按钮被点击，绘制设置面板
        if self.settings_button.is_clicked:
            # 绘制半透明背景
            settings_surface = pygame.Surface((300, 400))
            settings_surface.fill((200, 200, 200))
            settings_surface.set_alpha(230)
            settings_pos = (self.screen.get_width() - 320, 100)
            self.screen.blit(settings_surface, settings_pos)
            
            # 绘制设置标题
            title_font = get_font(36)
            title_text = title_font.render("设置", True, (0, 0, 0))
            title_rect = title_text.get_rect(centerx=settings_pos[0] + 150, y=settings_pos[1] + 20)
            self.screen.blit(title_text, title_rect)
            
            # 绘制音量控制
            font = get_font(28)
            volume_text = font.render(f"音量: {int(self.volume * 100)}%", True, (0, 0, 0))
            self.screen.blit(volume_text, (settings_pos[0] + 20, settings_pos[1] + 80))
            
            # 绘制音量滑块背景
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (settings_pos[0] + 20, settings_pos[1] + 110, 260, 10))
            
            # 绘制音量滑块
            slider_pos = settings_pos[0] + 20 + int(self.volume * 260)
            pygame.draw.circle(self.screen, (50, 50, 50), 
                             (slider_pos, settings_pos[1] + 115), 10)
            
            # 绘制按键设置
            key_settings_y = settings_pos[1] + 150
            key_text = font.render("按键设置", True, (0, 0, 0))
            self.screen.blit(key_text, (settings_pos[0] + 20, key_settings_y))
            
            # 显示当前按键设置
            key_y = key_settings_y + 40
            for action, key in self.key_bindings.items():
                key_name = pygame.key.name(key).upper()
                text = font.render(f"{action}: {key_name}", True, (0, 0, 0))
                self.screen.blit(text, (settings_pos[0] + 20, key_y))
                key_y += 30
            
            # 绘制关闭按钮
            close_text = font.render("×", True, (0, 0, 0))
            close_rect = close_text.get_rect(topright=(settings_pos[0] + 290, settings_pos[1] + 10))
            self.screen.blit(close_text, close_rect)
            
            # 更新关闭按钮的碰撞区域
            self.settings_close_rect = close_rect

if __name__ == "__main__":
    game = Game()
    game.run()