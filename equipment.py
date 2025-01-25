import pygame
import os
from utils import get_font

class Equipment:
    def __init__(self, name, equipment_type, stats, image_path=None):
        self.name = name
        self.equipment_type = equipment_type  # 头盔、胸甲、护腿、靴子、武器等
        self.stats = stats  # 装备属性，如 {"defense": 5, "attack": 2}
        self.image = None
        if image_path:
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (32, 32))  # 统一缩放到32x32
            except pygame.error:
                print(f"Warning: Could not load image {image_path}")
                # 创建默认图像
                self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.rect(self.image, (100, 100, 100), (0, 0, 32, 32))
                pygame.draw.rect(self.image, (150, 150, 150), (2, 2, 28, 28))
        else:
            self.image = pygame.Surface((32, 32))
            self.image.fill((100, 100, 100))

class EquipmentSlot:
    def __init__(self, slot_type, x, y):
        self.slot_type = slot_type
        self.x = x
        self.y = y
        self.equipment = None
        self.rect = pygame.Rect(x, y, 40, 40)
        # 创建默认的空槽位图像
        self.empty_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.empty_image, (100, 100, 100, 100), (0, 0, 40, 40), 2)
        
        # 加载槽位类型图标
        icon_path = os.path.join('assets', 'equipment', f'{slot_type}_icon.png')
        self.icon = None
        try:
            self.icon = pygame.image.load(icon_path).convert_alpha()
            self.icon = pygame.transform.scale(self.icon, (16, 16))
        except pygame.error:
            # 如果图标不存在，创建一个简单的标识
            self.icon = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.rect(self.icon, (150, 150, 150, 100), (0, 0, 16, 16))

    def draw(self, surface):
        # 绘制槽位背景
        surface.blit(self.empty_image, self.rect)
        
        # 绘制槽位图标（在右下角）
        surface.blit(self.icon, (self.x + 24, self.y + 24))
        
        # 如果有装备，绘制装备图像
        if self.equipment and self.equipment.image:
            # 在槽位中央绘制装备图像
            equipment_x = self.x + (40 - 32) // 2
            equipment_y = self.y + (40 - 32) // 2
            surface.blit(self.equipment.image, (equipment_x, equipment_y))

    def draw_tooltip(self, surface, mouse_pos):
        if self.equipment and self.rect.collidepoint(mouse_pos):
            # 创建工具提示背景
            padding = 5
            font = pygame.font.Font(None, 24)
            
            # 渲染装备名称
            name_surface = font.render(self.equipment.name, True, (255, 255, 255))
            
            # 渲染装备属性
            stat_lines = []
            for stat, value in self.equipment.stats.items():
                stat_text = f"{stat}: {value}"
                stat_surface = font.render(stat_text, True, (200, 200, 200))
                stat_lines.append(stat_surface)
            
            # 计算工具提示尺寸
            tooltip_width = max(name_surface.get_width(),
                              max(surface.get_width() for surface in stat_lines))
            tooltip_height = name_surface.get_height() + \
                           sum(surface.get_height() for surface in stat_lines) + \
                           padding * (len(stat_lines) + 1)
            
            # 创建工具提示表面
            tooltip = pygame.Surface((tooltip_width + padding * 2,
                                   tooltip_height + padding * 2),
                                  pygame.SRCALPHA)
            pygame.draw.rect(tooltip, (0, 0, 0, 200), tooltip.get_rect())
            
            # 绘制装备名称
            tooltip.blit(name_surface, (padding, padding))
            
            # 绘制装备属性
            y = padding + name_surface.get_height() + padding
            for stat_surface in stat_lines:
                tooltip.blit(stat_surface, (padding, y))
                y += stat_surface.get_height()
            
            # 在鼠标位置绘制工具提示
            tooltip_x = mouse_pos[0]
            tooltip_y = mouse_pos[1] - tooltip.get_height()
            if tooltip_y < 0:
                tooltip_y = mouse_pos[1] + 20
            surface.blit(tooltip, (tooltip_x, tooltip_y))

class EquipmentSystem:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visible = False
        self.slots = {
            "头盔": EquipmentSlot("头盔", x + 60, y + 10),
            "胸甲": EquipmentSlot("胸甲", x + 60, y + 60),
            "护腿": EquipmentSlot("护腿", x + 60, y + 110),
            "靴子": EquipmentSlot("靴子", x + 60, y + 160),
            "武器": EquipmentSlot("武器", x + 10, y + 60),
            "盾牌": EquipmentSlot("盾牌", x + 110, y + 60)
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
            slot.draw(surface)

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

    def get_equipped_items(self):
        """返回所有已装备的物品"""
        equipped_items = {}
        for slot_name, slot in self.slots.items():
            if slot.equipment:  # 使用equipment而不是item
                equipped_items[slot_name] = slot.equipment
        return equipped_items

def create_default_equipment():
    """创建默认装备"""
    equipment_list = []
    
    # 武器
    iron_sword = Equipment(
        name="铁剑",
        equipment_type="武器",
        stats={"攻击力": 5},
        image_path="assets/equipment/weapons/iron_sword.png"
    )
    equipment_list.append(iron_sword)
    
    magic_staff = Equipment(
        name="法杖",
        equipment_type="武器",
        stats={"魔法攻击": 8, "魔法值": 20},
        image_path="assets/equipment/weapons/magic_staff.png"
    )
    equipment_list.append(magic_staff)
    
    hunting_bow = Equipment(
        name="猎弓",
        equipment_type="武器",
        stats={"攻击力": 4, "命中": 3},
        image_path="assets/equipment/weapons/hunting_bow.png"
    )
    equipment_list.append(hunting_bow)
    
    # 防具
    iron_helmet = Equipment(
        name="铁盔",
        equipment_type="头盔",
        stats={"防御力": 3},
        image_path="assets/equipment/armor/iron_helmet.png"
    )
    equipment_list.append(iron_helmet)
    
    iron_armor = Equipment(
        name="铁甲",
        equipment_type="胸甲",
        stats={"防御力": 5},
        image_path="assets/equipment/armor/iron_armor.png"
    )
    equipment_list.append(iron_armor)
    
    iron_boots = Equipment(
        name="铁靴",
        equipment_type="靴子",
        stats={"防御力": 2, "移动速度": 1},
        image_path="assets/equipment/armor/iron_boots.png"
    )
    equipment_list.append(iron_boots)
    
    # 法师装备
    wizard_hat = Equipment(
        name="法师帽",
        equipment_type="头盔",
        stats={"魔法值": 15, "魔法防御": 2},
        image_path="assets/equipment/armor/wizard_hat.png"
    )
    equipment_list.append(wizard_hat)
    
    wizard_robe = Equipment(
        name="法袍",
        equipment_type="胸甲",
        stats={"魔法值": 25, "魔法防御": 3},
        image_path="assets/equipment/armor/wizard_robe.png"
    )
    equipment_list.append(wizard_robe)
    
    # 弓箭手装备
    leather_cap = Equipment(
        name="皮帽",
        equipment_type="头盔",
        stats={"防御力": 1, "敏捷": 2},
        image_path="assets/equipment/armor/leather_cap.png"
    )
    equipment_list.append(leather_cap)
    
    leather_armor = Equipment(
        name="皮甲",
        equipment_type="胸甲",
        stats={"防御力": 3, "敏捷": 3},
        image_path="assets/equipment/armor/leather_armor.png"
    )
    equipment_list.append(leather_armor)
    
    return equipment_list