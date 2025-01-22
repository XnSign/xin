import pygame

class InventorySlot:
    def __init__(self, x, y, size=32):
        self.rect = pygame.Rect(x, y, size, size)
        self.item = None
        self.size = size
        self.is_hotbar = False
        
    def draw(self, screen, font, selected=False):
        # 绘制槽位背景
        color = (100, 100, 100) if selected else (70, 70, 70)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1)
        
        # 如果有物品，绘制物品
        if self.item:
            item_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, 
                                  self.size - 4, self.size - 4)
            pygame.draw.rect(screen, self.item['color'], item_rect)
            
            # 绘制物品名称
            if self.is_hotbar:  # 只在物品栏显示名称
                text = font.render(self.item['name'][:4], True, (255, 255, 255))
                screen.blit(text, (self.rect.x + 2, self.rect.y + self.size - 16))

class Inventory:
    def __init__(self, x, y, cols=10, rows=5, slot_size=32, spacing=2):
        self.cols = cols
        self.rows = rows
        self.slot_size = slot_size
        self.spacing = spacing
        self.visible = False
        self.selected_slot = 0  # 当前选中的物品栏槽位
        
        # 创建所有槽位
        self.slots = []
        total_width = cols * (slot_size + spacing) - spacing
        total_height = rows * (slot_size + spacing) - spacing
        
        # 创建背包槽位
        for row in range(rows):
            for col in range(cols):
                x_pos = x + col * (slot_size + spacing)
                y_pos = y + row * (slot_size + spacing)
                slot = InventorySlot(x_pos, y_pos, slot_size)
                if row == 0:  # 第一行是物品栏
                    slot.is_hotbar = True
                self.slots.append(slot)
                
        # 背包区域
        self.rect = pygame.Rect(x, y, total_width, total_height)
        
        # 测试物品（临时）
        test_items = [
            {'name': '石头', 'color': (128, 128, 128)},
            {'name': '泥土', 'color': (139, 69, 19)},
            {'name': '草地', 'color': (34, 139, 34)}
        ]
        for i, item in enumerate(test_items):
            if i < len(self.slots):
                self.slots[i].item = item
    
    def handle_click(self, pos):
        if not self.visible:
            return
            
        # 检查是否点击了任何槽位
        for i, slot in enumerate(self.slots):
            if slot.rect.collidepoint(pos):
                # 如果是物品栏，设置为当前选中
                if slot.is_hotbar:
                    self.selected_slot = i % self.cols
                return True
        return False
    
    def draw_hotbar(self, screen, font):
        # 只绘制第一行（物品栏）
        for i in range(self.cols):
            slot = self.slots[i]
            slot.draw(screen, font, i == self.selected_slot)
            
    def draw(self, screen, font):
        if not self.visible:
            return
            
        # 绘制半透明背景
        background = pygame.Surface((self.rect.width, self.rect.height))
        background.fill((50, 50, 50))
        background.set_alpha(200)
        screen.blit(background, self.rect)
        
        # 绘制所有槽位
        for i, slot in enumerate(self.slots):
            is_selected = i % self.cols == self.selected_slot and slot.is_hotbar
            slot.draw(screen, font, is_selected)
            
    def handle_key(self, event):
        # 数字键1-0选择物品栏
        if event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                self.selected_slot = event.key - pygame.K_1
            elif event.key == pygame.K_0:
                self.selected_slot = 9
                
    def get_selected_item(self):
        return self.slots[self.selected_slot].item 