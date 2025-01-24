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
        
        # 根据性别和体型调整身体比例
        if self.gender == '女':
            if self.body_type == "瘦小":
                body_width = 12
                shoulder_width = 16
                head_size = 0.85
                waist_ratio = 0.8  # 腰部收缩比例
            elif self.body_type == "魁梧":
                body_width = 18
                shoulder_width = 24
                head_size = 0.95
                waist_ratio = 0.85
            else:  # 普通体型
                body_width = 14
                shoulder_width = 20
                head_size = 0.9
                waist_ratio = 0.75
        else:  # 男性
            if self.body_type == "瘦小":
                body_width = 14
                shoulder_width = 18
                head_size = 0.9
                waist_ratio = 0.9
            elif self.body_type == "魁梧":
                body_width = 22
                shoulder_width = 30
                head_size = 1.1
                waist_ratio = 0.95
            else:  # 普通体型
                body_width = 18
                shoulder_width = 24
                head_size = 1.0
                waist_ratio = 0.9

        # 角色中心点
        center_x = 24
        center_y = 32

        # 根据状态调整姿势
        if self.state == "walk":
            angle = math.sin(self.animation_frame * 0.2) * (12 if self.gender == '女' else 15)  # 女性走路幅度稍小
        else:
            angle = 0

        # 绘制腿部（带运动效果）
        leg_color = skin_color
        leg_length = 20
        leg_width = 4 if self.gender == '女' else 5  # 女性腿部稍细
        
        if self.state == "walk":
            # 左腿（后腿）
            left_leg_angle = -angle
            left_leg_end = (
                center_x - body_width//4 + math.sin(math.radians(left_leg_angle)) * leg_length,
                center_y + 15 + math.cos(math.radians(left_leg_angle)) * leg_length
            )
            pygame.draw.line(self.image, leg_color,
                           (center_x - body_width//4, center_y + 15),
                           left_leg_end, leg_width)
            
            # 右腿（前腿）
            right_leg_angle = angle
            right_leg_end = (
                center_x + body_width//4 + math.sin(math.radians(right_leg_angle)) * leg_length,
                center_y + 15 + math.cos(math.radians(right_leg_angle)) * leg_length
            )
            pygame.draw.line(self.image, leg_color,
                           (center_x + body_width//4, center_y + 15),
                           right_leg_end, leg_width + 1)
        else:
            # 静止状态的腿部
            pygame.draw.line(self.image, leg_color,
                           (center_x - body_width//4, center_y + 15),
                           (center_x - body_width//3 - 2, center_y + 30), leg_width)
            pygame.draw.line(self.image, leg_color,
                           (center_x + body_width//4, center_y + 15),
                           (center_x + body_width//3 + 2, center_y + 30), leg_width + 1)

        # 绘制身体（带透视效果和腰部曲线）
        body_top = center_y - 15
        body_bottom = center_y + 15
        body_left = center_x - body_width//2
        body_right = center_x + body_width//2
        
        # 身体主体（梯形）
        waist_y = (body_top + body_bottom) // 2
        waist_offset = int(body_width * (1 - waist_ratio) // 2)
        
        body_points = [
            (body_left - 2, body_top),      # 左上
            (body_right + 2, body_top),     # 右上
            (body_right + 4, body_bottom),  # 右下
            (body_left - 4, body_bottom)    # 左下
        ]
        
        # 如果是女性，添加腰部曲线
        if self.gender == '女':
            body_points = [
                (body_left - 2, body_top),      # 左上
                (body_right + 2, body_top),     # 右上
                (body_right + 2, waist_y - 5),  # 右上腰
                (body_right - waist_offset + 2, waist_y),  # 右腰
                (body_right + 4, body_bottom),  # 右下
                (body_left - 4, body_bottom),   # 左下
                (body_left + waist_offset - 2, waist_y),  # 左腰
                (body_left - 2, waist_y - 5),   # 左上腰
            ]
        
        pygame.draw.polygon(self.image, skin_color, body_points)
        
        # 添加身体阴影效果
        shadow_color = tuple(max(c - 30, 0) for c in skin_color)
        pygame.draw.line(self.image, shadow_color,
                        body_points[0], body_points[-1], 2)
        pygame.draw.line(self.image, shadow_color,
                        (body_left, body_top + 10),
                        (body_left - 2, body_bottom - 5), 2)

        # 绘制手臂（带运动效果）
        arm_color = skin_color
        arm_length = 15
        arm_width = 3 if self.gender == '女' else 4  # 女性手臂稍细
        
        if self.state == "walk":
            # 左手臂（后臂）
            left_arm_angle = angle
            left_arm_end = (
                center_x - body_width//2 + math.sin(math.radians(left_arm_angle)) * arm_length,
                center_y - 5 + math.cos(math.radians(left_arm_angle)) * arm_length
            )
            pygame.draw.line(self.image, arm_color,
                           (center_x - body_width//2, center_y - 5),
                           left_arm_end, arm_width)
            
            # 右手臂（前臂）
            right_arm_angle = -angle
            right_arm_end = (
                center_x + body_width//2 + math.sin(math.radians(right_arm_angle)) * arm_length,
                center_y - 5 + math.cos(math.radians(right_arm_angle)) * arm_length
            )
            pygame.draw.line(self.image, arm_color,
                           (center_x + body_width//2, center_y - 5),
                           right_arm_end, arm_width + 1)
        else:
            # 静止状态的手臂
            pygame.draw.line(self.image, arm_color,
                           (center_x - body_width//2, center_y - 5),
                           (center_x - body_width//2 - 6, center_y + 8), arm_width)
            pygame.draw.line(self.image, arm_color,
                           (center_x + body_width//2, center_y - 5),
                           (center_x + body_width//2 + 6, center_y + 8), arm_width + 1)

        # 绘制头部（更自然的形状）
        head_width = int(20 * head_size)
        head_height = int(24 * head_size)
        head_surface = pygame.Surface((head_width, head_height), pygame.SRCALPHA)
        
        # 绘制脖子（女性更细）
        neck_width = 4 if self.gender == '女' else 6
        neck_height = 4
        pygame.draw.rect(self.image, skin_color,
                        (center_x - neck_width//2, body_top - neck_height, neck_width, neck_height))
        
        # 绘制头部主体（女性更圆润）
        if self.gender == '女':
            pygame.draw.ellipse(head_surface, skin_color, (0, 0, head_width, head_height))
        else:
            # 男性下巴更方
            pygame.draw.ellipse(head_surface, skin_color, (0, 0, head_width, int(head_height * 0.9)))
            jaw_height = int(head_height * 0.2)
            pygame.draw.rect(head_surface, skin_color,
                           (head_width//6, head_height - jaw_height,
                            head_width*2//3, jaw_height))
        
        # 添加下巴的弧度
        if self.gender == '女':
            # 女性下巴更尖细
            jaw_points = [
                (head_width//4, head_height-6),
                (head_width//2, head_height-2),
                (head_width*3//4, head_height-6)
            ]
        else:
            # 男性下巴更宽
            jaw_points = [
                (head_width//4, head_height-6),
                (head_width//2, head_height-4),
                (head_width*3//4, head_height-6)
            ]
        pygame.draw.lines(head_surface, skin_color, False, jaw_points, 2)
        
        # 旋转头部以匹配45度视角
        rotated_head = pygame.transform.rotate(head_surface, -15)
        self.image.blit(rotated_head, (center_x - head_width//2, body_top - head_height))

        # 绘制面部特征
        face_y = body_top - head_height + head_height//3
        
        # 眼睛（性别差异）
        eye_color = (50, 50, 50)
        if self.gender == '女':
            # 女性眼睛更大更圆
            # 右眼（近）
            pygame.draw.ellipse(self.image, eye_color,
                              (center_x + 2, face_y, 5, 4))  # 眼白
            pygame.draw.ellipse(self.image, (0, 0, 0),
                              (center_x + 3, face_y + 1, 3, 3))  # 瞳孔
            # 睫毛
            pygame.draw.line(self.image, (0, 0, 0),
                           (center_x + 2, face_y),
                           (center_x + 7, face_y - 1), 1)
            
            # 左眼（远）
            pygame.draw.ellipse(self.image, eye_color,
                              (center_x - 6, face_y - 1, 4, 3))  # 眼白
            pygame.draw.ellipse(self.image, (0, 0, 0),
                              (center_x - 5, face_y - 1, 2, 2))  # 瞳孔
            # 睫毛
            pygame.draw.line(self.image, (0, 0, 0),
                           (center_x - 6, face_y - 1),
                           (center_x - 3, face_y - 2), 1)
        else:
            # 男性眼睛更小更锐利
            # 右眼（近）
            pygame.draw.ellipse(self.image, eye_color,
                              (center_x + 2, face_y, 4, 3))  # 眼白
            pygame.draw.ellipse(self.image, (0, 0, 0),
                              (center_x + 3, face_y, 2, 2))  # 瞳孔
            
            # 左眼（远）
            pygame.draw.ellipse(self.image, eye_color,
                              (center_x - 5, face_y - 1, 3, 2))  # 眼白
            pygame.draw.ellipse(self.image, (0, 0, 0),
                              (center_x - 4, face_y - 1, 1, 1))  # 瞳孔

        # 眉毛（性别差异）
        if self.gender == '女':
            # 女性眉毛更细更弯
            pygame.draw.arc(self.image, hair_color,
                          (center_x - 7, face_y - 5, 9, 5), 0, math.pi, 1)
            pygame.draw.arc(self.image, hair_color,
                          (center_x + 2, face_y - 5, 9, 5), 0, math.pi, 1)
        else:
            # 男性眉毛更粗更直
            pygame.draw.arc(self.image, hair_color,
                          (center_x - 6, face_y - 4, 8, 4), 0, math.pi, 2)
            pygame.draw.arc(self.image, hair_color,
                          (center_x + 2, face_y - 4, 8, 4), 0, math.pi, 2)

        # 嘴巴（性别差异）
        mouth_y = face_y + 8
        if self.gender == '女':
            # 女性嘴唇更饱满
            lip_color = (200, 100, 100)
            pygame.draw.arc(self.image, lip_color,
                          (center_x - 3, mouth_y, 8, 4), 0, math.pi, 2)
            # 上唇
            pygame.draw.arc(self.image, lip_color,
                          (center_x - 2, mouth_y - 1, 6, 2), math.pi, 2*math.pi, 1)
        else:
            # 男性嘴唇更薄
            pygame.draw.arc(self.image, (200, 100, 100),
                          (center_x - 3, mouth_y, 8, 3), 0, math.pi, 2)

        # 绘制发型（根据性别调整）
        if self.hairstyle:
            if "短" in self.hairstyle:
                if self.gender == '女':
                    # 女性短发更蓬松
                    for i in range(4):
                        y_offset = i * 2
                        curve_points = []
                        for t in range(0, 101, 10):
                            t = t / 100
                            x = center_x - 12 + t * 24
                            y = body_top - head_height + 2 + y_offset + math.sin(t * math.pi) * 4
                            curve_points.append((int(x), int(y)))
                        if len(curve_points) > 1:
                            pygame.draw.lines(self.image, hair_color, False, curve_points, 2)
                else:
                    # 男性短发更利落
                    for i in range(3):
                        y_offset = i * 2
                        curve_points = []
                        for t in range(0, 101, 10):
                            t = t / 100
                            x = center_x - 10 + t * 20
                            y = body_top - head_height + 4 + y_offset + math.sin(t * math.pi) * 3
                            curve_points.append((int(x), int(y)))
                        if len(curve_points) > 1:
                            pygame.draw.lines(self.image, hair_color, False, curve_points, 2)
            
            elif "长" in self.hairstyle:
                # 长发（自然飘动）
                strand_count = 5 if self.gender == '女' else 4  # 女性头发更多
                for i in range(strand_count):
                    start_x = center_x - 14 + i * 7
                    start_y = body_top - head_height + 4
                    points = []
                    
                    # 使用正弦波创造飘动效果
                    wave_amplitude = 4 if self.gender == '女' else 3
                    wave_frequency = 0.15 if self.gender == '女' else 0.2
                    wave_phase = self.animation_frame * 0.1 + i
                    
                    for t in range(0, 26 if self.gender == '女' else 21):
                        t = t / (25 if self.gender == '女' else 20)
                        x = start_x + math.sin(t * math.pi * wave_frequency + wave_phase) * wave_amplitude
                        y = start_y + t * (30 if self.gender == '女' else 25)
                        points.append((int(x), int(y)))
                    
                    if len(points) > 1:
                        pygame.draw.lines(self.image, hair_color, False, points, 2)

        # 根据职业和性别添加装备
        if self.class_type == "战士":
            # 盔甲（性别差异）
            armor_color = (150, 150, 150)
            highlight_color = (180, 180, 180)
            shadow_color = (120, 120, 120)
            
            if self.gender == '女':
                # 女性盔甲更轻盈
                # 胸甲（考虑曲线）
                chest_points = [p for p in body_points]
                pygame.draw.polygon(self.image, armor_color, chest_points)
                
                # 装饰线条更细致
                for i in range(4):
                    y = body_top + i * 8
                    pygame.draw.line(self.image, highlight_color,
                                   (body_left, y),
                                   (body_right, y), 1)
                
                # 肩甲更小巧
                pygame.draw.circle(self.image, armor_color,
                                 (center_x + shoulder_width//2, body_top), 5)
                pygame.draw.circle(self.image, armor_color,
                                 (center_x - shoulder_width//2, body_top), 4)
            else:
                # 男性盔甲更厚重
                # 胸甲
                chest_points = [p for p in body_points]
                pygame.draw.polygon(self.image, armor_color, chest_points)
                
                # 添加盔甲纹理
                for i in range(3):
                    y = body_top + i * 10
                    pygame.draw.line(self.image, highlight_color,
                                   (body_left, y),
                                   (body_right, y), 2)
                    pygame.draw.line(self.image, shadow_color,
                                   (body_left, y + 1),
                                   (body_right, y + 1), 2)
                
                # 肩甲
                pygame.draw.circle(self.image, armor_color,
                                 (center_x + shoulder_width//2, body_top), 6)
                pygame.draw.circle(self.image, armor_color,
                                 (center_x - shoulder_width//2, body_top), 5)
            
            # 装饰边缘
            pygame.draw.lines(self.image, highlight_color, True, chest_points, 2)
            
        elif self.class_type == "法师":
            # 法师长袍（性别差异）
            if self.gender == '女':
                # 女性法师长袍更轻盈飘逸
                robe_color = (100, 0, 150)  # 更亮的紫色
                robe_highlight = (120, 20, 170)
                
                # 主体长袍（更贴身）
                robe_points = [
                    (body_left - 4, body_top - 5),
                    (body_right + 4, body_top - 5),
                    (body_right + 6, body_bottom + 12),
                    (body_left - 6, body_bottom + 12)
                ]
                pygame.draw.polygon(self.image, robe_color, robe_points)
                
                # 添加更多褶皱和流动效果
                for i in range(5):
                    y = body_top + i * 6
                    wave = math.sin(self.animation_frame * 0.15 + i * 0.4) * 3
                    pygame.draw.line(self.image, robe_highlight,
                                   (body_left - 4 + wave, y),
                                   (body_right + 4 + wave, y), 1)
            else:
                # 男性法师长袍更庄重
                robe_color = (70, 0, 120)
                robe_highlight = (90, 20, 140)
                
                # 主体长袍
                robe_points = [
                    (body_left - 6, body_top - 5),
                    (body_right + 6, body_top - 5),
                    (body_right + 8, body_bottom + 10),
                    (body_left - 8, body_bottom + 10)
                ]
                pygame.draw.polygon(self.image, robe_color, robe_points)
                
                # 添加褶皱和流动效果
                for i in range(4):
                    y = body_top + i * 8
                    wave = math.sin(self.animation_frame * 0.1 + i * 0.5) * 2
                    pygame.draw.line(self.image, robe_highlight,
                                   (body_left - 6 + wave, y),
                                   (body_right + 6 + wave, y), 2)
            
        elif self.class_type == "弓箭手":
            # 轻甲和装备（性别差异）
            if self.gender == '女':
                # 女性弓箭手装备更轻便
                leather_color = (160, 82, 45)  # 更亮的棕色
                
                # 轻甲条带更细
                for i in range(4):
                    y = body_top + i * 8
                    pygame.draw.line(self.image, leather_color,
                                   (body_left, y),
                                   (body_right, y), 2)
                
                # 箭袋更小巧
                quiver_points = [
                    (body_right + 3, body_top),
                    (body_right + 6, body_top),
                    (body_right + 8, body_bottom - 5),
                    (body_right + 5, body_bottom - 5)
                ]
                pygame.draw.polygon(self.image, leather_color, quiver_points)
                
                # 箭矢
                arrow_color = (121, 85, 61)
                for i in range(3):
                    start_pos = (body_right + 5, body_top + 4 + i * 5)
                    end_pos = (body_right + 6, body_top + 12 + i * 5)
                    pygame.draw.line(self.image, arrow_color, start_pos, end_pos, 1)
                    # 箭头更小
                    pygame.draw.polygon(self.image, arrow_color, [
                        end_pos,
                        (end_pos[0] + 2, end_pos[1] - 1),
                        (end_pos[0] + 2, end_pos[1] + 1)
                    ])
            else:
                # 男性弓箭手装备更重
                leather_color = (139, 69, 19)
                
                # 轻甲条带
                for i in range(3):
                    y = body_top + i * 10
                    pygame.draw.line(self.image, leather_color,
                                   (body_left, y),
                                   (body_right, y), 3)
                
                # 箭袋
                quiver_points = [
                    (body_right + 4, body_top),
                    (body_right + 8, body_top),
                    (body_right + 10, body_bottom - 5),
                    (body_right + 6, body_bottom - 5)
                ]
                pygame.draw.polygon(self.image, leather_color, quiver_points)
                
                # 箭矢
                arrow_color = (101, 67, 33)
                for i in range(3):
                    start_pos = (body_right + 6, body_top + 5 + i * 6)
                    end_pos = (body_right + 8, body_top + 15 + i * 6)
                    pygame.draw.line(self.image, arrow_color, start_pos, end_pos, 2)
                    # 箭头
                    pygame.draw.polygon(self.image, arrow_color, [
                        end_pos,
                        (end_pos[0] + 3, end_pos[1] - 2),
                        (end_pos[0] + 3, end_pos[1] + 2)
                    ])

        # 如果角色朝左，翻转图像
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

        # 添加简单的阴影
        shadow_height = 4
        shadow_surface = pygame.Surface((30, shadow_height), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, 100)
        pygame.draw.ellipse(shadow_surface, shadow_color,
                          (0, 0, 30, shadow_height))
        self.image.blit(shadow_surface,
                       (center_x - 15, self.rect.height - shadow_height))

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