import pygame
import sys
import math
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

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("2D冒险游戏")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 自动保存相关
        self.last_autosave_time = pygame.time.get_ticks()
        self.autosave_interval = 5 * 60 * 1000  # 5分钟，转换为毫秒
        
        # 游戏状态
        self.game_state = "menu"  # "menu", "playing", "keybinds", "save_menu", "settings"
        self.game_paused = False
        self.show_keybinds = False
        
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
        
        # 等待按键绑定的状态
        self.waiting_for_key = None
        
        # 创建存档管理器
        self.save_manager = SaveManager()
        
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
        
        # 初始化玩家在地图中央的地面上
        self.player = Player(center_x - TILE_SIZE // 2, spawn_y)  # 调整水平位置以确保居中
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        
        # 初始化摄像机位置（以玩家为中心）
        self.camera_x = center_x - WINDOW_WIDTH // 2
        self.camera_y = max(0, spawn_y - WINDOW_HEIGHT // 2)
        
        # 创建背包
        self.inventory = Inventory(10, 10)  # 位于左上角
        
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
        
        # 创建设置按钮
        self.settings_button = Button(WINDOW_WIDTH - 120, WINDOW_HEIGHT - 60, 
                                    100, 40, "设置", get_font(24))
        
        # 创建设置菜单按钮
        self.settings_buttons = [
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 120, 200, 50, "继续游戏"),
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 40, 200, 50, "按键设置"),
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 40, 200, 50, "返回主菜单"),
            Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 120, 200, 50, "退出游戏")
        ]
        
    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # 处理按钮事件
            for i, button in enumerate(self.menu_buttons):
                if button.handle_event(event):
                    if i == 0:  # 开始游戏
                        self.game_state = "playing"
                        self.game_paused = False  # 确保游戏开始时不是暂停状态
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
                elif i == 2:  # 返回主菜单
                    self.game_state = "menu"
                    self.game_paused = False
                    self.show_keybinds = False
                elif i == 3:  # 退出游戏
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
                  button_width, button_height, "返回主菜单"),
            Button(WINDOW_WIDTH//2 - button_width//2, start_y + 3 * (button_height + button_spacing), 
                  button_width, button_height, "退出游戏")
        ]
        
        # 绘制按钮
        for button in self.settings_buttons:
            button.draw(self.screen)

    def update(self):
        # 只在游戏状态为 playing 且未暂停时更新
        if self.game_state == "playing" and not self.game_paused and not self.show_keybinds:
            # 更新玩家
            self.player.update(self.world, self.key_bindings)
            
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
        elif self.game_state == "save_menu":
            self.draw_save_menu()
        elif self.game_state == "playing" or self.game_state == "keybinds" or self.game_state == "settings":
            self.draw_game()
            
        pygame.display.flip()
        
    def run(self):
        while self.running:
            if self.game_state == "menu":
                self.handle_menu_events()
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

    def load_characters_and_maps(self):
        # TODO: 从文件加载已有角色和地图
        # 如果没有检测到角色和地图，列表将为空
        self.characters = []
        self.maps = []
        self.update_selection_buttons()

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
                # 创建新角色
                new_char = f"角色{len(self.characters) + 1}"
                self.characters.append(new_char)
                self.update_selection_buttons()
                # 如果这是第一个角色，直接选择它并进入地图选择
                if len(self.characters) == 1:
                    self.selected_character = new_char
                    self.game_state = "map_select"
                return
                
            # 处理角色选择按钮
            for i, button in enumerate(self.character_buttons):
                if button.handle_event(event):
                    self.selected_character = self.characters[i]
                    self.game_state = "map_select"
                    return
                    
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

if __name__ == "__main__":
    game = Game()
    game.run()