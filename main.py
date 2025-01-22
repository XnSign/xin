import pygame
import sys
from player import Player
from world import World
from inventory import Inventory

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
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=RED):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = get_font(36)
        
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
        self.game_state = "menu"  # "menu", "playing", "keybinds"
        
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
        
        # 按键绑定
        self.key_bindings = {
            'left': pygame.K_a,  # 改为A键
            'right': pygame.K_d,  # 改为D键
            'jump': pygame.K_SPACE
        }
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
            "K键：显示/隐藏按键设置",
            "ESC键：打开/关闭背包",
            "1-0键：选择物品栏"
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
                if event.key == pygame.K_k and not self.show_keybinds:
                    self.show_keybinds = True
                    self.inventory.visible = False
                elif event.key == pygame.K_ESCAPE:
                    if self.show_keybinds:
                        self.show_keybinds = False
                    else:
                        self.inventory.visible = not self.inventory.visible
                elif self.waiting_for_key:
                    self.key_bindings[self.waiting_for_key] = event.key
                    self.waiting_for_key = None
                else:
                    # 处理物品栏快捷键
                    self.inventory.handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.show_keybinds:
                    self.handle_keybind_click(event.pos)
                elif self.inventory.visible:
                    self.inventory.handle_click(event.pos)
                
    def handle_keybind_click(self, pos):
        x, y = pos
        if 10 <= x <= 210:
            button_height = 40
            button_spacing = 10
            
            for i, action in enumerate(['left', 'right', 'jump']):
                button_y = 10 + i * (button_height + button_spacing)
                if button_y <= y <= button_y + button_height:
                    self.waiting_for_key = action
                    break
                
    def update(self):
        if self.game_state == "playing":
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
            # 绘制按键绑定面板背景
            panel = pygame.Surface((220, 150))
            panel.fill((200, 200, 200))
            panel.set_alpha(200)
            self.screen.blit(panel, (10, 10))
            
            font = get_font(24)
            button_height = 40
            button_spacing = 10
            
            # 绘制每个按键绑定按钮
            for i, (action, key) in enumerate(self.key_bindings.items()):
                y = 10 + i * (button_height + button_spacing)
                
                # 绘制按钮背景
                button_color = RED if self.waiting_for_key == action else GRAY
                pygame.draw.rect(self.screen, button_color, (10, y, 200, button_height))
                
                # 绘制按钮文本
                action_text = f"{self.action_names[action]}: {pygame.key.name(key)}"
                if self.waiting_for_key == action:
                    action_text = "请按任意键..."
                text = font.render(action_text, True, WHITE)
                text_rect = text.get_rect(center=(110, y + button_height // 2))
                self.screen.blit(text, text_rect)
            
            # 添加返回按钮
            back_text = font.render("按ESC返回", True, BLACK)
            back_rect = back_text.get_rect(center=(110, 130))
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
        
        # 绘制背包（当可见时）
        if self.inventory.visible:
            self.inventory.draw(self.screen, get_font(16))
            
        # 绘制按键绑定面板
        if self.show_keybinds:
            self.draw_keybinds()
            
    def draw(self):
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "playing" or self.game_state == "keybinds":
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