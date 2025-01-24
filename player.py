import pygame
import math

class Player:
    def __init__(self, x, y, data):
        """初始化玩家"""
        self.rect = pygame.Rect(x, y, 48, 64)  # 调整为更合适的大小
        self.name = data.get("name", "Player")
        self.hairstyle = data.get("hairstyle", "默认")
        self.body_type = data.get("body_type", "普通")
        self.class_type = data.get("class", "战士")
        self.skin_color = data.get("skin_color", [255, 220, 177])  # 默认肤色
        self.health = data.get("health", 100)
        self.mana = data.get("mana", 100)
        self.inventory = data.get("inventory", [])
        self.preview_mode = False
        self.facing_right = True  # 朝向标志
        self.image = None
        self.update_appearance()
        
        # 位置和移动
        self.x_speed = 0
        self.y_speed = 0
        self.dx = 0  # 水平速度
        self.dy = 0  # 垂直速度
        self.gravity = 0.8  # 重力加速度
        self.max_fall_speed = 20  # 最大下落速度
        self.move_speed = 5  # 移动速度
        
        # 跳跃相关
        self.is_jumping = False
        self.on_ground = False
        self.jump_pressed = False
        self.jumps_left = 2  # 允许二段跳
        self.jump_power = -15  # 跳跃力度
        
        # 动画相关
        self.animation_timer = pygame.time.get_ticks()
        self.animation_speed = 100  # 每帧动画持续100毫秒
        self.animation_frame = 0
        self.state = "idle"
        self.last_state = "idle"
        self.last_facing = True
    
    def update_appearance(self):
        """更新角色外观"""
        # 创建角色表面
        self.image = pygame.Surface((48, 64), pygame.SRCALPHA)
        
        # 基础颜色
        skin_color = tuple(self.skin_color)
        hair_colors = {
            "金色": (255, 215, 0),
            "褐色": (139, 69, 19),
            "黑色": (30, 30, 30),
            "灰色": (128, 128, 128)
        }
        hair_color = hair_colors.get(self.hairstyle.split('_')[0], (0, 0, 0))
        
        # 身体比例调整
        if self.body_type == "瘦小":
            body_width = 16
            shoulder_width = 20
        elif self.body_type == "魁梧":
            body_width = 24
            shoulder_width = 32
        else:  # 普通体型
            body_width = 20
            shoulder_width = 26
        
        # 绘制身体（稍微倾斜以显示立体感）
        body_points = [
            (24 - body_width//2, 25),  # 左肩
            (24 + body_width//2, 25),  # 右肩
            (24 + body_width//2 - 2, 50),  # 右臀
            (24 - body_width//2 - 2, 50)   # 左臀
        ]
        pygame.draw.polygon(self.image, skin_color, body_points)
        
        # 绘制头部（椭圆形以显示立体感）
        head_rect = pygame.Rect(24 - 10, 8, 20, 24)
        pygame.draw.ellipse(self.image, skin_color, head_rect)
        
        # 绘制面部特征
        # 眼睛
        eye_color = (50, 50, 50)
        pygame.draw.ellipse(self.image, eye_color, (24 - 6, 15, 4, 6))
        pygame.draw.ellipse(self.image, eye_color, (24 + 2, 15, 4, 6))
        # 眉毛
        pygame.draw.line(self.image, hair_color, (24 - 7, 13), (24 - 3, 13), 2)
        pygame.draw.line(self.image, hair_color, (24 + 3, 13), (24 + 7, 13), 2)
        # 嘴巴
        pygame.draw.line(self.image, (200, 100, 100), (24 - 3, 25), (24 + 3, 25), 2)
        
        # 绘制发型
        if self.hairstyle:
            # 根据发型类型绘制不同的发型
            if "短" in self.hairstyle:
                # 短发
                hair_points = [
                    (24 - 12, 8),  # 左上
                    (24 + 12, 8),  # 右上
                    (24 + 14, 20), # 右下
                    (24 - 14, 20)  # 左下
                ]
                pygame.draw.polygon(self.image, hair_color, hair_points)
            elif "长" in self.hairstyle:
                # 长发
                hair_points = [
                    (24 - 12, 8),   # 左上
                    (24 + 12, 8),   # 右上
                    (24 + 16, 35),  # 右下
                    (24 - 16, 35)   # 左下
                ]
                pygame.draw.polygon(self.image, hair_color, hair_points)
                # 添加发丝细节
                for i in range(3):
                    pygame.draw.line(self.image, hair_color,
                                   (24 - 12 + i*8, 20),
                                   (24 - 14 + i*8, 35), 2)
        
        # 绘制四肢
        # 手臂
        arm_color = skin_color
        # 左臂
        pygame.draw.line(self.image, arm_color, (24 - body_width//2, 25),
                        (24 - body_width//2 - 8, 40), 4)
        # 右臂
        pygame.draw.line(self.image, arm_color, (24 + body_width//2, 25),
                        (24 + body_width//2 + 8, 40), 4)
        
        # 腿部
        leg_color = skin_color
        # 左腿
        pygame.draw.line(self.image, leg_color, (24 - body_width//4, 50),
                        (24 - body_width//4 - 4, 62), 4)
        # 右腿
        pygame.draw.line(self.image, leg_color, (24 + body_width//4, 50),
                        (24 + body_width//4 + 4, 62), 4)
        
        # 根据职业添加装备
        if self.class_type == "战士":
            # 添加盔甲轮廓
            armor_color = (150, 150, 150)
            pygame.draw.lines(self.image, armor_color, False, body_points, 2)
            # 添加肩甲
            pygame.draw.circle(self.image, armor_color, (24 - body_width//2, 25), 4)
            pygame.draw.circle(self.image, armor_color, (24 + body_width//2, 25), 4)
        elif self.class_type == "法师":
            # 添加法师长袍
            robe_color = (70, 0, 120)
            robe_points = [
                (24 - body_width//2 - 4, 25),  # 左肩
                (24 + body_width//2 + 4, 25),  # 右肩
                (24 + body_width//2 + 6, 60),  # 右下
                (24 - body_width//2 - 6, 60)   # 左下
            ]
            pygame.draw.polygon(self.image, robe_color, robe_points)
        elif self.class_type == "弓箭手":
            # 添加轻甲和箭袋
            leather_color = (139, 69, 19)
            pygame.draw.lines(self.image, leather_color, False, body_points, 2)
            # 箭袋
            pygame.draw.rect(self.image, leather_color,
                           (24 + body_width//2, 30, 6, 15))
            
        # 如果角色朝左，翻转图像
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
            
    def update(self, world, key_bindings):
        current_time = pygame.time.get_ticks()
        
        # 更新动画帧
        if current_time - self.animation_timer > self.animation_speed:
            self.animation_frame += 1
            self.animation_timer = current_time
        
        # 每帧都更新碰撞检测区域
        self.update_collision_rects(world)
        
        # 获取键盘输入
        keys = pygame.key.get_pressed()
        
        # 水平移动
        dx = 0
        if keys[key_bindings['left']]:
            dx = -1
            self.facing_right = False
            self.state = "walk"
        elif keys[key_bindings['right']]:
            dx = 1
            self.facing_right = True
            self.state = "walk"
        else:
            self.state = "idle"
            
        # 如果在空中，设置跳跃状态
        if not self.on_ground:
            self.state = "jump"
            
        # 如果有移动输入，执行移动
        if dx != 0:
            self.move(dx, 0, world)
            
        # 处理跳跃输入
        if not keys[key_bindings['jump']]:
            self.jump_pressed = False  # 释放跳跃键
        elif not self.jump_pressed and self.jumps_left > 0:  # 只在第一次按下时跳跃
            self.dy = self.jump_power
            self.jumps_left -= 1
            self.on_ground = False
            self.state = "jump"
            self.jump_pressed = True
            
        # 应用重力和碰撞检测
        self.apply_gravity(world)
        
        # 检查是否需要重生
        world_height_pixels = world.height * world.grid_size
        if self.rect.top > world_height_pixels:
            self.reset_position(world)
        
        # 只在状态或朝向改变时重新绘制角色
        if (self.state != self.last_state or 
            self.facing_right != self.last_facing or 
            self.state in ["walk", "jump"]):  # 这些状态需要持续动画
            self.draw_character()
            
        self.last_state = self.state
        self.last_facing = self.facing_right
    
    def move(self, dx, dy, world):
        """移动玩家并处理碰撞"""
        # 水平移动
        if dx != 0:
            dx *= self.move_speed
            self.rect.x += dx
            # 检查水平碰撞
            for rect in self.collision_rects:
                if self.rect.colliderect(rect):
                    if dx > 0:  # 向右移动
                        self.rect.right = rect.left
                    elif dx < 0:  # 向左移动
                        self.rect.left = rect.right
        
        # 垂直移动
        if dy != 0:
            self.rect.y += dy
            # 检查垂直碰撞
            for rect in self.collision_rects:
                if self.rect.colliderect(rect):
                    if dy > 0:  # 下落
                        self.rect.bottom = rect.top
                        self.dy = 0
                        self.on_ground = True
                        self.jumps_left = 2  # 着地时重置跳跃次数
                    elif dy < 0:  # 上升
                        self.rect.top = rect.bottom
                        self.dy = 0
            
            # 如果没有发生碰撞，说明在空中
            if not any(self.rect.colliderect(rect) for rect in self.collision_rects):
                self.on_ground = False
        
        # 重新绘制角色
        self.draw_character()
    
    def reset_position(self, world):
        """重置角色位置到世界中央的地面上"""
        # 计算世界中央的x坐标
        center_x = (world.width * world.grid_size) // 2
        center_grid_x = center_x // world.grid_size
        
        # 从上往下找到第一个地面方块
        spawn_y = 0
        for y in range(world.height):
            if world.grid[y][center_grid_x] != world.EMPTY:
                spawn_y = y * world.grid_size - self.rect.height
                break
        
        # 设置新位置
        self.dx = 0
        self.dy = 0
        self.rect.x = int(center_x - self.rect.width // 2)
        self.rect.y = int(spawn_y)
        self.on_ground = False
        self.jumps_left = 2  # 重置跳跃次数
    
    def apply_gravity(self, world):
        """应用重力并处理垂直移动"""
        # 应用重力
        self.dy += self.gravity
        
        # 限制最大下落速度
        if self.dy > self.max_fall_speed:
            self.dy = self.max_fall_speed
            
        # 应用垂直移动
        self.move(0, self.dy, world)
    
    def update_collision_rects(self, world):
        """更新附近的碰撞块列表"""
        self.collision_rects = []
        # 计算玩家所在的网格位置
        grid_x = int(self.rect.centerx // world.grid_size)
        grid_y = int(self.rect.centery // world.grid_size)
        
        # 扩大检查范围到7x7的网格以适应更大的角色
        check_range = 3
        for y in range(max(0, grid_y - check_range), min(len(world.grid), grid_y + check_range + 1)):
            for x in range(max(0, grid_x - check_range), min(len(world.grid[0]), grid_x + check_range + 1)):
                if world.grid[y][x] != world.EMPTY:
                    self.collision_rects.append(
                        pygame.Rect(x * world.grid_size, 
                                  y * world.grid_size,
                                  world.grid_size, 
                                  world.grid_size)
                    )

    def get_position(self):
        """获取玩家位置"""
        return self.rect.x, self.rect.y
        
    def get_health_hearts(self):
        """返回需要显示的完整心形数量"""
        return self.health // 20
        
    def get_mana_stars(self):
        """返回需要显示的完整星形数量"""
        return self.mana // 20

    def jump(self):
        """处理跳跃"""
        if self.jumps_left > 0:
            # 如果是第二段跳跃，跳跃力减弱
            if not self.on_ground:
                self.dy = self.jump_power * 0.8
            else:
                self.dy = self.jump_power
            self.jumps_left -= 1
            self.on_ground = False
            print(f"跳跃！剩余跳跃次数：{self.jumps_left}")  # 调试输出 

    def draw_character(self):
        """绘制角色"""
        # 清空图像
        self.image.fill((0, 0, 0, 0))
        
        # 获取动画偏移量
        leg_offset = math.sin(self.animation_frame * 0.2) * 4 if self.state == "walk" else 0
        arm_offset = -math.sin(self.animation_frame * 0.2) * 4 if self.state == "walk" else 0
        
        # 绘制腿部
        pygame.draw.rect(self.image, self.skin_color, (8, 48 + leg_offset, 8, 16))  # 左腿
        pygame.draw.rect(self.image, self.skin_color, (32, 48 - leg_offset, 8, 16))  # 右腿
        
        # 绘制身体
        pygame.draw.rect(self.image, self.skin_color, (16, 24, 16, 24))  # 躯干
        
        # 绘制手臂
        pygame.draw.rect(self.image, self.skin_color, (4, 24 + arm_offset, 8, 20))   # 左臂
        pygame.draw.rect(self.image, self.skin_color, (36, 24 - arm_offset, 8, 20))  # 右臂
        
        # 绘制头部
        pygame.draw.circle(self.image, self.skin_color, (24, 12), 12)  # 头
        
        # 如果不是朝右，翻转图像
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
            
        # 保存当前状态
        self.last_state = self.state
        self.last_facing = self.facing_right 

    def draw_shadow(self, surface):
        """绘制角色阴影"""
        shadow_color = (0, 0, 0, 100)
        shadow_surface = pygame.Surface((30, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, shadow_color, shadow_surface.get_rect())
        surface.blit(shadow_surface, (self.rect.centerx - 15, self.rect.bottom - 5)) 