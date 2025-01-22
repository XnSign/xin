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
        
        # 生命值和魔力值
        self.max_health = 100
        self.health = self.max_health
        self.max_mana = 20
        self.mana = self.max_mana
        
        # 用于精确位置控制
        self.true_x = float(x)
        self.true_y = float(y)
        
    def move(self, dx, dy, world):
        # 保存旧位置
        old_x = self.true_x
        old_y = self.true_y
        
        # 尝试移动
        new_x = self.true_x + dx * self.speed
        
        # 更新水平位置并检查碰撞
        self.true_x = new_x
        self.rect.x = int(self.true_x)
        
        # 检查水平碰撞
        if dx < 0:  # 向左移动
            # 检查左边两个点（左上角和左下角）
            if (world.is_solid(self.rect.left, self.rect.top + 5) or 
                world.is_solid(self.rect.left, self.rect.bottom - 5)):
                self.true_x = old_x
                self.rect.x = int(self.true_x)
        elif dx > 0:  # 向右移动
            # 检查右边两个点（右上角和右下角）
            if (world.is_solid(self.rect.right, self.rect.top + 5) or 
                world.is_solid(self.rect.right, self.rect.bottom - 5)):
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
        
        # 检查垂直碰撞
        if self.velocity_y > 0:  # 下落
            # 检查底部两个点（左下角和右下角）
            if (world.is_solid(self.rect.left + 5, self.rect.bottom) or 
                world.is_solid(self.rect.right - 5, self.rect.bottom)):
                # 将玩家放在方块顶部
                self.rect.bottom = (self.rect.bottom // world.tile_size) * world.tile_size
                self.true_y = float(self.rect.y)
                self.velocity_y = 0
                self.is_jumping = False
        elif self.velocity_y < 0:  # 上升
            # 检查顶部两个点（左上角和右上角）
            if (world.is_solid(self.rect.left + 5, self.rect.top) or 
                world.is_solid(self.rect.right - 5, self.rect.top)):
                # 将玩家放在方块底部
                self.rect.top = ((self.rect.top // world.tile_size) + 1) * world.tile_size
                self.true_y = float(self.rect.y)
                self.velocity_y = 0
        
    def update(self, world, key_bindings):
        # 获取键盘输入
        keys = pygame.key.get_pressed()
        
        # 水平移动
        dx = 0
        if keys[key_bindings['left']]:  # A键
            dx = -1
        if keys[key_bindings['right']]:  # D键
            dx = 1
            
        # 如果有移动输入，执行移动
        if dx != 0:
            self.move(dx, 0, world)
            
        # 跳跃
        if keys[key_bindings['jump']]:  # 空格键
            self.jump()
            
        # 应用重力和碰撞检测
        self.apply_gravity(world)
        
    def get_position(self):
        return self.rect.x, self.rect.y 

    def get_health_hearts(self):
        """返回需要显示的完整心形数量"""
        return self.health // 20
        
    def get_mana_stars(self):
        """返回需要显示的完整星形数量"""
        return self.mana // 20 