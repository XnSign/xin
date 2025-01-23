import pygame
import numpy as np
import random

class World:
    def __init__(self, width, height, tile_size):
        self.tile_size = tile_size
        self.world_width = width
        self.world_height = height
        
        # 计算网格大小
        self.grid_width = width // tile_size
        self.grid_height = height // tile_size
        
        # 初始化地形
        self.EMPTY = 0
        self.GROUND = 1
        self.PLATFORM = 2
        
        # 颜色映射
        self.colors = {
            self.EMPTY: (135, 206, 235),  # 天空蓝
            self.GROUND: (139, 69, 19),   # 深棕色
            self.PLATFORM: (169, 169, 169) # 灰色
        }
        
        # 创建地形网格
        self.grid = self.generate_terrain()
        
    def generate_terrain(self):
        """生成基本地形"""
        # 创建空网格
        grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
        
        # 生成基本地面
        ground_height = self.grid_height - 10  # 基本地面高度
        grid[ground_height:] = self.GROUND
        
        # 添加一些随机的地形变化
        for x in range(self.grid_width):
            # 随机调整地面高度
            if random.random() < 0.3:  # 30%的概率改变高度
                height_change = random.choice([-1, 1])
                ground_height = max(self.grid_height - 15, 
                                  min(self.grid_height - 5, 
                                      ground_height + height_change))
                
            # 设置地面
            grid[ground_height:, x] = self.GROUND
            
            # 随机添加平台
            if random.random() < 0.1:  # 10%的概率生成平台
                platform_height = random.randint(ground_height - 8, ground_height - 4)
                platform_width = random.randint(3, 6)
                for px in range(x, min(x + platform_width, self.grid_width)):
                    grid[platform_height, px] = self.PLATFORM
                    
        return grid
        
    def draw(self, surface, camera_x, camera_y):
        """绘制可见的地形"""
        # 计算可见区域的网格范围
        start_x = max(0, camera_x // self.tile_size)
        end_x = min(self.grid_width, (camera_x + surface.get_width()) // self.tile_size + 1)
        start_y = max(0, camera_y // self.tile_size)
        end_y = min(self.grid_height, (camera_y + surface.get_height()) // self.tile_size + 1)
        
        # 绘制可见的方块
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if self.grid[y][x] != self.EMPTY:
                    rect = pygame.Rect(
                        x * self.tile_size - camera_x,
                        y * self.tile_size - camera_y,
                        self.tile_size,
                        self.tile_size
                    )
                    
                    # 根据方块类型选择颜色
                    color = self.colors[self.grid[y][x]]
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, (0, 0, 0), rect, 1)  # 黑色边框
                    
    def get_world_size(self):
        """返回世界的像素尺寸"""
        return self.world_width, self.world_height
        
    def check_collision(self, entity):
        """检查实体与地形的碰撞"""
        # 计算实体所在的网格范围
        grid_x = entity.rect.x // self.tile_size
        grid_y = entity.rect.y // self.tile_size
        grid_right = (entity.rect.right - 1) // self.tile_size
        grid_bottom = (entity.rect.bottom - 1) // self.tile_size
        
        # 确保网格坐标在有效范围内
        if (grid_x < 0 or grid_right >= self.grid_width or
            grid_y < 0 or grid_bottom >= self.grid_height):
            return False
            
        # 检查实体占据的所有网格是否有碰撞
        for y in range(grid_y, grid_bottom + 1):
            for x in range(grid_x, grid_right + 1):
                if self.grid[y][x] != self.EMPTY:
                    return True
                    
        return False 