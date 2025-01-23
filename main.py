import pygame
import sys
import math
import os
import json
import random
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
    def __init__(self, x, y, width, height, text, font=None, color=(0, 0, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = (255, 0, 0)
        self.is_hovered = False
        self.font = font if font else get_font(36)
        
    def draw(self, screen):
        # 绘制按钮背景
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=15)
        
        # 绘制文本
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            old_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            return old_hovered != self.is_hovered
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self.rect.collidepoint(event.pos)
        return False

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        self.handle_rect = pygame.Rect(
            self.get_handle_x(), y, 10, height
        )
        
    def get_handle_x(self):
        return (self.rect.x + 
                (self.value - self.min_val) / (self.max_val - self.min_val) * 
                (self.rect.width - 10))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = min(max(event.pos[0], self.rect.x), self.rect.right - 10)
            self.value = (self.min_val + 
                         (rel_x - self.rect.x) / self.rect.width * 
                         (self.max_val - self.min_val))
            self.handle_rect.x = rel_x
            return True
        return False
        
    def draw(self, screen):
        # 绘制滑动条背景
        pygame.draw.rect(screen, GRAY, self.rect)
        # 绘制滑块
        pygame.draw.rect(screen, BLUE, self.handle_rect)
        # 绘制标签和数值
        font = get_font(20)
        label_text = font.render(f"{self.label}: {int(self.value)}", True, BLACK)
        screen.blit(label_text, (self.rect.x, self.rect.y - 25))

class CharacterCreator:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.name = ""
        self.name_active = False
        
        # 初始化滑动条
        slider_width = 200
        slider_height = 20
        slider_x = x + 50
        slider_y = y + 250  # 调整位置，为名称输入框留出空间
        spacing = 50
        
        self.color_sliders = [
            Slider(slider_x, slider_y, slider_width, slider_height, 0, 255, 128, "红色"),
            Slider(slider_x, slider_y + spacing, slider_width, slider_height, 0, 255, 128, "绿色"),
            Slider(slider_x, slider_y + spacing * 2, slider_width, slider_height, 0, 255, 128, "蓝色")
        ]
        
        # 选择按钮
        button_width = 30
        button_height = 30
        text_width = 120  # 文字显示区域宽度
        button_spacing = 40
        
        # 发型选择按钮
        self.hairstyle_index = 0
        self.hairstyle_prev = SimpleButton(x + 180, y + 100, button_width, button_height, "<")
        self.hairstyle_next = SimpleButton(x + 180 + text_width + button_width, y + 100, button_width, button_height, ">")
        
        # 体型选择按钮
        self.body_type_index = 1  # 默认普通体型
        self.body_prev = SimpleButton(x + 180, y + 140, button_width, button_height, "<")
        self.body_next = SimpleButton(x + 180 + text_width + button_width, y + 140, button_width, button_height, ">")
        
        # 职业选择按钮
        self.class_index = 0
        self.class_prev = SimpleButton(x + 180, y + 180, button_width, button_height, "<")
        self.class_next = SimpleButton(x + 180 + text_width + button_width, y + 180, button_width, button_height, ">")
        
        # 确认和取消按钮
        self.confirm_button = SimpleButton(x + width//4 - 50, y + height - 60, 100, 40, "确认")
        self.cancel_button = SimpleButton(x + width*3//4 - 50, y + height - 60, 100, 40, "取消")
        
    def handle_event(self, event):
        # 更新所有按钮的悬停状态
        if event.type == pygame.MOUSEMOTION:
            self.hairstyle_prev.handle_event(event)
            self.hairstyle_next.handle_event(event)
            self.body_prev.handle_event(event)
            self.body_next.handle_event(event)
            self.class_prev.handle_event(event)
            self.class_next.handle_event(event)
            self.confirm_button.handle_event(event)
            self.cancel_button.handle_event(event)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 处理名称输入框点击
            name_rect = pygame.Rect(self.rect.x + 120, self.rect.y + 50, 200, 30)
            if name_rect.collidepoint(event.pos):
                self.name_active = True
                return True
            else:
                self.name_active = False
            
            # 处理发型选择
            if self.hairstyle_prev.handle_event(event):
                self.hairstyle_index = (self.hairstyle_index - 1) % len(HAIRSTYLES)
                return True
            if self.hairstyle_next.handle_event(event):
                self.hairstyle_index = (self.hairstyle_index + 1) % len(HAIRSTYLES)
                return True
                
            # 处理体型选择
            if self.body_prev.handle_event(event):
                self.body_type_index = (self.body_type_index - 1) % len(BODY_TYPES)
                return True
            if self.body_next.handle_event(event):
                self.body_type_index = (self.body_type_index + 1) % len(BODY_TYPES)
                return True
                
            # 处理职业选择
            if self.class_prev.handle_event(event):
                self.class_index = (self.class_index - 1) % len(CLASSES)
                return True
            if self.class_next.handle_event(event):
                self.class_index = (self.class_index + 1) % len(CLASSES)
                return True
                
            # 处理确认和取消按钮
            if self.confirm_button.handle_event(event):
                if not self.name:  # 如果名称为空，生成随机名称
                    self.name = f"角色{random.randint(1, 999)}"
                return "confirm"
            if self.cancel_button.handle_event(event):
                return "cancel"
                
        elif event.type == pygame.KEYDOWN:
            if self.name_active:
                if event.key == pygame.K_RETURN:
                    self.name_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                else:
                    # 只接受可打印字符
                    if event.unicode.isprintable() and len(self.name) < 10:
                        self.name += event.unicode
                return True
                    
        # 处理滑动条
        for slider in self.color_sliders:
            if slider.handle_event(event):
                return True
                
        return False
        
    def draw(self, screen):
        # 绘制背景
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        # 绘制标题
        title_font = get_font(36)
        title_text = title_font.render("创建角色", True, BLACK)
        screen.blit(title_text, (self.rect.centerx - title_text.get_width()//2, self.rect.y + 10))
        
        # 绘制名称输入框
        name_font = get_font(24)
        name_text = name_font.render("名称:", True, BLACK)
        screen.blit(name_text, (self.rect.x + 50, self.rect.y + 50))
        
        name_rect = pygame.Rect(self.rect.x + 120, self.rect.y + 50, 200, 30)
        pygame.draw.rect(screen, (240, 240, 240) if self.name_active else WHITE, name_rect)
        pygame.draw.rect(screen, BLACK, name_rect, 2)
        
        name_surface = name_font.render(self.name + ("_" if self.name_active and pygame.time.get_ticks() % 1000 < 500 else ""), True, BLACK)
        screen.blit(name_surface, (name_rect.x + 5, name_rect.y + 2))
        
        # 绘制发型选择
        hairstyle_text = name_font.render(f"发型: {HAIRSTYLES[self.hairstyle_index]}", True, BLACK)
        text_rect = hairstyle_text.get_rect(midright=(self.hairstyle_prev.rect.left - 10, self.hairstyle_prev.rect.centery))
        screen.blit(hairstyle_text, text_rect)
        self.hairstyle_prev.draw(screen)
        self.hairstyle_next.draw(screen)
        
        # 绘制体型选择
        body_text = name_font.render(f"体型: {BODY_TYPES[self.body_type_index]}", True, BLACK)
        text_rect = body_text.get_rect(midright=(self.body_prev.rect.left - 10, self.body_prev.rect.centery))
        screen.blit(body_text, text_rect)
        self.body_prev.draw(screen)
        self.body_next.draw(screen)
        
        # 绘制职业选择
        class_text = name_font.render(f"职业: {CLASSES[self.class_index]}", True, BLACK)
        text_rect = class_text.get_rect(midright=(self.class_prev.rect.left - 10, self.class_prev.rect.centery))
        screen.blit(class_text, text_rect)
        self.class_prev.draw(screen)
        self.class_next.draw(screen)
        
        # 绘制肤色滑动条
        for slider in self.color_sliders:
            slider.draw(screen)
            
        # 绘制角色预览
        preview_rect = pygame.Rect(self.rect.right - 250, self.rect.y + 50, 200, 300)
        
        # 创建一个临时的Player对象来预览角色
        preview_player = Player(
            preview_rect.centerx - 16,  # 角色宽度的一半
            preview_rect.centery - 24,  # 角色高度的一半
            {
                "name": self.name,
                "hairstyle": HAIRSTYLES[self.hairstyle_index],
                "body_type": BODY_TYPES[self.body_type_index],
                "class": CLASSES[self.class_index],
                "skin_color": [int(s.value) for s in self.color_sliders]
            }
        )
        
        # 绘制预览区域背景
        pygame.draw.rect(screen, (200, 200, 200), preview_rect)
        pygame.draw.rect(screen, BLACK, preview_rect, 2)
        
        # 绘制角色预览
        preview_player.preview_mode = True  # 设置预览模式，使角色呈45度角
        preview_player.draw_character()  # 重新绘制角色
        screen.blit(preview_player.image, preview_player.rect)
        
        # 绘制确认和取消按钮
        self.confirm_button.draw(screen)
        self.cancel_button.draw(screen)

    def get_character_data(self):
        """获取角色数据"""
        return {
            "name": self.name if self.name else f"角色{random.randint(1, 999)}",
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
        pygame.init()
        
        # 固定窗口大小
        self.screen_width = 1280
        self.screen_height = 720
        
        # 设置窗口模式
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.DOUBLEBUF | pygame.HWSURFACE
        )
        pygame.display.set_caption("2D冒险游戏")
        
        # 创建缓冲surface
        self.buffer = pygame.Surface((self.screen_width, self.screen_height))
        
        # 初始化时钟和运行状态
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60
        
        # 游戏状态
        self.game_state = "menu"
        self.game_paused = False
        self.show_keybinds = False
        self.waiting_for_key = None
        self.needs_redraw = True
        
        # 初始化按键绑定
        self.key_bindings = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'jump': pygame.K_SPACE,
            'exit': pygame.K_ESCAPE
        }
        
        # 按键名称中文映射
        self.action_names = {
            'left': '向左移动',
            'right': '向右移动',
            'jump': '跳跃',
            'exit': '退出'
        }
        
        # 确保游戏目录存在并获取路径
        self.player_path, self.world_path = ensure_game_directories()
        
        # 创建存档管理器
        self.save_manager = SaveManager()
        
        # 初始化游戏相关变量
        self.characters = []  # 存储已有角色
        self.maps = []  # 存储已有地图
        self.selected_character = None
        self.selected_map = None
        self.player = None
        self.world = None
        self.inventory = None
        self.camera_x = 0
        self.camera_y = 0
        self.last_autosave_time = pygame.time.get_ticks()
        self.autosave_interval = 5 * 60 * 1000  # 5分钟，转换为毫秒
        
        # 加载已有的角色和地图
        self.load_characters_and_maps()
        
        # 创建角色创建器
        self.character_creator = CharacterCreator(
            self.screen_width//2 - 400,
            self.screen_height//2 - 300,
            800,
            600
        )
        
        # 创建菜单按钮
        button_width = 400
        button_height = 80
        button_spacing = 40
        
        # 计算第一个按钮的起始Y坐标，使按钮组整体居中
        total_height = 3 * button_height + 2 * button_spacing
        start_y = self.screen_height // 2 - total_height // 2
        
        self.menu_buttons = [
            SimpleButton(self.screen_width//2 - button_width//2, start_y, 
                  button_width, button_height, "开始游戏", get_font(48)),
            SimpleButton(self.screen_width//2 - button_width//2, start_y + button_height + button_spacing, 
                  button_width, button_height, "按键设置", get_font(48)),
            SimpleButton(self.screen_width//2 - button_width//2, start_y + 2 * (button_height + button_spacing), 
                  button_width, button_height, "退出游戏", get_font(48))
        ]
        
        # 创建设置按钮
        self.settings_button = SimpleButton(
            self.screen_width - 200,
            self.screen_height - 100,
            150,
            60,
            "设置",
            get_font(32)
        )
        
        # 创建设置菜单按钮
        settings_button_width = 300
        settings_button_height = 60
        settings_button_spacing = 30
        settings_start_y = 250
        
        self.settings_buttons = [
            SimpleButton(
                self.screen_width//2 - settings_button_width//2,
                settings_start_y,
                settings_button_width,
                settings_button_height,
                "继续游戏",
                get_font(36)
            ),
            SimpleButton(
                self.screen_width//2 - settings_button_width//2,
                settings_start_y + settings_button_height + settings_button_spacing,
                settings_button_width,
                settings_button_height,
                "按键设置",
                get_font(36)
            ),
            SimpleButton(
                self.screen_width//2 - settings_button_width//2,
                settings_start_y + 2 * (settings_button_height + settings_button_spacing),
                settings_button_width,
                settings_button_height,
                "保存游戏",
                get_font(36)
            ),
            SimpleButton(
                self.screen_width//2 - settings_button_width//2,
                settings_start_y + 3 * (settings_button_height + settings_button_spacing),
                settings_button_width,
                settings_button_height,
                "返回主菜单",
                get_font(36)
            ),
            SimpleButton(
                self.screen_width//2 - settings_button_width//2,
                settings_start_y + 4 * (settings_button_height + settings_button_spacing),
                settings_button_width,
                settings_button_height,
                "退出游戏",
                get_font(36)
            )
        ]
        
        # 初始化选择界面的按钮
        self.update_selection_buttons()
        
        # 渲染相关
        self.last_render_time = pygame.time.get_ticks()
        self.render_interval = 16  # 约60fps

    def draw_menu(self):
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

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEMOTION:
                # 检查按钮悬停状态
                for button in self.menu_buttons:
                    old_hovered = button.is_hovered
                    button.handle_event(event)
                    if old_hovered != button.is_hovered:
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
                            self.game_state = "keybinds"
                            self.show_keybinds = True
                            self.needs_redraw = True
                        elif i == 2:  # 退出游戏
                            print("点击了退出游戏按钮")
                            self.running = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == self.key_bindings['exit'] and (event.mod & pygame.KMOD_ALT):  # Alt+ESC切换全屏
                    # 切换窗口模式
                    if self.is_fullscreen:
                        # 从全屏切换到窗口模式
                        self.screen_width, self.screen_height = self.screen_width, self.screen_height
                        pygame.display.quit()
                        pygame.display.init()
                        self.screen = pygame.display.set_mode(
                            (self.screen_width, self.screen_height),
                            pygame.DOUBLEBUF | pygame.HWSURFACE
                        )
                    else:
                        # 保存当前窗口尺寸
                        self.screen_width, self.screen_height = self.screen_width, self.screen_height
                        # 切换到全屏模式
                        info = pygame.display.Info()
                        self.screen_width = info.current_w
                        self.screen_height = info.current_h
                        pygame.display.quit()
                        pygame.display.init()
                        self.screen = pygame.display.set_mode(
                            (self.screen_width, self.screen_height),
                            pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
                        )
                    
                    # 更新缩放比例和缓冲区
                    self.needs_redraw = True
                    
                elif event.key == pygame.K_ESCAPE:  # ESC键用于界面控制
                    if self.show_keybinds:
                        self.show_keybinds = False
                        self.game_paused = False
                    elif self.game_state == "settings":
                        self.game_state = "playing"
                        self.game_paused = False
                    else:
                        self.inventory.visible = not self.inventory.visible
                        self.game_paused = self.inventory.visible  # 当背包打开时暂停游戏
                elif self.waiting_for_key is not None:
                    # 更新按键绑定
                    self.key_bindings[self.waiting_for_key] = event.key
                    print(f"按键已更新: {self.action_names[self.waiting_for_key]} -> {pygame.key.name(event.key)}")
                    self.waiting_for_key = None
                    # 自动保存按键设置
                    self.save_manager.save_game({
                        "player": self.player,
                        "inventory": self.inventory,
                        "camera_x": self.camera_x,
                        "camera_y": self.camera_y,
                        "key_bindings": self.key_bindings
                    })
            elif event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                # 处理窗口大小调整
                self.screen_width = event.w
                self.screen_height = event.h
                self.screen = pygame.display.set_mode(
                    (self.screen_width, self.screen_height),
                    pygame.DOUBLEBUF | pygame.HWSURFACE
                )
                self.needs_redraw = True
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                # 首先处理按键绑定界面的点击
                if self.show_keybinds:
                    if self.handle_keybind_click(mouse_pos):
                        return
                # 然后处理其他界面的点击
                elif self.inventory.visible:
                    # 检查是否点击了设置按钮
                    if self.settings_button.handle_event(event):
                        print("点击了设置按钮")
                        self.game_state = "settings"
                        self.game_paused = True
                        self.inventory.visible = False
                    else:
                        self.inventory.handle_click(mouse_pos)
                elif self.game_state == "settings":
                    self.handle_settings_click(mouse_pos)

    def handle_keybind_click(self, pos):
        if not self.show_keybinds:
            return False
            
        # 按钮尺寸和位置
        button_width = 300
        button_height = 60
        button_spacing = 30
        start_y = 250
        
        # 检查每个按键绑定按钮
        for i, action in enumerate(['left', 'right', 'jump']):
            button_rect = pygame.Rect(
                self.screen_width//2 - button_width//2,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            
            if button_rect.collidepoint(pos):
                print(f"等待新的按键绑定: {action}")
                self.waiting_for_key = action
                return True
        return False

    def handle_settings_click(self, pos):
        # 转换鼠标位置到基准分辨率
        base_pos = (int(pos[0] / (self.screen_width / BASE_WIDTH)), int(pos[1] / (self.screen_height / BASE_HEIGHT)))
        
        # 直接检查每个按钮的点击
        for i, button in enumerate(self.settings_buttons):
            if button.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos})):
                print(f"点击了设置菜单按钮 {i}")  # 调试信息
                if i == 0:  # 继续游戏
                    self.game_state = "playing"
                    self.game_paused = False
                    self.show_keybinds = False
                elif i == 1:  # 按键设置
                    self.show_keybinds = True
                    self.game_paused = True
                elif i == 2:  # 保存游戏
                    self.save_character(self.selected_character)
                    self.save_map(self.selected_map)
                    print("游戏已保存")
                elif i == 3:  # 返回主菜单
                    self.game_state = "menu"
                    self.game_paused = False
                    self.show_keybinds = False
                elif i == 4:  # 退出游戏
                    self.running = False
                return True
        return False

    def draw_settings(self):
        # 清空缓冲区
        self.buffer.fill(SKY_BLUE)
        
        # 绘制半透明背景
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.buffer.blit(overlay, (0, 0))
        
        # 绘制标题
        title_font = get_font(48)
        title_text = title_font.render("游戏设置", True, WHITE)
        title_rect = title_text.get_rect(center=(self.screen_width//2, 150))
        self.buffer.blit(title_text, title_rect)
        
        # 绘制按钮
        for button in self.settings_buttons:
            button.draw(self.buffer)
            
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()

    def update(self):
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
            self.camera_x = player_x - BASE_WIDTH // 2
            self.camera_y = player_y - BASE_HEIGHT // 2
            
            # 确保摄像机不会超出世界边界
            world_width, world_height = self.world.get_world_size()
            self.camera_x = max(0, min(self.camera_x, world_width - BASE_WIDTH))
            self.camera_y = max(0, min(self.camera_y, world_height - BASE_HEIGHT))
            
            # 检查是否需要自动保存
            current_time = pygame.time.get_ticks()
            if current_time - self.last_autosave_time >= self.autosave_interval:
                self.auto_save()
                self.last_autosave_time = current_time

    def auto_save(self):
        # 执行自动保存
        self.save_manager.save_game({
            "player": self.player,
            "inventory": self.inventory,
            "camera_x": self.camera_x,
            "camera_y": self.camera_y,
            "key_bindings": self.key_bindings
        })
        print("游戏已自动保存")

    def draw_keybinds(self):
        if not self.show_keybinds:
            return
            
        # 绘制半透明背景
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.buffer.blit(overlay, (0, 0))
        
        # 绘制标题
        title_font = get_font(48)
        title_text = title_font.render("按键设置", True, WHITE)
        title_rect = title_text.get_rect(center=(self.screen_width//2, 150))
        self.buffer.blit(title_text, title_rect)
        
        # 按钮尺寸和位置
        button_width = 300
        button_height = 60
        button_spacing = 30
        start_y = 250
        
        # 绘制每个按键绑定按钮
        for i, (action, key) in enumerate(self.key_bindings.items()):
            button_rect = pygame.Rect(
                self.screen_width//2 - button_width//2,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            
            # 绘制按钮背景
            color = RED if self.waiting_for_key == action else GRAY
            pygame.draw.rect(self.buffer, color, button_rect, border_radius=15)
            
            # 绘制按钮文本
            text = f"{self.action_names[action]}: {pygame.key.name(key)}"
            if self.waiting_for_key == action:
                text = "请按任意键..."
            text_surface = get_font(32).render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.buffer.blit(text_surface, text_rect)
        
        # 绘制返回提示
        back_text = get_font(24).render("按ESC返回", True, WHITE)
        back_rect = back_text.get_rect(
            center=(self.screen_width//2, start_y + len(self.key_bindings) * (button_height + button_spacing) + 40)
        )
        self.buffer.blit(back_text, back_rect)

    def draw(self):
        current_time = pygame.time.get_ticks()
        
        # 检查是否需要重新渲染
        if not self.needs_redraw and current_time - self.last_render_time < self.render_interval:
            return
            
        # 清空缓冲区
        self.buffer.fill(SKY_BLUE)
        
        # 根据游戏状态绘制不同界面
        print(f"当前游戏状态: {self.game_state}")
        if self.game_state == "menu":
            self.draw_menu()
            return  # 主菜单有自己的缓冲区处理
        elif self.game_state == "character_select":
            self.draw_character_select()
            return  # 角色选择界面有自己的缓冲区处理
        elif self.game_state == "character_create":
            self.character_creator.draw(self.buffer)
        elif self.game_state == "map_select":
            self.draw_map_select()
            return  # 地图选择界面有自己的缓冲区处理
        elif self.game_state == "save_menu":
            self.draw_save_menu()
        elif self.game_state == "playing" or self.game_state == "keybinds" or self.game_state == "settings":
            self.draw_game()
            
        # 直接将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.last_render_time = current_time
        self.needs_redraw = False

    def draw_game(self):
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

    def draw_minimap(self):
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
        
        # 绘制小地图边框
        border_width = max(1, int(2 * min(scale_x, scale_y)))
        pygame.draw.rect(minimap, (255, 255, 255), (0, 0, minimap_width, minimap_height), border_width)
        
        # 将小地图绘制到屏幕
        self.screen.blit(minimap, (minimap_x, minimap_y))

    def run(self):
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
            self.update()
            
            # 渲染
            self.draw()
            
            # 限制帧率
            self.clock.tick(self.fps)
            
            # 显示当前帧率和游戏状态
            fps = int(self.clock.get_fps())
            pygame.display.set_caption(f"2D冒险游戏 - FPS: {fps} - 状态: {self.game_state}")
            
        # 退出游戏时自动保存
        if self.game_state == "playing":
            self.auto_save()
            
        pygame.quit()
        sys.exit()

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

    def handle_character_select_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            if event.type == pygame.MOUSEMOTION:
                # 鼠标移动时检查是否需要重绘
                self.needs_redraw = True
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # 检查返回按钮
                    back_rect = pygame.Rect(50, self.screen_height - 100, 120, 40)
                    if back_rect.collidepoint(mouse_pos):
                        print("点击了返回按钮")
                        self.game_state = "menu"
                        self.needs_redraw = True
                        return
                    
                    # 检查新建角色按钮
                    new_rect = pygame.Rect(self.screen_width - 170, self.screen_height - 100, 120, 40)
                    if new_rect.collidepoint(mouse_pos):
                        print("点击了新建角色按钮")
                        self.game_state = "character_create"
                        self.needs_redraw = True
                        return
                    
                    # 检查角色选择和删除按钮
                    if self.characters:
                        for i, character_name in enumerate(self.characters):
                            y_pos = 150 + i * 100
                            # 角色选择区域
                            char_rect = pygame.Rect(self.screen_width // 4, y_pos, self.screen_width // 2, 80)
                            if char_rect.collidepoint(mouse_pos):
                                print(f"选择了角色: {character_name}")
                                self.selected_character = character_name
                                self.game_state = "map_select"
                                self.needs_redraw = True
                                return
                                
                            # 删除按钮
                            delete_rect = pygame.Rect(self.screen_width * 3 // 4 + 10, y_pos + 20, 60, 40)
                            if delete_rect.collidepoint(mouse_pos):
                                print(f"删除角色: {character_name}")
                                self.delete_character(character_name)
                                self.needs_redraw = True
                                return

    def handle_character_create_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            result = self.character_creator.handle_event(event)
            if result == "confirm":
                # 获取角色数据并保存
                character_data = self.character_creator.get_character_data()
                self.characters.append(character_data["name"])
                self.save_character(character_data["name"], character_data)
                self.update_selection_buttons()
                self.game_state = "character_select"
                self.needs_redraw = True
            elif result == "cancel":
                self.game_state = "character_select"
                self.needs_redraw = True
            elif result:  # 如果有任何更改
                self.needs_redraw = True

    def handle_map_select_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            if event.type == pygame.MOUSEMOTION:
                # 检查按钮悬停状态
                old_hover_states = []
                
                # 保存所有按钮的当前悬停状态
                old_hover_states.append(self.back_button.is_hovered)
                old_hover_states.append(self.new_map_button.is_hovered)
                for button in self.map_buttons:
                    old_hover_states.append(button.is_hovered)
                for button in self.map_delete_buttons:
                    old_hover_states.append(button.is_hovered)
                
                # 更新按钮状态
                self.back_button.handle_event(event)
                self.new_map_button.handle_event(event)
                for button in self.map_buttons:
                    button.handle_event(event)
                for button in self.map_delete_buttons:
                    button.handle_event(event)
                
                # 检查是否有任何按钮的悬停状态发生变化
                new_hover_states = [self.back_button.is_hovered, self.new_map_button.is_hovered]
                new_hover_states.extend([b.is_hovered for b in self.map_buttons])
                new_hover_states.extend([b.is_hovered for b in self.map_delete_buttons])
                
                if old_hover_states != new_hover_states:
                    self.needs_redraw = True
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 处理返回按钮
                if self.back_button.handle_event(event):
                    self.game_state = "character_select"
                    self.needs_redraw = True
                    return
                    
                # 处理新建地图按钮
                if self.new_map_button.handle_event(event):
                    # 创建新地图
                    new_map = f"地图{len(self.maps) + 1}"
                    self.maps.append(new_map)
                    # 初始化并保存新地图
                    self.world = World(BASE_WIDTH, BASE_HEIGHT, TILE_SIZE)
                    self.save_map(new_map)
                    self.update_selection_buttons()
                    # 如果这是第一个地图，直接选择它并开始游戏
                    if len(self.maps) == 1:
                        self.selected_map = new_map
                        self.initialize_game()
                    self.needs_redraw = True
                    return
                    
                # 处理地图选择按钮
                for i, button in enumerate(self.map_buttons):
                    if button.handle_event(event):
                        self.selected_map = self.maps[i]
                        self.initialize_game()
                        self.needs_redraw = True
                        return
                        
                # 处理地图删除按钮
                for i, button in enumerate(self.map_delete_buttons):
                    if button.handle_event(event):
                        self.delete_map(self.maps[i])
                        self.needs_redraw = True
                        return

    def initialize_game(self):
        # 初始化世界
        self.world = World(BASE_WIDTH, BASE_HEIGHT, TILE_SIZE)
        world_width, world_height = self.world.get_world_size()
        
        # 计算地图中央的地面位置
        center_x = world_width // 2
        center_grid_x = center_x // TILE_SIZE
        spawn_y = 0
        
        # 从上往下找到第一个地面方块
        for y in range(len(self.world.grid)):
            if self.world.grid[y][center_grid_x] != self.world.EMPTY:
                spawn_y = y * TILE_SIZE - TILE_SIZE  # 将玩家放在地面方块上方
                break
        
        # 加载角色数据
        character_data = None
        if self.selected_character:
            file_path = os.path.join(self.player_path, f"{self.selected_character}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    character_data = json.load(f)
        
        # 初始化玩家在地图中央的地面上
        self.player = Player(center_x - TILE_SIZE // 2, spawn_y, character_data)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        
        # 初始化摄像机位置（以玩家为中心）
        self.camera_x = center_x - BASE_WIDTH // 2
        self.camera_y = max(0, spawn_y - BASE_HEIGHT // 2)
        
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

    def draw_character_select(self):
        # 清空缓冲区并填充背景色
        self.buffer.fill(SKY_BLUE)
        
        # 绘制标题
        title_font = get_font(48)  # 使用自定义字体函数
        title_text = title_font.render("选择角色", True, BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 50))
        self.buffer.blit(title_text, title_rect)
        
        # 绘制角色列表
        if not self.characters:
            # 如果没有角色，显示提示信息
            font = get_font(36)  # 使用自定义字体函数
            text = font.render("没有可用的角色", True, BLACK)
            text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.buffer.blit(text, text_rect)
        else:
            # 显示现有角色
            for i, character_name in enumerate(self.characters):
                y_pos = 150 + i * 100
                # 绘制角色信息
                char_rect = pygame.Rect(self.screen_width // 4, y_pos, self.screen_width // 2, 80)
                if char_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.buffer, LIGHT_GRAY, char_rect)
                else:
                    pygame.draw.rect(self.buffer, WHITE, char_rect)
                pygame.draw.rect(self.buffer, BLACK, char_rect, 2)
                
                # 绘制角色名称
                font = get_font(36)  # 使用自定义字体函数
                name_text = font.render(str(character_name), True, BLACK)
                name_rect = name_text.get_rect(center=(self.screen_width // 2, y_pos + 40))
                self.buffer.blit(name_text, name_rect)
                
                # 绘制删除按钮
                delete_rect = pygame.Rect(self.screen_width * 3 // 4 + 10, y_pos + 20, 60, 40)
                if delete_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.buffer, RED, delete_rect)
                else:
                    pygame.draw.rect(self.buffer, LIGHT_RED, delete_rect)
                delete_text = font.render("删除", True, WHITE)
                delete_rect_text = delete_text.get_rect(center=delete_rect.center)
                self.buffer.blit(delete_text, delete_rect_text)
        
        # 绘制返回按钮
        back_rect = pygame.Rect(50, self.screen_height - 100, 120, 40)
        if back_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(self.buffer, DARK_GRAY, back_rect)
        else:
            pygame.draw.rect(self.buffer, GRAY, back_rect)
        back_text = get_font(36).render("返回", True, WHITE)  # 使用自定义字体函数
        back_rect_text = back_text.get_rect(center=back_rect.center)
        self.buffer.blit(back_text, back_rect_text)
        
        # 绘制新建角色按钮
        new_rect = pygame.Rect(self.screen_width - 170, self.screen_height - 100, 120, 40)
        if new_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(self.buffer, DARK_GREEN, new_rect)
        else:
            pygame.draw.rect(self.buffer, GREEN, new_rect)
        new_text = get_font(36).render("新建", True, WHITE)  # 使用自定义字体函数
        new_rect_text = new_text.get_rect(center=new_rect.center)
        self.buffer.blit(new_text, new_rect_text)
        
        # 将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()

    def update_selection_buttons(self):
        # 更新角色选择按钮
        button_width = 400
        button_height = 80
        button_spacing = 40
        start_y = 200
        delete_button_width = 60
        delete_button_spacing = 20
        
        self.character_buttons = []
        self.character_delete_buttons = []
        
        if len(self.characters) == 0:
            # 如果没有角色，只显示新建角色按钮
            self.new_character_button = SimpleButton(
                self.screen_width//2 - button_width//2,
                start_y,
                button_width,
                button_height,
                "新建角色",
                get_font(48)
            )
        else:
            # 有角色时，显示所有角色按钮和删除按钮
            for i, char in enumerate(self.characters):
                # 主按钮
                self.character_buttons.append(
                    SimpleButton(
                        self.screen_width//2 - button_width//2,
                        start_y + i * (button_height + button_spacing),
                        button_width,
                        button_height,
                        char,
                        get_font(48)
                    )
                )
                # 删除按钮
                self.character_delete_buttons.append(
                    SimpleButton(
                        self.screen_width//2 + button_width//2 + delete_button_spacing,
                        start_y + i * (button_height + button_spacing),
                        delete_button_width,
                        button_height,
                        "×",
                        get_font(48),
                        color=(255, 0, 0)
                    )
                )
            
            # 新建角色按钮放在最后
            self.new_character_button = SimpleButton(
                self.screen_width//2 - button_width//2,
                start_y + len(self.characters) * (button_height + button_spacing),
                button_width,
                button_height,
                "新建角色",
                get_font(48)
            )
        
        # 更新地图选择按钮
        self.map_buttons = []
        self.map_delete_buttons = []
        
        if len(self.maps) == 0:
            # 如果没有地图，只显示新建地图按钮
            self.new_map_button = SimpleButton(
                self.screen_width//2 - button_width//2,
                start_y,
                button_width,
                button_height,
                "新建地图",
                get_font(48)
            )
        else:
            # 有地图时，显示所有地图按钮和删除按钮
            for i, map_name in enumerate(self.maps):
                # 主按钮
                self.map_buttons.append(
                    SimpleButton(
                        self.screen_width//2 - button_width//2,
                        start_y + i * (button_height + button_spacing),
                        button_width,
                        button_height,
                        map_name,
                        get_font(48)
                    )
                )
                # 删除按钮
                self.map_delete_buttons.append(
                    SimpleButton(
                        self.screen_width//2 + button_width//2 + delete_button_spacing,
                        start_y + i * (button_height + button_spacing),
                        delete_button_width,
                        button_height,
                        "×",
                        get_font(48),
                        color=(255, 0, 0)
                    )
                )
            
            # 新建地图按钮放在最后
            self.new_map_button = SimpleButton(
                self.screen_width//2 - button_width//2,
                start_y + len(self.maps) * (button_height + button_spacing),
                button_width,
                button_height,
                "新建地图",
                get_font(48)
            )
        
        # 更新返回按钮
        self.back_button = SimpleButton(
            50,
            self.screen_height - 150,
            200,
            80,
            "返回",
            get_font(36)
        )

    def delete_character(self, character_name):
        """删除角色"""
        file_path = os.path.join(self.player_path, f"{character_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            self.characters.remove(character_name)
            self.update_selection_buttons()

    def delete_map(self, map_name):
        """删除地图"""
        file_path = os.path.join(self.world_path, f"{map_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            self.maps.remove(map_name)
            self.update_selection_buttons()

    def draw_character_create(self):
        """绘制角色创建界面"""
        self.screen.fill(SKY_BLUE)
        self.character_creator.draw(self.screen)
        pygame.display.flip()

    def draw_map_select(self):
        # 只在需要时重绘
        if not self.needs_redraw:
            return
            
        # 清空缓冲区
        self.buffer.fill(SKY_BLUE)
        
        # 绘制标题
        title_font = get_font(64)  # 使用固定大小
        title_text = title_font.render("选择地图", True, BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width//2, 80))
        self.buffer.blit(title_text, title_rect)
        
        # 绘制返回按钮
        self.back_button.draw(self.buffer)
        
        # 绘制新建地图按钮
        self.new_map_button.draw(self.buffer)
        
        # 绘制地图选择按钮和删除按钮
        for button in self.map_buttons:
            button.draw(self.buffer)
        for button in self.map_delete_buttons:
            button.draw(self.buffer)
            
        # 直接将缓冲区内容复制到屏幕
        self.screen.blit(self.buffer, (0, 0))
        pygame.display.flip()
        
        self.needs_redraw = False

if __name__ == "__main__":
    game = Game()
    game.run()