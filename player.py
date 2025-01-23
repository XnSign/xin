import pygame
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, character_data=None):
        super().__init__()
        
        # 设置默认属性 - 2x3方块大小
        self.width = 64  # 2个方块宽
        self.height = 96  # 3个方块高
        
        # 根据体型调整大小
        if character_data and "body_type" in character_data:
            if character_data["body_type"] == "瘦小":
                self.width = 56  # 略小
                self.height = 88
            elif character_data["body_type"] == "魁梧":
                self.width = 72  # 略大
                self.height = 104
        
        # 创建带Alpha通道的surface
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.base_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)  # 用于存储基本状态
        
        # 设置角色颜色
        if character_data and "skin_color" in character_data:
            self.color = tuple(character_data["skin_color"] + [255])  # 添加Alpha值
        else:
            self.color = (255, 200, 150, 255)  # 默认肤色
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # 动画相关
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 16  # 每16ms更新一次动画（约60fps）
        self.state = "idle"  # idle, walk, jump
        self.preview_mode = False  # 是否处于预览模式
        self.last_state = None  # 用于检测状态变化
        self.last_facing = True  # 用于检测朝向变化
        
        # 物理属性
        self.true_x = float(x)
        self.true_y = float(y)
        self.x_vel = 0
        self.y_vel = 0
        self.speed = 8  # 增加移动速度
        self.jump_power = -16  # 增加跳跃力度
        self.gravity = 0.8  # 增加重力
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2  # 允许二段跳
        self.jump_pressed = False  # 跳跃键是否被按下
        self.air_control = 0.7  # 空中移动控制
        
        # 碰撞检测优化
        self.collision_rects = []  # 存储附近的碰撞块
        self.last_collision_check = 0
        self.collision_check_interval = 16  # 每帧都更新碰撞检测
        
        # 游戏属性
        self.health = 100
        self.max_health = 100
        self.mana = 100
        self.max_mana = 100
        
        # 职业相关属性
        if character_data and "class" in character_data:
            if character_data["class"] == "战士":
                self.max_health = 120
                self.health = 120
                self.speed = 7
            elif character_data["class"] == "法师":
                self.max_mana = 150
                self.mana = 150
                self.jump_power = -18
            elif character_data["class"] == "弓箭手":
                self.speed = 9
                self.max_jumps = 3
        
        # 角色外观
        self.hairstyle = character_data.get("hairstyle", "发型1") if character_data else "发型1"
        self.draw_character()
        self.base_image.blit(self.image, (0, 0))  # 保存基本状态
    
    def draw_character(self):
        # 清空surface
        self.image.fill((0, 0, 0, 0))
        
        # 计算肢体位置的偏移量（基于动画帧）
        if self.state == "walk":
            leg_offset = math.sin(self.animation_frame * 0.5) * 4
            arm_offset = -math.sin(self.animation_frame * 0.5) * 4
        elif self.state == "jump":
            leg_offset = 2
            arm_offset = -4
        else:  # idle
            leg_offset = math.sin(self.animation_frame * 0.1) * 2
            arm_offset = math.sin(self.animation_frame * 0.1) * 2
        
        # 如果是预览模式，调整偏移量以呈现45度角效果
        if self.preview_mode:
            leg_offset = 0
            arm_offset = 2
        
        # 绘制腿部
        leg_width = self.width // 4
        leg_height = self.height // 3
        # 左腿
        if self.preview_mode:
            # 45度角时，一条腿在前一条腿在后
            pygame.draw.rect(self.image, self.color, 
                           (self.width//4 - leg_width//2 - 4, 
                            self.height*2//3,
                            leg_width, leg_height))  # 后腿
            pygame.draw.rect(self.image, self.color,
                           (self.width*3//4 - leg_width//2 + 4,
                            self.height*2//3,
                            leg_width, leg_height))  # 前腿
        else:
            pygame.draw.rect(self.image, self.color, 
                           (self.width//4 - leg_width//2, 
                            self.height*2//3 + leg_offset,
                            leg_width, leg_height))
            pygame.draw.rect(self.image, self.color,
                           (self.width*3//4 - leg_width//2,
                            self.height*2//3 - leg_offset,
                            leg_width, leg_height))
        
        # 绘制躯干
        body_width = self.width // 2
        body_height = self.height // 2
        if self.preview_mode:
            # 45度角时躯干稍微倾斜
            body_points = [
                (self.width//2 - body_width//2 - 2, self.height//3),
                (self.width//2 + body_width//2 + 2, self.height//3),
                (self.width//2 + body_width//2 + 2, self.height//3 + body_height),
                (self.width//2 - body_width//2 - 2, self.height//3 + body_height)
            ]
            pygame.draw.polygon(self.image, self.color, body_points)
        else:
            pygame.draw.rect(self.image, self.color,
                           (self.width//2 - body_width//2,
                            self.height//3,
                            body_width, body_height))
        
        # 绘制手臂
        arm_width = self.width // 4
        arm_height = self.height // 2.5
        if self.preview_mode:
            # 45度角时，一只手臂在前一只在后
            pygame.draw.rect(self.image, self.color,
                           (self.width//6 - arm_width//2 - 4,
                            self.height//3 + 2,
                            arm_width, arm_height))  # 后臂
            pygame.draw.rect(self.image, self.color,
                           (self.width*5//6 - arm_width//2 + 4,
                            self.height//3 - 2,
                            arm_width, arm_height))  # 前臂
        else:
            if self.facing_right:
                pygame.draw.rect(self.image, self.color,
                               (self.width//6 - arm_width//2,
                                self.height//3 + arm_offset,
                                arm_width, arm_height))
                pygame.draw.rect(self.image, self.color,
                               (self.width*5//6 - arm_width//2,
                                self.height//3 - arm_offset,
                                arm_width, arm_height))
            else:
                pygame.draw.rect(self.image, self.color,
                               (self.width//6 - arm_width//2,
                                self.height//3 - arm_offset,
                                arm_width, arm_height))
                pygame.draw.rect(self.image, self.color,
                               (self.width*5//6 - arm_width//2,
                                self.height//3 + arm_offset,
                                arm_width, arm_height))
        
        # 绘制头部
        head_size = self.width * 0.7
        if self.preview_mode:
            # 45度角时头部稍微偏移
            head_rect = pygame.Rect(self.width//2 - head_size//2 + 2,
                                  0,
                                  head_size, head_size)
        else:
            head_rect = pygame.Rect(self.width//2 - head_size//2,
                                  0,
                                  head_size, head_size)
        pygame.draw.ellipse(self.image, self.color, head_rect)
        
        # 绘制发型
        hair_color = (50, 50, 50, 255)  # 黑色头发
        if self.hairstyle.startswith("发型"):
            style_num = int(self.hairstyle[2:])
            hair_rect = head_rect.copy()
            if self.preview_mode:
                hair_rect.x += 2  # 45度角时发型也要偏移
            
            if style_num == 1:  # 短发
                pygame.draw.rect(self.image, hair_color, 
                               (hair_rect.x, 0,
                                head_size, head_size//2))
            elif style_num == 2:  # 长发
                pygame.draw.rect(self.image, hair_color,
                               (hair_rect.x, 0,
                                head_size, head_size*0.8))
            elif style_num == 3:  # 马尾
                pygame.draw.rect(self.image, hair_color,
                               (hair_rect.x, 0,
                                head_size, head_size//2))
                pygame.draw.rect(self.image, hair_color,
                               (hair_rect.centerx - 2,
                                head_size//2,
                                4, head_size))
            elif style_num == 4:  # 双马尾
                pygame.draw.rect(self.image, hair_color,
                               (hair_rect.x, 0,
                                head_size, head_size//2))
                if self.preview_mode:
                    # 45度角时双马尾一前一后
                    pygame.draw.rect(self.image, hair_color,
                                   (hair_rect.x - 2,
                                    head_size//2,
                                    4, head_size))  # 后马尾
                    pygame.draw.rect(self.image, hair_color,
                                   (hair_rect.right - 2,
                                    head_size//2,
                                    4, head_size))  # 前马尾
                else:
                    pygame.draw.rect(self.image, hair_color,
                                   (hair_rect.x,
                                    head_size//2,
                                    4, head_size))
                    pygame.draw.rect(self.image, hair_color,
                                   (hair_rect.right - 4,
                                    head_size//2,
                                    4, head_size))
            elif style_num == 5:  # 蓬松短发
                for i in range(4):
                    angle = i * math.pi / 2
                    offset_x = math.cos(angle) * 4
                    offset_y = math.sin(angle) * 4
                    if self.preview_mode:
                        offset_x += 2
                    pygame.draw.circle(self.image, hair_color,
                                    (hair_rect.centerx + offset_x,
                                     head_size//2 + offset_y),
                                     head_size//3)
            elif style_num == 6:  # 莫西干
                pygame.draw.rect(self.image, hair_color,
                               (hair_rect.centerx - head_size//6,
                                0,
                                head_size//3,
                                head_size//2))
            elif style_num == 7:  # 波浪长发
                for i in range(4):
                    y_offset = math.sin(i * 0.5) * 4
                    x_offset = 2 if self.preview_mode else 0
                    pygame.draw.rect(self.image, hair_color,
                                   (hair_rect.x + i*head_size//4 + x_offset,
                                    y_offset,
                                    head_size//4,
                                    head_size))
            elif style_num == 8:  # 爆炸头
                for i in range(8):
                    angle = i * math.pi / 4
                    x_offset = 2 if self.preview_mode else 0
                    end_x = hair_rect.centerx + math.cos(angle) * head_size//2 + x_offset
                    end_y = head_size//2 + math.sin(angle) * head_size//2
                    pygame.draw.line(self.image, hair_color,
                                   (hair_rect.centerx + x_offset, head_size//2),
                                   (end_x, end_y), 3)
            elif style_num == 9:  # 斜刘海
                points = [
                    (hair_rect.x, 0),
                    (hair_rect.right, 0),
                    (hair_rect.right, head_size//2),
                    (hair_rect.x, head_size*0.7)
                ]
                if self.preview_mode:
                    points = [(x + 2, y) for x, y in points]
                pygame.draw.polygon(self.image, hair_color, points)
            elif style_num == 10:  # 中分
                x_offset = 2 if self.preview_mode else 0
                pygame.draw.rect(self.image, hair_color,
                               (hair_rect.x + x_offset,
                                0,
                                head_size//2 - 2,
                                head_size*0.7))
                pygame.draw.rect(self.image, hair_color,
                               (hair_rect.centerx + 2 + x_offset,
                                0,
                                head_size//2 - 2,
                                head_size*0.7))
        
        # 绘制面部特征
        eye_color = (0, 0, 0, 255)
        x_offset = 2 if self.preview_mode else 0
        # 左眼
        pygame.draw.circle(self.image, eye_color,
                         (self.width//2 - head_size//6 + x_offset,
                          head_size//2),
                          2)
        # 右眼
        pygame.draw.circle(self.image, eye_color,
                         (self.width//2 + head_size//6 + x_offset,
                          head_size//2),
                          2)
        
        # 绘制嘴巴
        pygame.draw.line(self.image, (150, 50, 50, 255),
                        (self.width//2 - 4 + x_offset, head_size*0.7),
                        (self.width//2 + 4 + x_offset, head_size*0.7),
                        2)
        
        # 如果面向左边且不是预览模式，翻转图像
        if not self.facing_right and not self.preview_mode:
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
        if keys[key_bindings['jump']]:
            if not self.jump_pressed:  # 只在按键第一次按下时跳跃
                self.jump()
                self.jump_pressed = True
        else:
            self.jump_pressed = False  # 释放跳跃键
            
        # 应用重力和碰撞检测
        self.apply_gravity(world)
        
        # 检查是否需要重生
        if self.rect.top > world.world_height:
            self.reset_position(world)
        
        # 只在状态或朝向改变时重新绘制角色
        if (self.state != self.last_state or 
            self.facing_right != self.last_facing or 
            self.state in ["walk", "jump"]):  # 这些状态需要持续动画
            self.draw_character()
            
        self.last_state = self.state
        self.last_facing = self.facing_right
    
    def move(self, dx, dy, world):
        # 水平移动
        if dx != 0:
            # 在空中时移动速度较慢
            actual_speed = self.speed * (self.air_control if not self.on_ground else 1.0)
            step = actual_speed if dx > 0 else -actual_speed
            
            # 分步移动以防止穿墙
            next_x = self.true_x + step
            # 检查世界边界
            if 0 <= next_x <= world.world_width - self.width:
                # 先尝试移动
                old_x = self.rect.x
                self.true_x = next_x
                self.rect.x = int(self.true_x)
                
                # 检查碰撞
                collision = False
                for block_rect in self.collision_rects:
                    if self.rect.colliderect(block_rect):
                        collision = True
                        if dx > 0:  # 向右移动
                            self.rect.right = block_rect.left
                        else:  # 向左移动
                            self.rect.left = block_rect.right
                        self.true_x = float(self.rect.x)
                        break
                
                # 如果发生碰撞，停止当前方向的移动
                if collision:
                    return False
        
        # 垂直移动
        if dy != 0:
            # 分步移动以防止穿墙
            step = 1 if dy > 0 else -1
            steps = abs(int(dy))
            
            for _ in range(steps):
                next_y = self.true_y + step
                # 检查世界边界
                if 0 <= next_y <= world.world_height - self.height:
                    old_y = self.rect.y
                    self.true_y = next_y
                    self.rect.y = int(self.true_y)
                    
                    # 检查碰撞
                    collision = False
                    for block_rect in self.collision_rects:
                        if self.rect.colliderect(block_rect):
                            collision = True
                            if dy > 0:  # 下落
                                self.rect.bottom = block_rect.top
                                self.true_y = float(self.rect.y)
                                self.y_vel = 0
                                self.on_ground = True
                                self.jump_count = 0
                            else:  # 上升
                                self.rect.top = block_rect.bottom
                                self.true_y = float(self.rect.y)
                                self.y_vel = 0
                            break
                    
                    if collision:
                        break
        return True

    def reset_position(self, world):
        """重置角色位置到世界中央的地面上"""
        # 计算世界中央的x坐标
        center_x = world.world_width // 2
        center_grid_x = center_x // world.tile_size
        
        # 从上往下找到第一个地面方块
        spawn_y = 0
        for y in range(len(world.grid)):
            if world.grid[y][center_grid_x] != world.EMPTY:
                spawn_y = y * world.tile_size - self.height
                break
        
        # 设置新位置
        self.true_x = float(center_x - self.width // 2)
        self.true_y = float(spawn_y)
        self.rect.x = int(self.true_x)
        self.rect.y = int(self.true_y)
        self.y_vel = 0
        self.on_ground = False
        self.jump_count = 0

    def jump(self):
        """执行跳跃"""
        if self.on_ground or self.jump_count < self.max_jumps:
            # 在地面上或者还有剩余跳跃次数时可以跳跃
            self.y_vel = self.jump_power * (1.0 if self.on_ground else 0.8)  # 二段跳跃力稍弱
            self.jump_count += 1
            self.on_ground = False
            self.state = "jump"

    def apply_gravity(self, world):
        """应用重力并更新碰撞检测"""
        # 更新碰撞检测区域
        self.update_collision_rects(world)
        
        # 检查是否在地面上
        if not self.on_ground:
            # 检查下方是否有方块
            test_rect = self.rect.copy()
            test_rect.y += 1
            
            ground_detected = False
            for block_rect in self.collision_rects:
                if test_rect.colliderect(block_rect):
                    self.on_ground = True
                    self.y_vel = 0
                    self.jump_count = 0
                    ground_detected = True
                    # 确保角色正确地站在方块上
                    self.rect.bottom = block_rect.top
                    self.true_y = float(self.rect.y)
                    break
            
            if not ground_detected:
                # 应用重力
                self.y_vel = min(self.y_vel + self.gravity, 15)  # 限制最大下落速度
                # 使用move函数进行实际的移动
                self.move(0, self.y_vel, world)
        else:
            # 即使在地面上也要检查下方是否有方块（防止走下坡时穿模）
            test_rect = self.rect.copy()
            test_rect.y += 1
            ground_below = False
            for block_rect in self.collision_rects:
                if test_rect.collidepoint(block_rect.centerx, block_rect.top):
                    ground_below = True
                    break
            if not ground_below:
                self.on_ground = False

    def update_collision_rects(self, world):
        """更新附近的碰撞块列表"""
        self.collision_rects = []
        # 计算玩家所在的网格位置
        grid_x = int(self.rect.centerx // world.tile_size)
        grid_y = int(self.rect.centery // world.tile_size)
        
        # 扩大检查范围到7x7的网格以适应更大的角色
        check_range = 3
        for y in range(max(0, grid_y - check_range), min(len(world.grid), grid_y + check_range + 1)):
            for x in range(max(0, grid_x - check_range), min(len(world.grid[0]), grid_x + check_range + 1)):
                if world.grid[y][x] != world.EMPTY:
                    self.collision_rects.append(
                        pygame.Rect(x * world.tile_size, 
                                  y * world.tile_size,
                                  world.tile_size, 
                                  world.tile_size)
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