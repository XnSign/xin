import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((255, 0, 0))  # 临时用红色方块表示玩家
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # 玩家属性
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        self.velocity_y = 0
        self.is_jumping = False
        
        # 用于精确位置控制
        self.true_x = float(x)
        self.true_y = float(y)
        
    def move(self, dx, dy, world):
        # 保存旧位置
        old_x = self.true_x
        
        # 尝试移动
        new_x = self.true_x + dx * self.speed
        
        # 更新位置
        self.true_x = new_x
        self.rect.x = int(self.true_x)
        
        # 检查碰撞
        if dx < 0:  # 向左移动
            if world.is_solid(self.rect.left, self.rect.centery):
                self.true_x = old_x
                self.rect.x = int(self.true_x)
        elif dx > 0:  # 向右移动
            if world.is_solid(self.rect.right, self.rect.centery):
                self.true_x = old_x
                self.rect.x = int(self.true_x)
        
    def jump(self):
        if not self.is_jumping:
            self.velocity_y = self.jump_power
            self.is_jumping = True
            
    def apply_gravity(self, world):
        # 应用重力前的位置
        old_y = self.true_y
        
        # 应用重力
        self.velocity_y += self.gravity
        self.true_y += self.velocity_y
        self.rect.y = int(self.true_y)
        
        # 检查下方碰撞
        if world.is_solid(self.rect.centerx, self.rect.bottom):
            # 将玩家放在方块顶部
            self.rect.bottom = (self.rect.bottom // world.tile_size) * world.tile_size
            self.true_y = float(self.rect.y)
            self.velocity_y = 0
            self.is_jumping = False
        
        # 检查头顶碰撞
        elif world.is_solid(self.rect.centerx, self.rect.top):
            # 将玩家放在方块底部
            self.rect.top = ((self.rect.top // world.tile_size) + 1) * world.tile_size
            self.true_y = float(self.rect.y)
            self.velocity_y = 0
        
    def update(self, world, key_bindings):
        # 获取键盘输入
        keys = pygame.key.get_pressed()
        
        # 水平移动
        dx = 0
        if keys[key_bindings['left']]:
            dx -= 1
        if keys[key_bindings['right']]:
            dx += 1
            
        # 如果有移动输入，执行移动
        if dx != 0:
            self.move(dx, 0, world)
            
        # 跳跃
        if keys[key_bindings['jump']]:
            self.jump()
            
        # 应用重力和碰撞检测
        self.apply_gravity(world)
        
    def get_position(self):
        return self.rect.x, self.rect.y 