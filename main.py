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
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
TILE_SIZE = 32

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

class Button:
    def __init__(self, x, y, width, height, text, font=None, color=BLUE, hover_color=RED):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = font if font else get_font(36)
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
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
        self.hairstyle_prev = Button(x + 180, y + 100, button_width, button_height, "<", get_font(20))
        self.hairstyle_next = Button(x + 180 + text_width + button_width, y + 100, button_width, button_height, ">", get_font(20))
        
        # 体型选择按钮
        self.body_type_index = 1  # 默认普通体型
        self.body_prev = Button(x + 180, y + 140, button_width, button_height, "<", get_font(20))
        self.body_next = Button(x + 180 + text_width + button_width, y + 140, button_width, button_height, ">", get_font(20))
        
        # 职业选择按钮
        self.class_index = 0
        self.class_prev = Button(x + 180, y + 180, button_width, button_height, "<", get_font(20))
        self.class_next = Button(x + 180 + text_width + button_width, y + 180, button_width, button_height, ">", get_font(20))
        
        # 确认和取消按钮
        self.confirm_button = Button(x + width//4 - 50, y + height - 60, 100, 40, "确认", get_font(24))
        self.cancel_button = Button(x + width*3//4 - 50, y + height - 60, 100, 40, "取消", get_font(24))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 处理名称输入框点击
            name_rect = pygame.Rect(self.rect.x + 120, self.rect.y + 50, 200, 30)
            self.name_active = name_rect.collidepoint(event.pos)
            
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
        
        name_surface = name_font.render(self.name + ("_" if self.name_active else ""), True, BLACK)
        screen.blit(name_surface, (name_rect.x + 5, name_rect.y + 2))
        
        # 绘制发型选择
        hairstyle_text = name_font.render(f"发型: {HAIRSTYLES[self.hairstyle_index]}", True, BLACK)
        screen.blit(hairstyle_text, (self.rect.x + 50, self.rect.y + 100))
        self.hairstyle_prev.draw(screen)
        self.hairstyle_next.draw(screen)
        
        # 绘制体型选择
        body_text = name_font.render(f"体型: {BODY_TYPES[self.body_type_index]}", True, BLACK)
        screen.blit(body_text, (self.rect.x + 50, self.rect.y + 140))
        self.body_prev.draw(screen)
        self.body_next.draw(screen)
        
        # 绘制职业选择
        class_text = name_font.render(f"职业: {CLASSES[self.class_index]}", True, BLACK)
        screen.blit(class_text, (self.rect.x + 50, self.rect.y + 180))
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

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("2D冒险游戏")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 确保游戏目录存在并获取路径
        self.player_path, self.world_path = ensure_game_directories()
        
        # 游戏状态
        self.game_state = "menu"  # "menu", "character_select", "character_create", "map_select", "playing", "keybinds", "save_menu", "settings"
        self.game_paused = False
        self.show_keybinds = False
        self.waiting_for_key = None
        
        # 角色和地图相关
        self.characters = []  # 存储已有角色
        self.maps = []  # 存储已有地图
        self.selected_character = None
        self.selected_map = None
        
        # 初始化按键绑定
        self.key_bindings = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'jump': pygame.K_SPACE
        }
        
        # 按键名称中文映射
        self.action_names = {
            'left': '向左移动',
            'right': '向右移动',
            'jump': '跳跃'
        }
        
        # 创建存档管理器
        self.save_manager = SaveManager()
        
        # 创建设置按钮
        self.settings_button = Button(WINDOW_WIDTH - 120, WINDOW_HEIGHT - 60, 
                                    100, 40, "设置", get_font(24))
        
        # 创建设置菜单按钮
        self.settings_buttons = [
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 150, 200, 50, "继续游戏"),
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 75, 200, 50, "按键设置"),
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2, 200, 50, "保存游戏"),
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 75, 200, 50, "返回主菜单"),
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 150, 200, 50, "退出游戏")
        ]
        
        # 创建菜单按钮
        button_width = 200
        button_height = 50
        button_spacing = 20
        start_y = WINDOW_HEIGHT // 2 - (3 * button_height + 2 * button_spacing) // 2
        
        self.menu_buttons = [
            Button(WINDOW_WIDTH//2 - button_width//2, start_y, 
                  button_width, button_height, "开始游戏"),
            Button(WINDOW_WIDTH//2 - button_width//2, start_y + button_height + button_spacing, 
                  button_width, button_height, "按键设置"),
            Button(WINDOW_WIDTH//2 - button_width//2, start_y + 2 * (button_height + button_spacing), 
                  button_width, button_height, "退出游戏")
        ]
        
        # 自动保存相关
        self.last_autosave_time = pygame.time.get_ticks()
        self.autosave_interval = 5 * 60 * 1000  # 5分钟，转换为毫秒
        
        # 加载已有的角色和地图
        self.load_characters_and_maps()
        
        # 初始化选择界面的按钮
        self.update_selection_buttons()
        
        # 创建角色创建器
        self.character_creator = CharacterCreator(
            WINDOW_WIDTH//2 - 400, 
            WINDOW_HEIGHT//2 - 300, 
            800, 
            600
        )

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # 处理按钮事件
            for i, button in enumerate(self.menu_buttons):
                if button.handle_event(event):
                    if i == 0:  # 开始游戏
                        self.game_state = "character_select"  # 进入角色选择界面
                    elif i == 1:  # 按键设置
                        self.game_state = "keybinds"
                        self.show_keybinds = True
                    elif i == 2:  # 退出游戏
                        self.running = False

    def draw_menu(self):
        self.screen.fill(SKY_BLUE)
        
        # 绘制标题
        title_font = get_font(74)
        title_text = title_font.render("2D冒险游戏", True, BLACK)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, 150))
        self.screen.blit(title_text, title_rect)
        
        # 绘制按钮
        for button in self.menu_buttons:
            button.draw(self.screen)
            
        pygame.display.flip()
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.waiting_for_key is not None:
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
                elif event.key == pygame.K_ESCAPE:
                    if self.show_keybinds:
                        self.show_keybinds = False
                        self.game_paused = False
                    elif self.game_state == "settings":
                        self.game_state = "playing"
                        self.game_paused = False
                    else:
                        self.inventory.visible = not self.inventory.visible
                        self.game_paused = self.inventory.visible  # 当背包打开时暂停游戏
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                # 首先处理按键绑定界面的点击
                if self.show_keybinds:
                    if self.handle_keybind_click(mouse_pos):
                        return
                # 然后处理其他界面的点击
                elif self.inventory.visible:
                    # 检查是否点击了设置按钮
                    if self.settings_button.rect.collidepoint(mouse_pos):
                        print("点击了设置按钮")
                        self.game_state = "settings"
                        self.game_paused = True
                        self.inventory.visible = False
                    else:
                        self.inventory.handle_click(mouse_pos)
                elif self.game_state == "settings":
                    self.handle_settings_click(mouse_pos)

    def handle_keybind_click(self, pos):
        # 计算按键绑定面板的中心位置
        panel_center_x = WINDOW_WIDTH // 2
        panel_center_y = WINDOW_HEIGHT // 2
        
        # 按钮尺寸和间距
        button_width = 200
        button_height = 40
        button_spacing = 10
        
        # 计算第一个按钮的顶部位置（标题下方）
        start_y = panel_center_y - 30
        
        # 检查每个按键绑定按钮
        for i, action in enumerate(['left', 'right', 'jump']):
            button_rect = pygame.Rect(
                panel_center_x - button_width//2,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            
            if button_rect.collidepoint(pos):
                print(f"等待新的按键绑定: {action}")  # 调试信息
                self.waiting_for_key = action
                return True
        return False

    def handle_settings_click(self, pos):
        # 直接检查每个按钮的点击
        for i, button in enumerate(self.settings_buttons):
            if button.rect.collidepoint(pos):
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
        # 绘制半透明背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # 绘制标题
        title_font = get_font(48)
        title_text = title_font.render("游戏设置", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 200))
        self.screen.blit(title_text, title_rect)
        
        # 更新按钮位置
        button_width = 200
        button_height = 50
        button_spacing = 20
        start_y = WINDOW_HEIGHT//2 - 100
        
        # 重新创建按钮以更新位置
        self.settings_buttons = [
            Button(WINDOW_WIDTH//2 - button_width//2, start_y, 
                  button_width, button_height, "继续游戏"),
            Button(WINDOW_WIDTH//2 - button_width//2, start_y + button_height + button_spacing, 
                  button_width, button_height, "按键设置"),
            Button(WINDOW_WIDTH//2 - button_width//2, start_y + 2 * (button_height + button_spacing), 
                  button_width, button_height, "保存游戏"),
            Button(WINDOW_WIDTH//2 - button_width//2, start_y + 3 * (button_height + button_spacing), 
                  button_width, button_height, "返回主菜单"),
            Button(WINDOW_WIDTH//2 - button_width//2, start_y + 4 * (button_height + button_spacing), 
                  button_width, button_height, "退出游戏")
        ]
        
        # 绘制按钮
        for button in self.settings_buttons:
            button.draw(self.screen)

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
            self.camera_x = player_x - WINDOW_WIDTH // 2
            self.camera_y = player_y - WINDOW_HEIGHT // 2
            
            # 确保摄像机不会超出世界边界
            world_width, world_height = self.world.get_world_size()
            self.camera_x = max(0, min(self.camera_x, world_width - WINDOW_WIDTH))
            self.camera_y = max(0, min(self.camera_y, world_height - WINDOW_HEIGHT))
            
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
        if self.show_keybinds:
            # 绘制半透明背景
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)
            self.screen.blit(overlay, (0, 0))
            
            # 计算面板尺寸和位置
            panel_width = 300
            panel_height = 250
            panel_x = WINDOW_WIDTH//2 - panel_width//2
            panel_y = WINDOW_HEIGHT//2 - panel_height//2
            
            # 绘制面板背景
            panel = pygame.Surface((panel_width, panel_height))
            panel.fill((200, 200, 200))
            self.screen.blit(panel, (panel_x, panel_y))
            
            # 绘制标题
            font = get_font(32)
            title = font.render("按键设置", True, BLACK)
            title_rect = title.get_rect(centerx=WINDOW_WIDTH//2, top=panel_y + 20)
            self.screen.blit(title, title_rect)
            
            # 按钮尺寸和间距
            button_width = 200
            button_height = 40
            button_spacing = 10
            start_y = panel_y + 70  # 标题下方开始
            
            # 绘制每个按键绑定按钮
            font = get_font(24)
            for i, (action, key) in enumerate(self.key_bindings.items()):
                button_rect = pygame.Rect(
                    WINDOW_WIDTH//2 - button_width//2,
                    start_y + i * (button_height + button_spacing),
                    button_width,
                    button_height
                )
                
                # 绘制按钮背景
                button_color = RED if self.waiting_for_key == action else GRAY
                pygame.draw.rect(self.screen, button_color, button_rect)
                pygame.draw.rect(self.screen, BLACK, button_rect, 2)
                
                # 绘制按钮文本
                action_text = f"{self.action_names[action]}: {pygame.key.name(key)}"
                if self.waiting_for_key == action:
                    action_text = "请按任意键..."
                text = font.render(action_text, True, WHITE)
                text_rect = text.get_rect(center=button_rect.center)
                self.screen.blit(text, text_rect)
            
            # 添加返回提示
            back_text = font.render("按ESC返回", True, BLACK)
            back_rect = back_text.get_rect(centerx=WINDOW_WIDTH//2, bottom=panel_y + panel_height - 20)
            self.screen.blit(back_text, back_rect)

    def draw_minimap(self):
        # 小地图尺寸和位置
        minimap_width = 200
        minimap_height = 150
        margin = 10
        heart_size = 20  # 减小心形大小
        heart_spacing = 2  # 减小间距
        star_size = 20  # 减小星形大小
        star_spacing = 2  # 减小间距
        
        # 计算小地图位置，考虑生命值图标的空间（2行红心）
        minimap_x = WINDOW_WIDTH - minimap_width - margin - (star_size + star_spacing + margin)  # 左移，为星形图标留空间
        minimap_y = margin + (heart_size + heart_spacing) * 2 + margin  # 下移，为两行红心留空间
        
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
        
        # 计算缩放比例
        visible_width = (end_x - start_x) * TILE_SIZE
        visible_height = (end_y - start_y) * TILE_SIZE
        scale_x = minimap_width / visible_width
        scale_y = minimap_height / visible_height
        
        # 绘制地形
        for y in range(int(start_y), int(end_y)):
            for x in range(int(start_x), int(end_x)):
                if self.world.grid[y][x] != self.world.EMPTY:
                    # 计算相对于可见区域的位置
                    rel_x = (x - start_x) * TILE_SIZE
                    rel_y = (y - start_y) * TILE_SIZE
                    block_x = int(rel_x * scale_x)
                    block_y = int(rel_y * scale_y)
                    block_size = max(1, int(TILE_SIZE * scale_x))
                    
                    # 使用方块对应的颜色
                    color = self.world.colors[self.world.grid[y][x]]
                    pygame.draw.rect(minimap, color, (block_x, block_y, block_size, block_size))
        
        # 绘制玩家位置（红点）
        player_rel_x = (self.player.rect.centerx // TILE_SIZE - start_x) * TILE_SIZE
        player_rel_y = (self.player.rect.centery // TILE_SIZE - start_y) * TILE_SIZE
        player_minimap_x = int(player_rel_x * scale_x)
        player_minimap_y = int(player_rel_y * scale_y)
        pygame.draw.circle(minimap, (255, 0, 0), (player_minimap_x, player_minimap_y), 3)
        
        # 绘制小地图边框
        pygame.draw.rect(minimap, (255, 255, 255), (0, 0, minimap_width, minimap_height), 2)
        
        # 将小地图绘制到主屏幕
        self.screen.blit(minimap, (minimap_x, minimap_y))

    def draw_game(self):
        self.screen.fill(SKY_BLUE)
        
        # 绘制世界（考虑摄像机偏移）
        self.world.draw(self.screen, self.camera_x, self.camera_y)
        
        # 绘制玩家（考虑摄像机偏移）
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, 
                           (sprite.rect.x - self.camera_x, 
                            sprite.rect.y - self.camera_y))
        
        # 绘制生命值和魔力值
        self.draw_status_bars()
        
        # 绘制物品栏（始终显示）
        self.inventory.draw_hotbar(self.screen, get_font(16))
        
        # 绘制小地图（始终显示）
        self.draw_minimap()
        
        # 绘制背包和设置按钮（当背包可见时）
        if self.inventory.visible:
            self.inventory.draw(self.screen, get_font(16))
            # 在背包界面的右下角绘制设置按钮
            self.settings_button.draw(self.screen)
            
        # 绘制设置界面
        if self.game_state == "settings" and not self.show_keybinds:
            self.draw_settings()
            
        # 绘制按键绑定面板（最后绘制，保证在最上层）
        if self.show_keybinds:
            self.draw_keybinds()

    def draw_status_bars(self):
        # 计算小地图位置
        minimap_width = 200
        minimap_height = 150
        margin = 10
        heart_size = 20  # 减小心形大小
        heart_spacing = 2  # 减小间距
        star_size = 20  # 减小星形大小
        star_spacing = 2  # 减小间距
        
        # 计算小地图位置
        minimap_x = WINDOW_WIDTH - minimap_width - margin - (star_size + star_spacing + margin)
        minimap_y = margin + (heart_size + heart_spacing) * 2 + margin
        
        # 绘制生命值心形（两行）
        hearts_per_row = 10
        total_hearts = self.player.get_health_hearts()
        
        # 计算心形区域的总宽度，确保与小地图对齐
        hearts_total_width = hearts_per_row * (heart_size + heart_spacing) - heart_spacing
        hearts_start_x = minimap_x
        
        for i in range(min(total_hearts, 20)):  # 最多显示20个心（2行*10列）
            row = i // hearts_per_row
            col = i % hearts_per_row
            heart_x = hearts_start_x + col * (heart_size + heart_spacing)
            heart_y = margin + row * (heart_size + heart_spacing)
            
            # 绘制红色心形
            pygame.draw.polygon(self.screen, (255, 0, 0), [
                (heart_x + heart_size//2, heart_y + heart_size//4),
                (heart_x + heart_size//4, heart_y),
                (heart_x, heart_y + heart_size//4),
                (heart_x + heart_size//2, heart_y + heart_size),
                (heart_x + heart_size, heart_y + heart_size//4),
                (heart_x + heart_size*3//4, heart_y),
            ])
        
        # 绘制魔力值星形（一列）
        star_x = WINDOW_WIDTH - star_size - margin  # 放在屏幕右边
        
        for i in range(self.player.get_mana_stars()):
            star_y = minimap_y + i * (star_size + star_spacing)  # 从小地图顶部开始往下排列
            
            # 绘制蓝色星形
            points = []
            for j in range(5):
                # 外部点
                angle = -90 + j * 72  # 从正上方开始，每72度一个点
                rad = math.radians(angle)
                points.append((
                    star_x + star_size//2 + int(star_size//2 * math.cos(rad)),
                    star_y + star_size//2 + int(star_size//2 * math.sin(rad))
                ))
                # 内部点
                angle += 36
                rad = math.radians(angle)
                points.append((
                    star_x + star_size//2 + int(star_size//4 * math.cos(rad)),
                    star_y + star_size//2 + int(star_size//4 * math.sin(rad))
                ))
            pygame.draw.polygon(self.screen, (0, 100, 255), points)

    def draw(self):
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "character_select":
            self.draw_character_select()
        elif self.game_state == "character_create":
            self.draw_character_create()
        elif self.game_state == "map_select":
            self.draw_map_select()
        elif self.game_state == "save_menu":
            self.draw_save_menu()
        elif self.game_state == "playing" or self.game_state == "keybinds" or self.game_state == "settings":
            self.draw_game()
            
        pygame.display.flip()
        
    def run(self):
        while self.running:
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
                
            self.update()
            self.draw()
            self.clock.tick(60)
            
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
        """从文件加载已有角色和地图"""
        self.characters = []
        self.maps = []
        
        # 加载角色
        if os.path.exists(self.player_path):
            for file in os.listdir(self.player_path):
                if file.endswith('.json'):
                    character_name = file[:-5]  # 移除.json后缀
                    self.characters.append(character_name)
                    
        # 加载地图
        if os.path.exists(self.world_path):
            for file in os.listdir(self.world_path):
                if file.endswith('.json'):
                    map_name = file[:-5]  # 移除.json后缀
                    self.maps.append(map_name)
                    
        self.update_selection_buttons()

    def handle_character_select_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # 处理返回按钮
            if self.back_button.handle_event(event):
                self.game_state = "menu"
                return
                
            # 处理新建角色按钮
            if self.new_character_button.handle_event(event):
                self.game_state = "character_create"
                return
                
            # 处理角色选择按钮
            for i, button in enumerate(self.character_buttons):
                if button.handle_event(event):
                    self.selected_character = self.characters[i]
                    self.game_state = "map_select"
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
            elif result == "cancel":
                self.game_state = "character_select"

    def handle_map_select_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # 处理返回按钮
            if self.back_button.handle_event(event):
                self.game_state = "character_select"
                return
                
            # 处理新建地图按钮
            if self.new_map_button.handle_event(event):
                # 创建新地图
                new_map = f"地图{len(self.maps) + 1}"
                self.maps.append(new_map)
                # 初始化并保存新地图
                self.world = World(WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE)
                self.save_map(new_map)
                self.update_selection_buttons()
                # 如果这是第一个地图，直接选择它并开始游戏
                if len(self.maps) == 1:
                    self.selected_map = new_map
                    self.initialize_game()
                return
                
            # 处理地图选择按钮
            for i, button in enumerate(self.map_buttons):
                if button.handle_event(event):
                    self.selected_map = self.maps[i]
                    self.initialize_game()
                    return

    def initialize_game(self):
        # 初始化世界
        self.world = World(WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE)
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
        self.camera_x = center_x - WINDOW_WIDTH // 2
        self.camera_y = max(0, spawn_y - WINDOW_HEIGHT // 2)
        
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
        self.screen.fill(SKY_BLUE)
        
        # 绘制标题
        title_font = get_font(64)
        title_text = title_font.render("选择角色", True, BLACK)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # 绘制返回按钮
        self.back_button.draw(self.screen)
        
        # 绘制新建角色按钮
        self.new_character_button.draw(self.screen)
        
        # 绘制角色选择按钮
        for button in self.character_buttons:
            button.draw(self.screen)
            
    def draw_map_select(self):
        self.screen.fill(SKY_BLUE)
        
        # 绘制标题
        title_font = get_font(64)
        title_text = title_font.render("选择地图", True, BLACK)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # 绘制返回按钮
        self.back_button.draw(self.screen)
        
        # 绘制新建地图按钮
        self.new_map_button.draw(self.screen)
        
        # 绘制地图选择按钮
        for button in self.map_buttons:
            button.draw(self.screen)

    def update_selection_buttons(self):
        # 更新角色选择按钮
        button_width = 200
        button_height = 50
        button_spacing = 20
        start_y = 150
        
        self.character_buttons = []
        if len(self.characters) == 0:
            # 如果没有角色，只显示新建角色按钮
            self.new_character_button = Button(
                WINDOW_WIDTH//2 - button_width//2,
                start_y,
                button_width,
                button_height,
                "新建角色"
            )
        else:
            # 有角色时，显示所有角色按钮
            for i, char in enumerate(self.characters):
                self.character_buttons.append(
                    Button(WINDOW_WIDTH//2 - button_width//2,
                          start_y + i * (button_height + button_spacing),
                          button_width,
                          button_height,
                          char)
                )
            # 新建角色按钮放在最后一个角色按钮下方
            self.new_character_button = Button(
                WINDOW_WIDTH//2 - button_width//2,
                start_y + len(self.characters) * (button_height + button_spacing),
                button_width,
                button_height,
                "新建角色"
            )
            
        # 更新地图选择按钮
        self.map_buttons = []
        if len(self.maps) == 0:
            # 如果没有地图，只显示新建地图按钮
            self.new_map_button = Button(
                WINDOW_WIDTH//2 - button_width//2,
                start_y,
                button_width,
                button_height,
                "新建地图"
            )
        else:
            # 有地图时，显示所有地图按钮
            for i, map_name in enumerate(self.maps):
                self.map_buttons.append(
                    Button(WINDOW_WIDTH//2 - button_width//2,
                          start_y + i * (button_height + button_spacing),
                          button_width,
                          button_height,
                          map_name)
                )
            # 新建地图按钮放在最后一个地图按钮下方
            self.new_map_button = Button(
                WINDOW_WIDTH//2 - button_width//2,
                start_y + len(self.maps) * (button_height + button_spacing),
                button_width,
                button_height,
                "新建地图"
            )
            
        # 更新返回按钮位置
        self.back_button = Button(
            50,
            WINDOW_HEIGHT - 70,
            100,
            40,
            "返回",
            get_font(24)
        )

    def draw_character_create(self):
        """绘制角色创建界面"""
        self.screen.fill(SKY_BLUE)
        self.character_creator.draw(self.screen)
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()