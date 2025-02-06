import pygame
import numpy as np
import random

class World:
    # 方块类型常量
    EMPTY = 0
    GROUND = 1
    PLATFORM = 2
    
    def __init__(self, width, height, grid_size):
        """初始化世界"""
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.grid = [[self.EMPTY for _ in range(width)] for _ in range(height)]
        
        # 定义方块颜色
        self.block_colors = {
            self.EMPTY: None,  # 空气方块不需要颜色
            self.GROUND: (139, 69, 19),  # 泥土方块的颜色
            self.PLATFORM: (128, 128, 128)  # 石头方块的颜色
        }
    
    def draw(self, surface, camera_x, camera_y):
        """绘制世界"""
        # 计算可见区域的网格范围
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        start_x = max(0, int(camera_x // self.grid_size))
        end_x = min(self.width, int((camera_x + screen_width) // self.grid_size) + 1)
        start_y = max(0, int(camera_y // self.grid_size))
        end_y = min(self.height, int((camera_y + screen_height) // self.grid_size) + 1)
        
        # 只绘制可见区域的方块
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                block_type = self.grid[y][x]
                if block_type != self.EMPTY:  # 不绘制空气方块
                    rect = pygame.Rect(
                        x * self.grid_size - camera_x,
                        y * self.grid_size - camera_y,
                        self.grid_size,
                        self.grid_size
                    )
                    pygame.draw.rect(surface, self.block_colors[block_type], rect)
                    if block_type != self.EMPTY:  # 只给非空方块添加边框
                        pygame.draw.rect(surface, (0, 0, 0), rect, 2)  # 2像素宽的黑色边框
    
    def get_block(self, x, y):
        """获取指定位置的方块类型"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return self.EMPTY
    
    def set_block(self, x, y, block_type):
        """设置指定位置的方块类型"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = block_type
        
    def generate_terrain(self):
        """生成基本地形"""
        # 创建空网格
        grid = np.zeros((self.height, self.width), dtype=np.int32)
        
        # 生成基本地面
        ground_height = self.height - 10  # 基本地面高度
        grid[ground_height:] = self.GROUND
        
        # 添加一些随机的地形变化
        for x in range(self.width):
            # 随机调整地面高度
            if random.random() < 0.3:  # 30%的概率改变高度
                height_change = random.choice([-1, 1])
                ground_height = max(self.height - 15, 
                                  min(self.height - 5, 
                                      ground_height + height_change))
                
            # 设置地面
            grid[ground_height:, x] = self.GROUND
            
            # 随机添加平台
            if random.random() < 0.1:  # 10%的概率生成平台
                platform_height = random.randint(ground_height - 8, ground_height - 4)
                platform_width = random.randint(3, 6)
                for px in range(x, min(x + platform_width, self.width)):
                    grid[platform_height, px] = self.PLATFORM
                    
        return grid
        
    def get_world_size(self):
        """返回世界的像素尺寸"""
        return self.width * self.grid_size, self.height * self.grid_size
        
    def check_collision(self, entity):
        """检查实体与地形的碰撞"""
        # 计算实体所在的网格范围
        grid_x = entity.rect.x // self.grid_size
        grid_y = entity.rect.y // self.grid_size
        grid_right = (entity.rect.right - 1) // self.grid_size
        grid_bottom = (entity.rect.bottom - 1) // self.grid_size
        
        # 确保网格坐标在有效范围内
        if (grid_x < 0 or grid_right >= self.width or
            grid_y < 0 or grid_bottom >= self.height):
            return False
            
        # 检查实体占据的所有网格是否有碰撞
        for y in range(grid_y, grid_bottom + 1):
            for x in range(grid_x, grid_right + 1):
                if self.grid[y][x] != self.EMPTY:
                    return True
                    
        return False 

    def generate(self):
        """生成新的世界地形"""
        # 生成基础地形高度
        terrain_height = [self.height // 2] * self.width
        for i in range(1, self.width):
            terrain_height[i] = terrain_height[i-1] + random.randint(-1, 1)
            terrain_height[i] = max(self.height // 4, min(terrain_height[i], self.height * 3 // 4))
        
        # 填充地形
        for x in range(self.width):
            for y in range(self.height):
                if y > terrain_height[x]:
                    if y > terrain_height[x] + 3:  # 深层为石头
                        self.grid[y][x] = self.PLATFORM
                    else:  # 表层为泥土
                        self.grid[y][x] = self.GROUND

    def load_from_data(self, data):
        """从数据加载世界"""
        if 'grid' in data:
            self.grid = data['grid']
        if 'width' in data:
            self.width = data['width']
        if 'height' in data:
            self.height = data['height']
        if 'grid_size' in data:
            self.grid_size = data['grid_size']

    def save_to_data(self):
        """保存世界数据"""
        return {
            'width': self.width,
            'height': self.height,
            'grid_size': self.grid_size,
            'grid': self.grid
        } 