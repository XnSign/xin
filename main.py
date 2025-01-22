import pygame
import sys
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
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("2D冒险游戏")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 游戏状态
        self.game_state = "menu"  # "menu", "playing", "keybinds", "save_menu", "settings"
        self.game_paused = False
        
        # 创建存档管理器
        self.save_manager = SaveManager()
        
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
        
        # 游戏相关初始化
        self.init_game()
        
    def init_game(self):
        # 创建世界
        self.world = World(WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE)
        self.world_width, self.world_height = self.world.get_world_size()
        
        # 创建玩家（初始位置在地面上）
        initial_x = WINDOW_WIDTH // 2
        initial_y = 0
        for y in range(WINDOW_HEIGHT):
            if self.world.is_solid(initial_x, y):
                initial_y = y - TILE_SIZE
                break
        self.player = Player(initial_x, initial_y)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        
        # 摄像机位置
        self.camera_x = 0
        self.camera_y = 0
        
        # 游戏设置
        self.show_keybinds = False
        self.player_speed = 5
        self.jump_power = 15
        self.gravity = 0.8
        
        # 创建背包
        self.inventory = Inventory(10, 10)  # 位于左上角
        
        # 默认按键绑定
        self.key_bindings = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'jump': pygame.K_SPACE
        }
        
        # 尝试加载已保存的按键设置
        save_slots = self.save_manager.get_save_slots()
        if save_slots:
            # 加载最新的存档中的按键设置
            latest_save = save_slots[0]["name"]
            self.save_manager.load_game(latest_save, {
                "player": self.player,
                "inventory": self.inventory,
                "camera_x": self.camera_x,
                "camera_y": self.camera_y,
                "key_bindings": self.key_bindings
            })
        
        # 按键名称中文映射
        self.action_names = {
            'left': '向左移动',
            'right': '向右移动',
            'jump': '跳跃'
        }
        self.waiting_for_key = None
        
    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # 处理按钮事件
            for i, button in enumerate(self.menu_buttons):
                if button.handle_event(event):
                    if i == 0:  # 开始游戏
                        self.game_state = "playing"
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
            
        # 绘制操作提示
        hint_font = get_font(24)
        hints = [
            "游戏操作说明：",
            "ESC键：打开/关闭背包",
            "1-0键：选择物品栏",
            "F5键：快速保存"
        ]
        for i, hint in enumerate(hints):
            hint_text = hint_font.render(hint, True, BLACK)
            self.screen.blit(hint_text, (20, WINDOW_HEIGHT - 120 + i * 20))
            
        pygame.display.flip()
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.show_keybinds:
                        self.show_keybinds = False
                        self.game_paused = False
                    elif self.game_state == "settings":
                        self.game_state = "playing"
                        self.game_paused = False
                    else:
                        # 切换背包和设置按钮的显示状态
                        self.inventory.visible = not self.inventory.visible
                elif event.key == pygame.K_F5:
                    # 快速保存
                    self.save_manager.save_game({
                        "player": self.player,
                        "inventory": self.inventory,
                        "camera_x": self.camera_x,
                        "camera_y": self.camera_y,
                        "key_bindings": self.key_bindings
                    })
                elif self.waiting_for_key is not None:
                    # 更新按键绑定
                    old_key = self.key_bindings[self.waiting_for_key]
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
                else:
                    # 处理物品栏快捷键
                    self.inventory.handle_key(event)
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
        if self.game_state == "playing" and not self.game_paused:
            # 更新玩家
            self.player.update(self.world, self.key_bindings)
            
            # 更新摄像机位置（以玩家为中心）
            player_x, player_y = self.player.get_position()
            self.camera_x = player_x - WINDOW_WIDTH // 2
            self.camera_y = player_y - WINDOW_HEIGHT // 2
            
            # 确保摄像机不会超出世界边界
            self.camera_x = max(0, min(self.camera_x, self.world_width - WINDOW_WIDTH))
            self.camera_y = max(0, min(self.camera_y, self.world_height - WINDOW_HEIGHT))
            
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

    def draw_game(self):
        self.screen.fill(SKY_BLUE)
        
        # 绘制世界（考虑摄像机偏移）
        self.world.draw(self.screen, self.camera_x, self.camera_y)
        
        # 绘制玩家（考虑摄像机偏移）
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, 
                           (sprite.rect.x - self.camera_x, 
                            sprite.rect.y - self.camera_y))
        
        # 绘制物品栏（始终显示）
        self.inventory.draw_hotbar(self.screen, get_font(16))
        
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
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()