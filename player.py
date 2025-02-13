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
        self.rect = pygame.Rect(x, y - 96, 48, 96)  # 修改初始位置，向上偏移一个角色高度
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
        self.jump_hold_time = 0  # 跳跃按住时间
        self.max_jump_hold_time = 15  # 最大跳跃蓄力时间
        self.initial_jump_power = -9.6  # 初始跳跃力度（2.2格高度 = 70像素）
        self.max_jump_power = -11.4  # 最大跳跃力度（3.1格高度 = 99像素）
        
        # 动画相关
        self.animation_timer = pygame.time.get_ticks()
        self.animation_speed = 100  # 每帧动画持续100毫秒
        self.animation_frame = 0
        self.state = "idle"
        self.last_state = "idle"
        self.last_facing = True
        self.preview_mode = False
        
        # 创建玩家图像
        self.image = pygame.Surface((64, 96), pygame.SRCALPHA)
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
            print("无法加载配置，使用空白贴图")
            return surface
        
        # 返回空白的透明surface，不再绘制肉色方块
        return surface

    def create_default_hair(self):
        """创建默认发型"""
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 不绘制任何默认发型，返回空的透明surface
        return surface
    
    def update_appearance(self):
        """更新角色外观"""
        # 创建新的surface
        self.image = pygame.Surface((64, 96), pygame.SRCALPHA)
        
        # 获取角色配置
        try:
            with open(os.path.join(os.path.dirname(__file__), 'assets', 'characters', 'character_base.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
                body_config = config['body_parts']['male' if self.gender == '男' else 'female']
        except Exception as e:
            print(f"加载角色配置失败: {e}")
            return
        
        # 按顺序绘制身体部件（先绘制身体，再绘制其他部件）
        draw_order = ['body', 'feet', 'legs', 'arms', 'head']  # 修改绘制顺序
        
        for part in draw_order:
            if part in self.body_parts:
                part_config = body_config[part]
                x = 32 + part_config['offset_x']  # 32是图像中心点
                
                # 如果朝左，镜像x偏移
                if not self.facing_right:
                    x = 64 - x
                
                y = part_config['offset_y']
                
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
        # 绘制头发
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
        
        # 处理跳跃蓄力
        if self.is_jumping and self.jump_pressed and self.jump_hold_time < self.max_jump_hold_time:
            self.jump_hold_time += 1
            # 根据按住时间线性增加向上的速度
            jump_boost = (self.max_jump_power - self.initial_jump_power) * (self.jump_hold_time / self.max_jump_hold_time)
            self.dy = self.initial_jump_power + jump_boost  # 根据按住时间增加跳跃高度
        
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
        collision_with_ground = False  # 添加一个标志来确保检测到地面碰撞
        
        # 检查是否站在地面上（即使没有垂直移动）
        check_ground_rect = self.rect.copy()
        check_ground_rect.y += 1  # 向下检测一个像素
        ground_grid_bottom = (check_ground_rect.bottom - 1) // world.grid_size
        
        for x in range(grid_left, grid_right + 1):
            if x < 0 or x >= world.width:
                continue
            # 检查当前位置下方是否有地面
            if ground_grid_bottom < world.height and world.grid[ground_grid_bottom][x] != world.EMPTY:
                self.on_ground = True
                if not self.is_jumping:  # 如果不在跳跃状态，重置所有跳跃相关状态
                    self.jump_pressed = False
                    self.jump_hold_time = 0
                break
        
        # 处理垂直移动的碰撞
        for x in range(grid_left, grid_right + 1):
            if x < 0 or x >= world.width:
                continue
            if self.dy > 0:  # 下落
                if grid_bottom < world.height and world.grid[grid_bottom][x] != world.EMPTY:
                    new_rect.bottom = grid_bottom * world.grid_size
                    self.dy = 0
                    self.on_ground = True
                    collision_with_ground = True
                    break
            elif self.dy < 0:  # 上升
                # 检查是否超出世界上边界
                if grid_top < 0:
                    new_rect.top = 0
                    self.dy = 0
                    break
                # 检查方块碰撞
                if grid_top >= 0 and world.grid[grid_top][x] != world.EMPTY:
                    new_rect.top = (grid_top + 1) * world.grid_size
                    self.dy = 0
                    break
        
        # 如果检测到地面碰撞，立即重置所有跳跃相关状态
        if collision_with_ground:
            self.is_jumping = False
            self.jump_pressed = False
            self.jump_hold_time = 0
        
        self.rect.y = new_rect.y
        
        # 防止掉出地图底部
        if self.rect.bottom > world.height * world.grid_size:
            self.rect.bottom = world.height * world.grid_size
            self.dy = 0
            self.on_ground = True
            self.is_jumping = False
            self.jump_pressed = False
            self.jump_hold_time = 0
        
        # 如果玩家在空中且向上速度为0，说明达到最高点，开始下落
        if not self.on_ground and self.dy == 0:
            self.is_jumping = False
            self.jump_pressed = False
        
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
        if self.on_ground and not self.is_jumping:  # 只有在地面上且没有在跳跃状态时才能跳跃
            self.is_jumping = True
            self.jump_hold_time = 0
            self.on_ground = False
            self.state = "jump"
            self.jump_pressed = True  # 确保跳跃键状态正确
            self.dy = self.initial_jump_power  # 设置初始跳跃速度（2.2格高度）
    
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