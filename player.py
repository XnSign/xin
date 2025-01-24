import pygame
import math

class Player:
    def __init__(self, x, y, data):
        """初始化玩家"""
        super().__init__()
        
        # 基本属性
        self.name = data['name']
        self.gender = data.get('gender', '男')  # 默认为男性
        self.hairstyle = data['hairstyle']
        self.body_type = data['body_type']
        self.class_type = data['class']
        self.skin_color = data['skin_color']
        self.health = data['health']
        self.mana = data['mana']
        
        # 位置和移动
        self.rect = pygame.Rect(x, y, 48, 64)  # 玩家碰撞箱
        self.x_speed = 0
        self.y_speed = 0
        self.dx = 0  # 水平速度
        self.dy = 0  # 垂直速度
        self.gravity = 0.8  # 重力加速度
        self.max_fall_speed = 20  # 最大下落速度
        self.move_speed = 5  # 移动速度
        
        # 跳跃相关
        self.facing_right = True
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
        self.preview_mode = False
        
        # 创建玩家图像
        self.image = pygame.Surface((48, 64), pygame.SRCALPHA)
        self.draw_character()
    
    def update_appearance(self):
        """更新角色外观"""
        # 创建一个新的surface作为角色图像
        self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        # 获取surface的中心点
        center_x = 32
        center_y = 32
        
        # 根据性别和体型调整身体比例
        if self.gender == '女':
            if self.body_type == "瘦小":
                body_width = 14
                body_height = 28
                shoulder_width = 16
                waist_ratio = 0.75
            elif self.body_type == "普通":
                body_width = 16
                body_height = 30
                shoulder_width = 18
                waist_ratio = 0.8
            else:  # 魁梧
                body_width = 18
                body_height = 32
                shoulder_width = 20
                waist_ratio = 0.85
        else:  # 男性
            if self.body_type == "瘦小":
                body_width = 16
                body_height = 30
                shoulder_width = 20
                waist_ratio = 0.9
            elif self.body_type == "普通":
                body_width = 18
                body_height = 32
                shoulder_width = 24
                waist_ratio = 0.95
            else:  # 魁梧
                body_width = 22
                body_height = 34
                shoulder_width = 28
                waist_ratio = 1.0
        
        # 计算身体各部分的位置
        body_top = center_y - body_height//2
        body_bottom = center_y + body_height//2
        body_left = center_x - body_width//2
        body_right = center_x + body_width//2
        waist_y = body_top + body_height * 0.4
        
        # 根据性别设置肤色
        if self.gender == '女':
            skin_color = (255, 223, 196)
            skin_shadow = (235, 203, 176)
        else:
            skin_color = (240, 200, 160)
            skin_shadow = (220, 180, 140)
        
        # 绘制腿部
        leg_width = 6 if self.gender == '女' else 8
        leg_spacing = 2
        # 左腿
        pygame.draw.rect(self.image, skin_color,
                        (center_x - leg_width - leg_spacing//2, waist_y,
                         leg_width, body_bottom - waist_y))
        # 右腿
        pygame.draw.rect(self.image, skin_color,
                        (center_x + leg_spacing//2, waist_y,
                         leg_width, body_bottom - waist_y))
        
        # 绘制身体（侧面视角）
        body_points = [
            (body_left, body_top),  # 左上
            (body_right, body_top),  # 右上
            (body_right - body_width//4, body_bottom),  # 右下
            (body_left - body_width//4, body_bottom)   # 左下
        ]
        pygame.draw.polygon(self.image, skin_color, body_points)
        
        # 绘制手臂（侧面视角）
        arm_width = 5 if self.gender == '女' else 7
        # 后臂（稍微向后）
        pygame.draw.line(self.image, skin_color,
                        (body_left, body_top + 4),
                        (body_left - 6, body_top + body_height//3),
                        arm_width)
        # 前臂（稍微向前）
        pygame.draw.line(self.image, skin_color,
                        (body_right, body_top + 4),
                        (body_right + 4, body_top + body_height//3),
                        arm_width)
        
        # 绘制头部（侧面视角）
        head_size = int(body_width * 1.2)
        face_y = body_top - head_size - 2
        
        # 绘制脖子
        neck_width = 6 if self.gender == '女' else 8
        neck_height = 6
        pygame.draw.rect(self.image, skin_color,
                        (center_x - neck_width//2, face_y + head_size,
                         neck_width, neck_height))
        
        # 绘制头部轮廓（侧面）
        head_points = [
            (center_x - head_size//2, face_y + head_size//2),  # 后脑
            (center_x, face_y),  # 头顶
            (center_x + head_size//2, face_y + head_size//4),  # 前额
            (center_x + head_size//2, face_y + head_size//2),  # 鼻子
            (center_x + head_size//3, face_y + head_size),  # 下巴
            (center_x - head_size//3, face_y + head_size)   # 颈部连接点
        ]
        pygame.draw.polygon(self.image, skin_color, head_points)
        
        # 设置发色
        if self.hairstyle.startswith("金色"):
            hair_color = (255, 215, 0)
            hair_shadow = (218, 165, 32)
        elif self.hairstyle.startswith("褐色"):
            hair_color = (139, 69, 19)
            hair_shadow = (101, 67, 33)
        else:  # 黑色
            hair_color = (30, 30, 30)
            hair_shadow = (10, 10, 10)
        
        # 绘制发型（侧面视角）
        if self.hairstyle.endswith("短发"):
            # 短发（侧面）
            hair_points = [
                (center_x - head_size//2 - 2, face_y + head_size//2),  # 后脑
                (center_x - head_size//4, face_y - head_size//4),  # 头顶后部
                (center_x + head_size//4, face_y - head_size//4),  # 头顶前部
                (center_x + head_size//2, face_y + head_size//4),  # 前额
                (center_x + head_size//3, face_y + head_size//2),  # 耳朵位置
            ]
            pygame.draw.polygon(self.image, hair_color, hair_points)
        else:
            # 长发（侧面）
            hair_points = [
                (center_x - head_size//2 - 4, face_y + head_size),  # 后脑底部
                (center_x - head_size//2 - 2, face_y),  # 后脑顶部
                (center_x, face_y - head_size//4),  # 头顶
                (center_x + head_size//2, face_y + head_size//4),  # 前额
                (center_x + head_size//3, face_y + head_size//2),  # 耳朵位置
                (center_x + head_size//4, face_y + head_size + 10),  # 发尾前部
                (center_x - head_size//4, face_y + head_size + 10)   # 发尾后部
            ]
            pygame.draw.polygon(self.image, hair_color, hair_points)
        
        # 绘制眼睛（侧面）
        eye_y = face_y + head_size * 0.4
        pygame.draw.ellipse(self.image, (255, 255, 255),
                          (center_x + head_size//6, eye_y, 4, 3))
        pygame.draw.ellipse(self.image, (60, 60, 60),
                          (center_x + head_size//6 + 1, eye_y + 1, 2, 2))
        
        # 根据职业添加装备
        if self.class_type == "战士":
            # 剑和盾（侧面视角）
            pygame.draw.rect(self.image, (192, 192, 192),
                           (body_right + 4, body_top + body_height//4, 20, 4))  # 剑
            pygame.draw.ellipse(self.image, (139, 69, 19),
                              (body_left - 12, body_top + body_height//4, 10, 15))  # 盾
            
        elif self.class_type == "法师":
            # 法杖（侧面视角）
            pygame.draw.rect(self.image, (139, 69, 19),
                           (body_right + 4, body_top - 10, 4, 30))  # 法杖
            pygame.draw.circle(self.image, (0, 191, 255),
                             (body_right + 6, body_top - 10), 4)  # 法杖顶端
            
        elif self.class_type == "弓箭手":
            # 弓（侧面视角）
            pygame.draw.arc(self.image, (139, 69, 19),
                          (body_right + 4, body_top, 10, 30),
                          -0.5, 0.5, 2)  # 弓
            
        # 如果不是朝右，翻转图像
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