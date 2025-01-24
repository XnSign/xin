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
        
        # 根据性别和体型调整身体比例（更真实的人体比例）
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
        waist_y = body_top + body_height * 0.4  # 更自然的腰部位置
        
        # 根据性别设置肤色（更自然的肤色）
        if self.gender == '女':
            skin_color = (255, 223, 196)  # 更自然的肤色
            skin_shadow = (235, 203, 176)  # 阴影色
        else:
            skin_color = (240, 200, 160)  # 更自然的肤色
            skin_shadow = (220, 180, 140)  # 阴影色
        
        # 绘制腿部（更自然的形状）
        leg_width = 6 if self.gender == '女' else 8
        leg_spacing = 4
        # 左腿
        pygame.draw.rect(self.image, skin_color,
                        (center_x - leg_width - leg_spacing, waist_y,
                         leg_width, body_bottom - waist_y))
        # 右腿
        pygame.draw.rect(self.image, skin_color,
                        (center_x + leg_spacing, waist_y,
                         leg_width, body_bottom - waist_y))
        
        # 绘制身体（考虑性别差异和更自然的形状）
        if self.gender == '女':
            # 女性身体（更自然的曲线）
            waist_width = body_width * waist_ratio
            # 上半身（带曲线）
            pygame.draw.polygon(self.image, skin_color, [
                (center_x - shoulder_width//2, body_top),  # 左肩
                (center_x + shoulder_width//2, body_top),  # 右肩
                (center_x + waist_width//2, waist_y),     # 右腰
                (center_x - waist_width//2, waist_y)      # 左腰
            ])
            # 添加胸部轮廓（柔和的曲线）
            chest_y = body_top + body_height * 0.2
            pygame.draw.arc(self.image, skin_shadow,
                           (center_x - waist_width//2 - 2, chest_y,
                            waist_width + 4, 8), 0, math.pi, 2)
        else:
            # 男性身体（更强壮的轮廓）
            pygame.draw.polygon(self.image, skin_color, [
                (center_x - shoulder_width//2, body_top),      # 左肩
                (center_x + shoulder_width//2, body_top),      # 右肩
                (center_x + body_width//2, body_bottom - 4),   # 右臀
                (center_x - body_width//2, body_bottom - 4)    # 左臀
            ])
            # 添加肌肉轮廓
            if self.body_type in ["普通", "魁梧"]:
                # 胸肌
                chest_y = body_top + body_height * 0.2
                pygame.draw.arc(self.image, skin_shadow,
                              (center_x - shoulder_width//4, chest_y,
                               shoulder_width//2, 10), 0, math.pi, 3)
                # 腹肌
                for i in range(2):
                    y = chest_y + 8 + i * 6
                    pygame.draw.line(self.image, skin_shadow,
                                   (center_x - 6, y),
                                   (center_x + 6, y), 2)
        
        # 绘制手臂（更自然的形状）
        arm_width = 5 if self.gender == '女' else 7
        # 左手臂
        pygame.draw.line(self.image, skin_color,
                        (center_x - shoulder_width//2, body_top + 4),
                        (center_x - shoulder_width//2 - 4, body_top + body_height//3),
                        arm_width)
        # 右手臂
        pygame.draw.line(self.image, skin_color,
                        (center_x + shoulder_width//2, body_top + 4),
                        (center_x + shoulder_width//2 + 4, body_top + body_height//3),
                        arm_width)
        
        # 绘制头部（更自然的形状）
        head_size = int(body_width * 1.2)
        face_y = body_top - head_size - 2
        
        # 绘制脖子（更自然的形状）
        neck_width = 6 if self.gender == '女' else 8
        neck_height = 6
        pygame.draw.rect(self.image, skin_color,
                        (center_x - neck_width//2, face_y + head_size,
                         neck_width, neck_height))
        
        # 绘制头部轮廓
        pygame.draw.ellipse(self.image, skin_color,
                           (center_x - head_size//2, face_y,
                            head_size, head_size))
        
        # 设置发色（更自然的颜色）
        if self.hairstyle.startswith("金色"):
            hair_color = (255, 215, 0)
            hair_shadow = (218, 165, 32)
        elif self.hairstyle.startswith("褐色"):
            hair_color = (139, 69, 19)
            hair_shadow = (101, 67, 33)
        else:  # 黑色
            hair_color = (30, 30, 30)
            hair_shadow = (10, 10, 10)
        
        # 绘制发型（更自然的发型）
        if self.hairstyle.endswith("短发"):
            if self.gender == '女':
                # 女性短发（更蓬松自然）
                for i in range(5):
                    y_offset = i * 2
                    curve_points = []
                    for t in range(0, 101, 5):
                        t = t / 100
                        x = center_x - 14 + t * 28
                        y = face_y + y_offset + math.sin(t * math.pi) * 4
                        curve_points.append((int(x), int(y)))
                    if len(curve_points) > 1:
                        pygame.draw.lines(self.image, hair_color, False, curve_points, 2)
                        # 添加发丝效果
                        if i % 2 == 0:
                            pygame.draw.lines(self.image, hair_shadow, False, curve_points, 1)
            else:
                # 男性短发（更利落自然）
                for i in range(4):
                    y_offset = i * 2
                    curve_points = []
                    for t in range(0, 101, 5):
                        t = t / 100
                        x = center_x - 12 + t * 24
                        y = face_y + y_offset + math.sin(t * math.pi) * 3
                        curve_points.append((int(x), int(y)))
                    if len(curve_points) > 1:
                        pygame.draw.lines(self.image, hair_color, False, curve_points, 2)
        else:  # 长发
            if self.gender == '女':
                # 女性长发（更飘逸自然）
                for i in range(7):
                    curve_points = []
                    for t in range(0, 101, 4):
                        t = t / 100
                        x = center_x - 18 + i * 6 + math.sin(t * math.pi * 2) * 3
                        y = face_y + t * 45
                        curve_points.append((int(x), int(y)))
                    if len(curve_points) > 1:
                        pygame.draw.lines(self.image, hair_color, False, curve_points, 2)
                        # 添加发丝效果
                        if i % 2 == 0:
                            pygame.draw.lines(self.image, hair_shadow, False, curve_points, 1)
            else:
                # 男性长发（更自然）
                for i in range(6):
                    curve_points = []
                    for t in range(0, 101, 5):
                        t = t / 100
                        x = center_x - 15 + i * 6
                        y = face_y + t * 40
                        curve_points.append((int(x), int(y)))
                    if len(curve_points) > 1:
                        pygame.draw.lines(self.image, hair_color, False, curve_points, 2)
        
        # 眼睛（更自然的形状）
        eye_y = face_y + head_size * 0.35
        if self.gender == '女':
            # 女性眼睛（更大更有神）
            # 眼白
            pygame.draw.ellipse(self.image, (255, 255, 255),
                              (center_x - 9, eye_y, 7, 4))
            pygame.draw.ellipse(self.image, (255, 255, 255),
                              (center_x + 2, eye_y, 7, 4))
            # 眼珠
            pygame.draw.ellipse(self.image, (60, 60, 60),
                              (center_x - 7, eye_y + 1, 3, 3))
            pygame.draw.ellipse(self.image, (60, 60, 60),
                              (center_x + 4, eye_y + 1, 3, 3))
            # 眼睑
            pygame.draw.arc(self.image, skin_shadow,
                           (center_x - 9, eye_y - 1, 7, 4),
                           0, math.pi, 1)
            pygame.draw.arc(self.image, skin_shadow,
                           (center_x + 2, eye_y - 1, 7, 4),
                           0, math.pi, 1)
            # 睫毛
            for i in range(3):
                offset = i * 2
                pygame.draw.line(self.image, (0, 0, 0),
                               (center_x - 8 + offset, eye_y),
                               (center_x - 9 + offset, eye_y - 1), 1)
                pygame.draw.line(self.image, (0, 0, 0),
                               (center_x + 3 + offset, eye_y),
                               (center_x + 2 + offset, eye_y - 1), 1)
        else:
            # 男性眼睛（更有神）
            # 眼白
            pygame.draw.ellipse(self.image, (255, 255, 255),
                              (center_x - 8, eye_y, 6, 3))
            pygame.draw.ellipse(self.image, (255, 255, 255),
                              (center_x + 2, eye_y, 6, 3))
            # 眼珠
            pygame.draw.ellipse(self.image, (40, 40, 40),
                              (center_x - 6, eye_y, 2, 2))
            pygame.draw.ellipse(self.image, (40, 40, 40),
                              (center_x + 4, eye_y, 2, 2))
            # 眼睑
            pygame.draw.arc(self.image, skin_shadow,
                           (center_x - 8, eye_y - 1, 6, 3),
                           0, math.pi, 1)
            pygame.draw.arc(self.image, skin_shadow,
                           (center_x + 2, eye_y - 1, 6, 3),
                           0, math.pi, 1)
        
        # 眉毛（更自然的形状）
        brow_y = eye_y - 5
        if self.gender == '女':
            # 女性眉毛（更细腻）
            pygame.draw.arc(self.image, hair_color,
                           (center_x - 8, brow_y, 10, 4),
                           0, math.pi, 1)
            pygame.draw.arc(self.image, hair_color,
                           (center_x + 2, brow_y, 10, 4),
                           0, math.pi, 1)
        else:
            # 男性眉毛（更浓重）
            pygame.draw.arc(self.image, hair_color,
                           (center_x - 7, brow_y, 8, 3),
                           0, math.pi, 2)
            pygame.draw.arc(self.image, hair_color,
                           (center_x + 1, brow_y, 8, 3),
                           0, math.pi, 2)
        
        # 鼻子（更自然的形状）
        nose_y = eye_y + 4
        if self.gender == '女':
            # 女性鼻子（更小巧）
            pygame.draw.line(self.image, skin_shadow,
                            (center_x, nose_y),
                            (center_x, nose_y + 3), 1)
        else:
            # 男性鼻子（更挺拔）
            pygame.draw.line(self.image, skin_shadow,
                            (center_x, nose_y),
                            (center_x, nose_y + 4), 2)
        
        # 嘴巴（更自然的形状）
        mouth_y = nose_y + 6
        if self.gender == '女':
            # 女性嘴唇（更饱满）
            lip_color = (200, 100, 100)
            # 上唇
            pygame.draw.arc(self.image, lip_color,
                           (center_x - 3, mouth_y - 1, 6, 3),
                           math.pi, 2*math.pi, 1)
            # 下唇
            pygame.draw.arc(self.image, lip_color,
                           (center_x - 4, mouth_y - 1, 8, 4),
                           0, math.pi, 2)
        else:
            # 男性嘴唇（更薄）
            pygame.draw.arc(self.image, skin_shadow,
                           (center_x - 3, mouth_y, 6, 2),
                           0, math.pi, 1)
        
        # 根据职业添加装备（更真实的装备）
        if self.class_type == "战士":
            if self.gender == '女':
                # 女性战士装备（更轻盈精致）
                # 轻型护肩
                shoulder_color = (192, 192, 192)
                highlight_color = (220, 220, 220)
                for i in range(2):
                    x_offset = [-shoulder_width//2 - 2, shoulder_width//2 - 8][i]
                    pygame.draw.ellipse(self.image, shoulder_color,
                                      (center_x + x_offset, body_top - 4, 10, 8))
                    pygame.draw.arc(self.image, highlight_color,
                                  (center_x + x_offset, body_top - 4, 10, 8),
                                  math.pi/4, 3*math.pi/4, 2)
                
                # 轻型护甲
                armor_color = (180, 180, 180)
                for i in range(3):
                    y = body_top + i * 8
                    pygame.draw.line(self.image, armor_color,
                                   (body_left + 2, y),
                                   (body_right - 2, y), 2)
                    # 添加金属光泽
                    pygame.draw.line(self.image, highlight_color,
                                   (body_left + 4, y - 1),
                                   (body_right - 4, y - 1), 1)
            else:
                # 男性战士装备（更厚重威武）
                # 重型护肩
                shoulder_color = (160, 160, 160)
                highlight_color = (200, 200, 200)
                shadow_color = (120, 120, 120)
                for i in range(2):
                    x_offset = [-shoulder_width//2 - 4, shoulder_width//2 - 10][i]
                    # 主体
                    pygame.draw.ellipse(self.image, shoulder_color,
                                      (center_x + x_offset, body_top - 6, 14, 12))
                    # 高光
                    pygame.draw.arc(self.image, highlight_color,
                                  (center_x + x_offset, body_top - 6, 14, 12),
                                  math.pi/4, 3*math.pi/4, 2)
                    # 装饰钉
                    pygame.draw.circle(self.image, highlight_color,
                                     (center_x + x_offset + 7, body_top), 2)
                
                # 重型护甲
                armor_color = (140, 140, 140)
                plate_height = 7
                for i in range(4):
                    y = body_top + i * plate_height
                    # 主体装甲板
                    pygame.draw.rect(self.image, armor_color,
                                   (body_left, y, body_width, plate_height))
                    # 高光
                    pygame.draw.line(self.image, highlight_color,
                                   (body_left + 2, y + 1),
                                   (body_right - 2, y + 1), 1)
                    # 阴影
                    pygame.draw.line(self.image, shadow_color,
                                   (body_left, y + plate_height - 1),
                                   (body_right, y + plate_height - 1), 1)
        
        elif self.class_type == "法师":
            if self.gender == '女':
                # 女性法师长袍（更飘逸华丽）
                robe_color = (100, 50, 150)
                highlight_color = (140, 90, 190)
                # 绘制飘逸的长袍
                for i in range(5):
                    curve_points = []
                    for t in range(0, 101, 4):
                        t = t / 100
                        x = body_left + body_width * t + math.sin(t * math.pi * 2 + i * 0.5) * 4
                        y = body_top + body_height * t
                        curve_points.append((int(x), int(y)))
                    if len(curve_points) > 1:
                        pygame.draw.lines(self.image, robe_color, False, curve_points, 2)
                        if i % 2 == 0:  # 添加装饰线
                            pygame.draw.lines(self.image, highlight_color, False, curve_points, 1)
            else:
                # 男性法师长袍（更庄重大气）
                robe_color = (80, 30, 120)
                highlight_color = (120, 70, 160)
                # 主体长袍
                robe_points = [
                    (body_left - 4, body_top),
                    (body_right + 4, body_top),
                    (body_right + 8, body_bottom),
                    (body_left - 8, body_bottom)
                ]
                pygame.draw.polygon(self.image, robe_color, robe_points)
                # 添加褶皱效果
                for i in range(3):
                    y = body_top + i * 12
                    pygame.draw.line(self.image, highlight_color,
                                   (body_left - 4 + i * 2, y),
                                   (body_right + 4 - i * 2, y), 2)
        
        elif self.class_type == "弓箭手":
            if self.gender == '女':
                # 女性弓箭手装备（更轻巧灵活）
                leather_color = (160, 82, 45)
                highlight_color = (180, 102, 65)
                
                # 轻型皮甲
                for i in range(4):
                    y = body_top + i * 8
                    pygame.draw.line(self.image, leather_color,
                                   (body_left + 1, y),
                                   (body_right - 1, y), 2)
                    # 添加皮革纹理
                    if i % 2 == 0:
                        pygame.draw.line(self.image, highlight_color,
                                       (body_left + 3, y - 1),
                                       (body_right - 3, y - 1), 1)
                
                # 小型箭袋
                quiver_color = (140, 70, 20)
                quiver_points = [
                    (body_right + 3, body_top),
                    (body_right + 6, body_top),
                    (body_right + 8, body_bottom - 5),
                    (body_right + 5, body_bottom - 5)
                ]
                pygame.draw.polygon(self.image, quiver_color, quiver_points)
                # 箭矢
                arrow_color = (121, 85, 61)
                arrow_head = (101, 67, 33)
                for i in range(3):
                    start_pos = (body_right + 5, body_top + 4 + i * 5)
                    end_pos = (body_right + 6, body_top + 12 + i * 5)
                    # 箭杆
                    pygame.draw.line(self.image, arrow_color, start_pos, end_pos, 1)
                    # 箭头
                    pygame.draw.polygon(self.image, arrow_head, [
                        end_pos,
                        (end_pos[0] + 2, end_pos[1] - 1),
                        (end_pos[0] + 2, end_pos[1] + 1)
                    ])
                    # 箭羽
                    feather_color = (200, 200, 200)
                    pygame.draw.line(self.image, feather_color,
                                   start_pos,
                                   (start_pos[0] + 1, start_pos[1] - 2), 1)
            else:
                # 男性弓箭手装备（更厚重实用）
                leather_color = (139, 69, 19)
                highlight_color = (169, 99, 49)
                shadow_color = (109, 39, 0)
                
                # 重型皮甲
                for i in range(5):
                    y = body_top + i * 6
                    # 主体皮甲
                    pygame.draw.rect(self.image, leather_color,
                                   (body_left - 2, y, body_width + 4, 5))
                    # 添加皮革纹理
                    pygame.draw.line(self.image, highlight_color,
                                   (body_left, y + 1),
                                   (body_right, y + 1), 1)
                    pygame.draw.line(self.image, shadow_color,
                                   (body_left, y + 4),
                                   (body_right, y + 4), 1)
                
                # 大型箭袋
                quiver_color = (120, 60, 20)
                highlight_color = (150, 90, 50)
                quiver_points = [
                    (body_right + 4, body_top - 2),
                    (body_right + 8, body_top - 2),
                    (body_right + 12, body_bottom),
                    (body_right + 6, body_bottom)
                ]
                pygame.draw.polygon(self.image, quiver_color, quiver_points)
                # 添加皮革纹理
                for i in range(3):
                    y = body_top + i * 10
                    pygame.draw.line(self.image, highlight_color,
                                   (body_right + 6, y),
                                   (body_right + 10, y), 1)
                
                # 箭矢
                arrow_color = (101, 67, 33)
                arrow_head = (81, 47, 13)
                for i in range(4):
                    start_pos = (body_right + 7, body_top + i * 6)
                    end_pos = (body_right + 9, body_top + 10 + i * 6)
                    # 箭杆
                    pygame.draw.line(self.image, arrow_color, start_pos, end_pos, 2)
                    # 箭头
                    pygame.draw.polygon(self.image, arrow_head, [
                        end_pos,
                        (end_pos[0] + 3, end_pos[1] - 2),
                        (end_pos[0] + 3, end_pos[1] + 2)
                    ])
                    # 箭羽
                    feather_color = (180, 180, 180)
                    pygame.draw.line(self.image, feather_color,
                                   start_pos,
                                   (start_pos[0] + 2, start_pos[1] - 3), 2)
        
        # 添加阴影和高光效果
        # 身体阴影
        shadow_color = tuple(max(c - 30, 0) for c in skin_color)
        pygame.draw.line(self.image, shadow_color,
                        (body_left, body_bottom - 2),
                        (body_right, body_bottom - 2), 2)
        
        # 添加地面阴影
        shadow_surface = pygame.Surface((30, 4), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, 100)  # 半透明黑色
        pygame.draw.ellipse(shadow_surface, shadow_color,
                           (0, 0, 30, 4))
        self.image.blit(shadow_surface,
                        (center_x - 15, body_bottom + 2))

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