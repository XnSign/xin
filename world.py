import pygame
import random
import numpy as np

class World:
    def __init__(self, screen_width, screen_height, tile_size):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        
        # 定义世界大小（10000个方块宽）
        self.world_width = 10000 * tile_size
        self.world_height = screen_height
        
        # 定义方块类型
        self.EMPTY = 0
        self.DIRT = 1
        self.GRASS = 2
        self.STONE = 3
        self.BARRIER = 4  # 边界墙
        
        # 颜色映射
        self.colors = {
            self.EMPTY: (135, 206, 235),  # 天空蓝
            self.DIRT: (139, 69, 19),     # 泥土棕
            self.GRASS: (34, 139, 34),    # 草地绿
            self.STONE: (128, 128, 128),  # 石头灰
            self.BARRIER: (64, 64, 64)    # 边界墙深灰
        }
        
        # 创建世界网格
        self.grid = self.generate_terrain()
        
    def generate_terrain(self):
        # 创建空的世界网格
        cols = self.world_width // self.tile_size
        rows = self.world_height // self.tile_size
        grid = np.zeros((rows, cols), dtype=int)
        
        # 生成地形高度
        surface_height = [rows // 2 for _ in range(cols)]
        
        # 使用柏林噪声或更复杂的算法生成地形
        for i in range(2, cols - 2):
            surface_height[i] = (surface_height[i-2] + surface_height[i-1] + 
                               surface_height[i] + surface_height[i+1] + 
                               surface_height[i+2]) // 5
            # 添加随机变化，使地形更有趣
            surface_height[i] += random.randint(-2, 2)
            # 确保地形不会太高或太低
            surface_height[i] = max(rows // 3, min(2 * rows // 3, surface_height[i]))
        
        # 填充地形
        for x in range(cols):
            height = surface_height[x]
            # 放置草块
            grid[height][x] = self.GRASS
            # 放置泥土
            for y in range(height + 1, height + 4):
                if y < rows:
                    grid[y][x] = self.DIRT
            # 放置石头
            for y in range(height + 4, rows):
                if y < rows:
                    grid[y][x] = self.STONE
                    
        # 添加边界墙
        grid[:, 0] = self.BARRIER  # 左边界
        grid[:, -1] = self.BARRIER  # 右边界
                    
        return grid
    
    def draw(self, screen, camera_x, camera_y):
        # 计算可见区域的网格坐标
        start_col = max(0, camera_x // self.tile_size)
        end_col = min(len(self.grid[0]), (camera_x + self.screen_width) // self.tile_size + 1)
        start_row = max(0, camera_y // self.tile_size)
        end_row = min(len(self.grid), (camera_y + self.screen_height) // self.tile_size + 1)
        
        # 只绘制可见区域的方块
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if self.grid[y][x] != self.EMPTY:
                    pygame.draw.rect(screen, 
                                   self.colors[self.grid[y][x]],
                                   (x * self.tile_size - camera_x, 
                                    y * self.tile_size - camera_y,
                                    self.tile_size, 
                                    self.tile_size))
    
    def is_solid(self, x, y):
        grid_x = x // self.tile_size
        grid_y = y // self.tile_size
        if 0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid):
            return self.grid[grid_y][grid_x] != self.EMPTY
        return True  # 地图外的区域视为实心
        
    def get_world_size(self):
        return self.world_width, self.world_height 