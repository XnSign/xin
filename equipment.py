import pygame
from utils import get_font

class Equipment:
    def __init__(self, name, equipment_type, stats, image_path=None):
        self.name = name
        self.equipment_type = equipment_type  # 头盔、胸甲、护腿、靴子、武器等
        self.stats = stats  # 装备属性，如 {"defense": 5, "attack": 2}
        self.image = None
        if image_path:
            try:
                self.image = pygame.image.load(image_path)
            except:
                print(f"无法加载装备图片: {image_path}")
                self.image = pygame.Surface((32, 32))
                self.image.fill((100, 100, 100))
        else:
            self.image = pygame.Surface((32, 32))
            self.image.fill((100, 100, 100))

class EquipmentSlot:
    def __init__(self, x, y, slot_type, size=40):
        self.rect = pygame.Rect(x, y, size, size)
        self.slot_type = slot_type
        self.equipment = None
        self.size = size
        self.is_hovered = False

    def draw(self, surface, font):
        # 绘制槽位背景
        color = (70, 70, 70) if self.is_hovered else (50, 50, 50)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)

        # 如果有装备，绘制装备图标
        if self.equipment:
            if self.equipment.image:
                scaled_image = pygame.transform.scale(self.equipment.image, (self.size-8, self.size-8))
                surface.blit(scaled_image, (self.rect.x+4, self.rect.y+4))

            # 绘制装备名称提示
            if self.is_hovered:
                self.draw_tooltip(surface, font)

    def draw_tooltip(self, surface, font):
        if not self.equipment:
            return

        # 创建工具提示文本
        lines = [
            self.equipment.name,
            f"类型: {self.equipment.slot_type}"
        ]
        for stat, value in self.equipment.stats.items():
            lines.append(f"{stat}: {value}")

        # 计算工具提示框大小
        padding = 5
        line_height = 20
        tooltip_width = max(font.size(line)[0] for line in lines) + padding * 2
        tooltip_height = len(lines) * line_height + padding * 2

        # 创建工具提示框
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        pygame.draw.rect(tooltip_surface, (0, 0, 0, 200), tooltip_surface.get_rect())

        # 绘制文本
        for i, line in enumerate(lines):
            text = font.render(line, True, (255, 255, 255))
            tooltip_surface.blit(text, (padding, padding + i * line_height))

        # 计算工具提示位置
        x = self.rect.right + 5
        y = self.rect.y
        if x + tooltip_width > surface.get_width():
            x = self.rect.x - tooltip_width - 5
        if y + tooltip_height > surface.get_height():
            y = surface.get_height() - tooltip_height

        # 绘制工具提示
        surface.blit(tooltip_surface, (x, y))

class EquipmentSystem:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visible = False
        self.slots = {
            "头盔": EquipmentSlot(x + 60, y + 10, "头盔"),
            "胸甲": EquipmentSlot(x + 60, y + 60, "胸甲"),
            "护腿": EquipmentSlot(x + 60, y + 110, "护腿"),
            "靴子": EquipmentSlot(x + 60, y + 160, "靴子"),
            "武器": EquipmentSlot(x + 10, y + 60, "武器"),
            "盾牌": EquipmentSlot(x + 110, y + 60, "盾牌")
        }
        self.dragging = None
        self.drag_offset = (0, 0)

    def draw(self, surface):
        if not self.visible:
            return

        # 绘制装备栏背景
        panel_width = 160
        panel_height = 220
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 30, 220), (0, 0, panel_width, panel_height))
        pygame.draw.rect(panel, (100, 100, 100, 255), (0, 0, panel_width, panel_height), 2)
        surface.blit(panel, (self.x, self.y))

        # 绘制标题
        font = get_font(24)
        title = font.render("装备", True, (255, 255, 255))
        surface.blit(title, (self.x + (panel_width - title.get_width()) // 2, self.y + 5))

        # 绘制装备槽位
        for slot in self.slots.values():
            slot.draw(surface, get_font(16))

        # 绘制正在拖动的装备
        if self.dragging:
            mouse_pos = pygame.mouse.get_pos()
            x = mouse_pos[0] - self.drag_offset[0]
            y = mouse_pos[1] - self.drag_offset[1]
            if self.dragging.image:
                surface.blit(self.dragging.image, (x, y))

    def handle_event(self, event):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEMOTION:
            # 更新槽位悬停状态
            mouse_pos = event.pos
            for slot in self.slots.values():
                slot.is_hovered = slot.rect.collidepoint(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                mouse_pos = event.pos
                for slot in self.slots.values():
                    if slot.rect.collidepoint(mouse_pos):
                        if slot.equipment:
                            self.dragging = slot.equipment
                            self.drag_offset = (mouse_pos[0] - slot.rect.x, mouse_pos[1] - slot.rect.y)
                            slot.equipment = None
                            return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:  # 释放左键
                mouse_pos = event.pos
                for slot in self.slots.values():
                    if slot.rect.collidepoint(mouse_pos):
                        if self.dragging.equipment_type == slot.slot_type:
                            # 交换装备
                            old_equipment = slot.equipment
                            slot.equipment = self.dragging
                            self.dragging = old_equipment
                            return True
                
                # 如果没有放在有效的槽位上，找到原始类型的槽位放回
                for slot in self.slots.values():
                    if slot.slot_type == self.dragging.equipment_type and not slot.equipment:
                        slot.equipment = self.dragging
                        self.dragging = None
                        return True

                self.dragging = None
                return True

        return False

    def equip_item(self, equipment):
        """尝试装备一个物品"""
        if not isinstance(equipment, Equipment):
            return False

        target_slot = self.slots.get(equipment.equipment_type)
        if not target_slot:
            return False

        # 如果槽位已经有装备，返回旧装备
        old_equipment = target_slot.equipment
        target_slot.equipment = equipment
        return old_equipment

    def unequip_item(self, slot_type):
        """卸下指定槽位的装备"""
        if slot_type not in self.slots:
            return None

        equipment = self.slots[slot_type].equipment
        self.slots[slot_type].equipment = None
        return equipment

    def get_total_stats(self):
        """计算所有装备的总属性"""
        total_stats = {}
        for slot in self.slots.values():
            if slot.equipment:
                for stat, value in slot.equipment.stats.items():
                    if stat in total_stats:
                        total_stats[stat] += value
                    else:
                        total_stats[stat] = value
        return total_stats 