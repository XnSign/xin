import pygame
import math
import random
import os
import json
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
        self.class_type = data['class']
        self.skin_color = data['skin_color']
        self.health = data['health']
        self.mana = data['mana']
        
        # 加载贴图
        self.load_sprites()
        
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
        self.update_appearance()
        
        # 初始化装备系统
        self.equipment_system = EquipmentSystem(10, 50)  # 位置可以根据需要调整
    
    def load_sprites(self):
        """加载角色贴图"""
        try:
            # 获取贴图基础路径
            base_path = os.path.dirname(os.path.abspath(__file__))
            char_path = os.path.join(base_path, 'assets', 'characters')
            
            # 加载身体部件贴图
            gender_folder = 'male' if self.gender == '男' else 'female'
            parts_path = os.path.join(char_path, gender_folder, 'parts')
            
            self.body_parts = {}
            for part in ['head', 'body', 'arms', 'legs', 'feet']:
                part_path = os.path.join(parts_path, f"{part}.png")
                try:
                    self.body_parts[part] = pygame.image.load(part_path).convert_alpha()
                except:
                    print(f"无法加载贴图: {part_path}，使用默认图形")
                    self.body_parts[part] = self.create_default_part(part)
            
            # 加载发型贴图
            hair_path = os.path.join(char_path, 'hairstyles', f"{self.hairstyle}.png")
            try:
                self.hair_sprite = pygame.image.load(hair_path).convert_alpha()
            except:
                print(f"无法加载发型贴图: {hair_path}，使用默认发型")
                self.hair_sprite = self.create_default_hair()
            
            # 加载装备贴图（如果有）
            self.equipment_sprites = {}
            if hasattr(self, 'equipment_system'):
                equipped_items = self.equipment_system.get_equipped_items()
                for slot, item in equipped_items.items():
                    if item:
                        equip_path = os.path.join(char_path, 'equipment', f"{item.name}.png")
                        if os.path.exists(equip_path):
                            self.equipment_sprites[slot] = pygame.image.load(equip_path).convert_alpha()
        
        except Exception as e:
            print(f"加载角色贴图失败: {e}")
            # 创建所有默认贴图
            self.body_parts = {}
            for part in ['head', 'body', 'arms', 'legs', 'feet']:
                self.body_parts[part] = self.create_default_part(part)
            self.hair_sprite = self.create_default_hair()
            self.equipment_sprites = {}
    
    def create_default_part(self, part_name):
        """创建默认的身体部件图形"""
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        # 获取配置
        try:
            with open(os.path.join(os.path.dirname(__file__), 'assets', 'characters', 'character_base.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
                body_config = config['body_parts']['male' if self.gender == '男' else 'female']
                part_config = body_config[part_name]
        except:
            print("无法加载配置，使用硬编码的默认值")
            return surface
        
        # 根据部件类型绘制不同的形状
        color = self.skin_color if isinstance(self.skin_color, tuple) else (240, 200, 160)
        
        x = 32 + part_config['offset_x']
        y = part_config['offset_y']
        width = part_config['width']
        height = part_config['height']
        
        if part_name == 'head':
            pygame.draw.ellipse(surface, color, (x - width//2, y, width, height))
        elif part_name == 'body':
            pygame.draw.rect(surface, color, (x - width//2, y, width, height))
        elif part_name == 'arms':
            pygame.draw.rect(surface, color, (x - width//2, y, width, height))
        elif part_name == 'legs':
            leg_width = width // 2 - 2
            pygame.draw.rect(surface, color, (x - width//2, y, leg_width, height))  # 左腿
            pygame.draw.rect(surface, color, (x + 2, y, leg_width, height))  # 右腿
        elif part_name == 'feet':
            pygame.draw.rect(surface, color, (x - width//2, y, width, height))
        
        return surface

    def create_default_hair(self):
        """创建默认发型"""
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 不绘制任何默认发型，返回空的透明surface
        return surface
    
    def update_appearance(self):
        """更新角色外观"""
        # 创建新的surface
        self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        # 获取角色配置
        try:
            with open(os.path.join(os.path.dirname(__file__), 'assets', 'characters', 'character_base.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
                body_config = config['body_parts']['male' if self.gender == '男' else 'female']
        except Exception as e:
            print(f"加载角色配置失败: {e}")
            return
        
        # 获取动画偏移量
        leg_offset = math.sin(self.animation_frame * 0.2) * 4 if self.state == "walk" else 0
        arm_offset = -math.sin(self.animation_frame * 0.2) * 4 if self.state == "walk" else 0
        
        # 按顺序绘制身体部件
        for part in ['feet', 'legs', 'body', 'arms', 'head']:
            if part in self.body_parts:
                part_config = body_config[part]
                x = 32 + part_config['offset_x']  # 32是图像中心点
                
                # 如果朝左，镜像x偏移
                if not self.facing_right:
                    x = 64 - x
                
                y = part_config['offset_y']
                
                # 应用动画偏移
                if part == 'legs':
                    y += leg_offset
                elif part == 'arms':
                    y += arm_offset
                
                # 获取部件图像
                part_image = self.body_parts[part]
                if not self.facing_right:
                    part_image = pygame.transform.flip(part_image, True, False)
                
                self.image.blit(part_image, (x - part_image.get_width()//2, y))
        
        # 应用发色（通过调色板替换）
        colored_hair = self.hair_sprite.copy()
        colored_hair.fill(self.hair_color, special_flags=pygame.BLEND_RGBA_MULT)
        if not self.facing_right:
            colored_hair = pygame.transform.flip(colored_hair, True, False)
        self.image.blit(colored_hair, (0, 0))
        
        # 绘制装备
        for sprite in self.equipment_sprites.values():
            equip_sprite = sprite
            if not self.facing_right:
                equip_sprite = pygame.transform.flip(sprite, True, False)
            self.image.blit(equip_sprite, (0, 0))

    def draw_character(self):
        """绘制角色"""
        # 更新动画帧
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer > self.animation_speed:
            self.animation_frame += 1
            self.animation_timer = current_time
        
        # 更新外观
        self.update_appearance()

    def update(self, world):
        """更新玩家状态"""
        if self.preview_mode:
            return
        
        # 应用重力
        if not self.on_ground:
            self.dy += self.gravity
            # 限制最大下落速度
            if self.dy > self.max_fall_speed:
                self.dy = self.max_fall_speed
        
        # 更新位置
        new_rect = self.rect.copy()
        
        # 先处理水平移动
        if self.x_speed != 0:
            new_rect.x += self.x_speed
            # 水平碰撞检测
            grid_left = new_rect.left // world.grid_size
            grid_right = (new_rect.right - 1) // world.grid_size
            grid_top = new_rect.top // world.grid_size
            grid_bottom = (new_rect.bottom - 1) // world.grid_size
            
            # 检查水平移动是否会碰撞
            collision = False
            for y in range(grid_top, grid_bottom + 1):
                if y < 0 or y >= world.height:
                    continue
                if self.x_speed > 0:  # 向右移动
                    if grid_right < world.width and world.grid[y][grid_right] != world.EMPTY:
                        new_rect.right = grid_right * world.grid_size
                        collision = True
                        break
                elif self.x_speed < 0:  # 向左移动
                    if grid_left >= 0 and world.grid[y][grid_left] != world.EMPTY:
                        new_rect.left = (grid_left + 1) * world.grid_size
                        collision = True
                        break
            
            if not collision:
                self.rect.x = new_rect.x
        
        # 然后处理垂直移动
        new_rect = self.rect.copy()
        new_rect.y += self.dy
        
        # 垂直碰撞检测
        grid_left = new_rect.left // world.grid_size
        grid_right = (new_rect.right - 1) // world.grid_size
        grid_top = new_rect.top // world.grid_size
        grid_bottom = (new_rect.bottom - 1) // world.grid_size
        
        # 检查垂直移动是否会碰撞
        self.on_ground = False
        for x in range(grid_left, grid_right + 1):
            if x < 0 or x >= world.width:
                continue
            if self.dy > 0:  # 下落
                if grid_bottom < world.height and world.grid[grid_bottom][x] != world.EMPTY:
                    new_rect.bottom = grid_bottom * world.grid_size
                    self.dy = 0
                    self.on_ground = True
                    self.jumps_left = 2  # 着地时重置跳跃次数
                    break
            elif self.dy < 0:  # 上升
                if grid_top >= 0 and world.grid[grid_top][x] != world.EMPTY:
                    new_rect.top = (grid_top + 1) * world.grid_size
                    self.dy = 0
                    break
        
        self.rect.y = new_rect.y
        
        # 如果掉出地图，重置位置
        if self.rect.top > world.height * world.grid_size:
            self.rect.x = world.width * world.grid_size // 2
            self.rect.y = 0
            self.dy = 0
            self.x_speed = 0
        
        # 更新动画状态
        if self.x_speed != 0:
            self.state = "walk"
        elif not self.on_ground:
            self.state = "jump"
        else:
            self.state = "idle"
        
        # 如果状态改变或正在移动，重新绘制角色
        if (self.state != self.last_state or 
            self.facing_right != self.last_facing or 
            self.state in ["walk", "jump"]):
            self.draw_character()
            self.last_state = self.state
            self.last_facing = self.facing_right
    
    def move_left(self):
        """向左移动"""
        self.x_speed = -self.move_speed
        self.facing_right = False
        self.state = "walk"
        self.needs_redraw = True
    
    def move_right(self):
        """向右移动"""
        self.x_speed = self.move_speed
        self.facing_right = True
        self.state = "walk"
        self.needs_redraw = True
    
    def stop(self):
        """停止移动"""
        self.x_speed = 0
        # 保持当前朝向不变
        self.state = "idle"
        self.needs_redraw = True
    
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
        
        # 直接绘制玩家（朝向已经在update_appearance中处理）
        surface.blit(self.image, (screen_x, screen_y))
        
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