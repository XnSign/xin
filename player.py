import pygame
import math
import random
from equipment import EquipmentSystem

class Player:
    def __init__(self, x, y, data):
        """初始化玩家"""
        super().__init__()
        
        # 基本属性
        self.name = data['name']
        self.gender = data.get('gender', '男')  # 默认为男性
        self.hairstyle = data['hairstyle']
        self.hair_color = data.get('hair_color', (0, 0, 0))  # 添加发色属性
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
        self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.draw_character()
        
        # 初始化装备系统
        self.equipment_system = EquipmentSystem(10, 50)  # 位置可以根据需要调整
    
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
                head_offset = 0
                head_scale = 1.0
            elif self.body_type == "普通":
                body_width = 16
                body_height = 30
                shoulder_width = 20
                waist_ratio = 0.8
                head_offset = 2
                head_scale = 1.1
            else:  # 魁梧
                body_width = 20
                body_height = 34
                shoulder_width = 24
                waist_ratio = 0.85
                head_offset = 4
                head_scale = 1.2
        else:  # 男性
            if self.body_type == "瘦小":
                body_width = 16
                body_height = 30
                shoulder_width = 20
                waist_ratio = 0.9
                head_offset = 0
                head_scale = 1.0
            elif self.body_type == "普通":
                body_width = 20
                body_height = 34
                shoulder_width = 26
                waist_ratio = 0.95
                head_offset = 2
                head_scale = 1.1
            else:  # 魁梧
                body_width = 24
                body_height = 38
                shoulder_width = 32
                waist_ratio = 1.0
                head_offset = 4
                head_scale = 1.2
        
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
        if self.body_type == "魁梧":
            leg_width += 2
        leg_spacing = 2 + (shoulder_width - 20) // 4  # 根据肩宽调整腿间距
        
        # 左腿
        pygame.draw.rect(self.image, skin_color,
                        (center_x - leg_width - leg_spacing//2, waist_y,
                         leg_width, body_bottom - waist_y))
        # 右腿
        pygame.draw.rect(self.image, skin_color,
                        (center_x + leg_spacing//2, waist_y,
                         leg_width, body_bottom - waist_y))
        
        # 绘制身体（侧面视角）
        waist_width = int(body_width * waist_ratio)
        body_points = [
            (body_left, body_top),  # 左上
            (body_right, body_top),  # 右上
            (center_x + waist_width//2, body_bottom),  # 右下
            (center_x - waist_width//2, body_bottom)   # 左下
        ]
        pygame.draw.polygon(self.image, skin_color, body_points)
        
        # 绘制手臂（侧面视角）
        arm_width = 5 if self.gender == '女' else 7
        if self.body_type == "魁梧":
            arm_width += 2
        # 后臂（稍微向后）
        pygame.draw.line(self.image, skin_color,
                        (body_left, body_top + 4),
                        (body_left - shoulder_width//3, body_top + body_height//3),
                        arm_width)
        # 前臂（稍微向前）
        pygame.draw.line(self.image, skin_color,
                        (body_right, body_top + 4),
                        (body_right + shoulder_width//3, body_top + body_height//3),
                        arm_width)
        
        # 绘制头部（侧面视角）
        head_size = int(body_width * head_scale)  # 使用head_scale调整头部大小
        face_y = body_top - head_size - 2 + head_offset
        
        # 绘制脖子
        neck_width = 6 if self.gender == '女' else 8
        if self.body_type == "魁梧":
            neck_width += 2
        neck_height = 6 + (shoulder_width - 20) // 4  # 根据体型调整脖子高度
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
        
        # 处理发型和发色
        hair_style = self.hairstyle  # 直接使用发型名称
        hair_color = getattr(self, 'hair_color', (0, 0, 0))  # 获取发色，默认黑色
        
        # 使用发型信息更新外观
        # 根据发型名称绘制不同发型
        if hair_style == "短发":
            # 绘制短发
            points = [
                (center_x - head_size//2 - 2, face_y + head_size//2),
                (center_x - head_size//4, face_y - head_size//4),
                (center_x + head_size//4, face_y - head_size//4),
                (center_x + head_size//2, face_y + head_size//4),
            ]
            pygame.draw.polygon(self.image, hair_color, points)
            
        elif hair_style == "长直发":
            points = [
                (center_x - head_size//2 - 4, face_y + head_size + 10),
                (center_x - head_size//2 - 2, face_y),
                (center_x, face_y - head_size//4),
                (center_x + head_size//2, face_y + head_size//4),
                (center_x + head_size//3, face_y + head_size + 10),
            ]
            pygame.draw.polygon(self.image, hair_color, points)
            
        elif hair_style == "蓬松短发":
            for i in range(5):
                offset = i * 4
                pygame.draw.circle(self.image, hair_color,
                                 (center_x - head_size//4 + offset,
                                  face_y + head_size//4), 6)
                                  
        elif hair_style == "双马尾":
            # 后面的马尾
            points1 = [
                (center_x - head_size//2 - 4, face_y + head_size//2),
                (center_x - head_size//2 - 8, face_y + head_size),
                (center_x - head_size//2, face_y + head_size + 15),
            ]
            # 前面的马尾
            points2 = [
                (center_x + head_size//2 + 4, face_y + head_size//2),
                (center_x + head_size//2 + 8, face_y + head_size),
                (center_x + head_size//2, face_y + head_size + 15),
            ]
            pygame.draw.polygon(self.image, hair_color, points1)
            pygame.draw.polygon(self.image, hair_color, points2)
            
        elif hair_style == "莫西干":
            for i in range(7):
                height = 10 - abs(i - 3) * 2
                pygame.draw.line(self.image, hair_color,
                               (center_x - 6 + i * 2, face_y),
                               (center_x - 6 + i * 2, face_y - height), 2)
                               
        elif hair_style == "波浪长发":
            for i in range(8):
                y_offset = math.sin(i * 0.5) * 4
                pygame.draw.line(self.image, hair_color,
                               (center_x - head_size//2 + i * 4, face_y + y_offset),
                               (center_x - head_size//2 + i * 4, face_y + head_size + 10), 3)
                               
        elif hair_style == "庞克头":
            for i in range(-3, 4):
                height = 15 - abs(i) * 3
                x = center_x + i * 4
                pygame.draw.line(self.image, hair_color,
                               (x, face_y),
                               (x + (i * 2), face_y - height), 2)
                               
        elif hair_style == "蘑菇头":
            pygame.draw.ellipse(self.image, hair_color,
                              (center_x - head_size//2 - 2,
                               face_y - head_size//4,
                               head_size + 4,
                               head_size//2 + 4))
                               
        elif hair_style == "卷发":
            for i in range(6):
                radius = 4
                x = center_x - head_size//2 + i * 6
                y = face_y + head_size//2
                pygame.draw.circle(self.image, hair_color, (int(x), int(y)), radius)
                pygame.draw.circle(self.image, hair_color, (int(x), int(y - 6)), radius)
                
        elif hair_style == "爆炸头":
            for i in range(12):
                angle = i * math.pi / 6
                length = 10 + random.randint(0, 4)
                end_x = center_x + math.cos(angle) * length
                end_y = face_y + math.sin(angle) * length
                pygame.draw.line(self.image, hair_color,
                               (center_x, face_y),
                               (end_x, end_y), 2)
        
        # 绘制眼睛（侧面）
        eye_y = face_y + head_size * 0.4
        pygame.draw.ellipse(self.image, (255, 255, 255),
                          (center_x + head_size//6, eye_y, 4, 3))
        pygame.draw.ellipse(self.image, (60, 60, 60),
                          (center_x + head_size//6 + 1, eye_y + 1, 2, 2))
        
        # 根据装备系统中的已装备物品来显示装备外观
        if hasattr(self, 'equipment_system'):
            equipped_items = self.equipment_system.get_equipped_items()
            
            # 绘制武器（如果有）
            if 'weapon' in equipped_items:
                weapon = equipped_items['weapon']
                if weapon.name == "铁剑":
                    # 绘制剑
                    pygame.draw.rect(self.image, (192, 192, 192),
                                   (body_right + 4, body_top + body_height//4, 20, 4))
                elif weapon.name == "法杖":
                    # 绘制法杖
                    pygame.draw.rect(self.image, (139, 69, 19),
                                   (body_right + 4, body_top - 10, 4, 30))
                    pygame.draw.circle(self.image, (0, 191, 255),
                                     (body_right + 6, body_top - 10), 4)
                elif weapon.name == "猎弓":
                    # 绘制弓
                    pygame.draw.arc(self.image, (139, 69, 19),
                                  (body_right + 4, body_top, 10, 30),
                                  -0.5, 0.5, 2)
            
            # 绘制盾牌（如果有）
            if 'shield' in equipped_items:
                shield = equipped_items['shield']
                if shield.name == "木盾":
                    pygame.draw.ellipse(self.image, (139, 69, 19),
                                      (body_left - 12, body_top + body_height//4, 10, 15))
                elif shield.name == "铁盾":
                    pygame.draw.ellipse(self.image, (192, 192, 192),
                                      (body_left - 12, body_top + body_height//4, 10, 15))
            
            # 绘制头盔（如果有）
            if 'helmet' in equipped_items:
                helmet = equipped_items['helmet']
                helmet_color = (192, 192, 192)  # 默认铁盔颜色
                if helmet.name == "布帽":
                    helmet_color = (139, 69, 19)
                elif helmet.name == "法师帽":
                    helmet_color = (0, 0, 139)
                pygame.draw.ellipse(self.image, helmet_color,
                                  (center_x - head_size//3, face_y - 2,
                                   head_size * 2//3, head_size//4))
            
            # 绘制胸甲（如果有）
            if 'chest' in equipped_items:
                chest = equipped_items['chest']
                armor_color = (192, 192, 192)  # 默认铁甲颜色
                if chest.name == "布衣":
                    armor_color = (139, 69, 19)
                elif chest.name == "法袍":
                    armor_color = (0, 0, 139)
                # 在身体上方绘制装甲轮廓
                armor_points = [
                    (body_left - 2, body_top),
                    (body_right + 2, body_top),
                    (center_x + waist_width//2 + 2, waist_y),
                    (center_x - waist_width//2 - 2, waist_y)
                ]
                pygame.draw.polygon(self.image, armor_color, armor_points)
        
        # 如果不是朝右，翻转图像
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

    def draw_character(self):
        """绘制角色"""
        # 清空图像
        self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        
        # 获取动画偏移量
        leg_offset = math.sin(self.animation_frame * 0.2) * 4 if self.state == "walk" else 0
        arm_offset = -math.sin(self.animation_frame * 0.2) * 4 if self.state == "walk" else 0
        
        # 更新动画帧
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer > self.animation_speed:
            self.animation_frame += 1
            self.animation_timer = current_time
        
        # 绘制角色
        self.update_appearance()

    def update(self, world):
        """更新玩家状态"""
        if self.preview_mode:
            return
        
        # 应用重力
        self.dy += 0.5
        
        # 限制最大下落速度
        if self.dy > 10:
            self.dy = 10
        
        # 更新位置
        new_rect = self.rect.copy()
        new_rect.x += self.x_speed
        new_rect.y += self.dy
        
        # 检测与世界的碰撞
        grid_size = world.grid_size
        
        # 获取玩家周围的网格坐标
        left = new_rect.left // grid_size
        right = new_rect.right // grid_size
        top = new_rect.top // grid_size
        bottom = new_rect.bottom // grid_size
        
        self.on_ground = False
        
        # 垂直碰撞检测
        if self.dy > 0:  # 下落
            for x in range(left, right + 1):
                if 0 <= x < world.width and 0 <= bottom < world.height:
                    if world.grid[bottom][x] != world.EMPTY:
                        new_rect.bottom = bottom * grid_size
                        self.dy = 0
                        self.on_ground = True
                        self.jumps_left = 2  # 着地时重置跳跃次数
                        break
        elif self.dy < 0:  # 上升
            for x in range(left, right + 1):
                if 0 <= x < world.width and 0 <= top < world.height:
                    if world.grid[top][x] != world.EMPTY:
                        new_rect.top = (top + 1) * grid_size
                        self.dy = 0
                        break
        
        # 水平碰撞检测
        if self.x_speed > 0:  # 向右移动
            for y in range(top, bottom + 1):
                if 0 <= right < world.width and 0 <= y < world.height:
                    if world.grid[y][right] != world.EMPTY:
                        new_rect.right = right * grid_size
                        self.x_speed = 0
                        break
        elif self.x_speed < 0:  # 向左移动
            for y in range(top, bottom + 1):
                if 0 <= left < world.width and 0 <= y < world.height:
                    if world.grid[y][left] != world.EMPTY:
                        new_rect.left = (left + 1) * grid_size
                        self.x_speed = 0
                        break
        
        # 更新位置
        self.rect = new_rect
    
    def move_left(self):
        """向左移动"""
        self.x_speed = -5
        self.facing_right = False
        self.state = "walk"
    
    def move_right(self):
        """向右移动"""
        self.x_speed = 5
        self.facing_right = True
        self.state = "walk"
    
    def stop(self):
        """停止移动"""
        self.x_speed = 0
        self.state = "idle"
    
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
            self.state = "jump"
    
    def draw(self, surface, camera_x, camera_y):
        """绘制玩家"""
        # 计算屏幕位置
        screen_x = self.rect.x - camera_x
        screen_y = self.rect.y - camera_y
        
        # 如果玩家面向左边，翻转图像
        image_to_draw = self.image
        if not self.facing_right:
            image_to_draw = pygame.transform.flip(self.image, True, False)
        
        # 绘制玩家
        surface.blit(image_to_draw, (screen_x, screen_y))
        
        # 如果装备系统可见，绘制装备界面
        if self.equipment_system.visible:
            self.equipment_system.draw(surface)
    
    def handle_event(self, event):
        """处理玩家相关的事件"""
        # 处理装备系统事件
        if self.equipment_system.visible:
            return self.equipment_system.handle_event(event)
        return False
    
    def toggle_equipment_system(self):
        """切换装备系统显示状态"""
        self.equipment_system.visible = not self.equipment_system.visible 