import pygame
import os

# 初始化pygame
pygame.init()

def create_directory(path):
    """创建目录（如果不存在）"""
    if not os.path.exists(path):
        os.makedirs(path)

def generate_weapon_icons():
    """生成武器图标"""
    weapons_dir = "assets/equipment/weapons"
    create_directory(weapons_dir)
    
    # 铁剑
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(surface, (139, 69, 19), (14, 20, 4, 10))  # 剑柄
    pygame.draw.rect(surface, (192, 192, 192), (14, 2, 4, 18))  # 剑身
    pygame.draw.rect(surface, (139, 69, 19), (10, 18, 12, 4))  # 剑格
    pygame.image.save(surface, os.path.join(weapons_dir, "iron_sword.png"))
    
    # 法杖
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(surface, (139, 69, 19), (14, 8, 4, 22))  # 杖身
    pygame.draw.circle(surface, (0, 191, 255), (16, 6), 4)  # 法杖顶端
    pygame.image.save(surface, os.path.join(weapons_dir, "magic_staff.png"))
    
    # 猎弓
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.arc(surface, (139, 69, 19), (8, 4, 16, 24), -0.5, 0.5, 2)  # 弓身
    pygame.draw.line(surface, (139, 69, 19), (8, 16), (24, 16), 2)  # 弓弦
    pygame.image.save(surface, os.path.join(weapons_dir, "hunting_bow.png"))

def generate_armor_icons():
    """生成防具图标"""
    armor_dir = "assets/equipment/armor"
    create_directory(armor_dir)
    
    # 铁盔
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (192, 192, 192), (8, 8, 16, 16))  # 头盔主体
    pygame.draw.rect(surface, (192, 192, 192), (6, 16, 20, 8))  # 头盔下部
    pygame.image.save(surface, os.path.join(armor_dir, "iron_helmet.png"))
    
    # 铁甲
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.polygon(surface, (192, 192, 192), [
        (10, 4), (22, 4),  # 肩部
        (24, 16), (20, 28),  # 右侧
        (12, 28), (8, 16)   # 左侧
    ])
    pygame.image.save(surface, os.path.join(armor_dir, "iron_armor.png"))
    
    # 铁靴
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(surface, (192, 192, 192), (8, 12, 16, 8))  # 靴筒
    pygame.draw.rect(surface, (192, 192, 192), (6, 18, 20, 4))  # 靴底
    pygame.image.save(surface, os.path.join(armor_dir, "iron_boots.png"))
    
    # 法师帽
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.polygon(surface, (0, 0, 139), [
        (16, 2),  # 帽尖
        (24, 20), # 右边
        (8, 20)   # 左边
    ])
    pygame.draw.ellipse(surface, (0, 0, 139), (6, 18, 20, 6))  # 帽檐
    pygame.image.save(surface, os.path.join(armor_dir, "wizard_hat.png"))
    
    # 法袍
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.polygon(surface, (0, 0, 139), [
        (10, 4), (22, 4),  # 肩部
        (26, 28), (6, 28)  # 下摆
    ])
    pygame.image.save(surface, os.path.join(armor_dir, "wizard_robe.png"))
    
    # 皮帽
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (139, 69, 19), (8, 8, 16, 16))  # 帽子主体
    pygame.image.save(surface, os.path.join(armor_dir, "leather_cap.png"))
    
    # 皮甲
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.polygon(surface, (139, 69, 19), [
        (10, 4), (22, 4),  # 肩部
        (24, 16), (20, 28),  # 右侧
        (12, 28), (8, 16)   # 左侧
    ])
    pygame.image.save(surface, os.path.join(armor_dir, "leather_armor.png"))

def generate_slot_icons():
    """生成装备槽位图标"""
    slots_dir = "assets/equipment"
    create_directory(slots_dir)
    
    # 头盔槽位
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (150, 150, 150, 100), (2, 2, 12, 12))
    pygame.image.save(surface, os.path.join(slots_dir, "头盔_icon.png"))
    
    # 胸甲槽位
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.polygon(surface, (150, 150, 150, 100), [
        (4, 2), (12, 2),
        (14, 8), (12, 14),
        (4, 14), (2, 8)
    ])
    pygame.image.save(surface, os.path.join(slots_dir, "胸甲_icon.png"))
    
    # 护腿槽位
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.rect(surface, (150, 150, 150, 100), (4, 2, 8, 12))
    pygame.image.save(surface, os.path.join(slots_dir, "护腿_icon.png"))
    
    # 靴子槽位
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.rect(surface, (150, 150, 150, 100), (2, 6, 12, 8))
    pygame.image.save(surface, os.path.join(slots_dir, "靴子_icon.png"))
    
    # 武器槽位
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.line(surface, (150, 150, 150, 100), (8, 2), (8, 14), 2)
    pygame.draw.rect(surface, (150, 150, 150, 100), (6, 10, 4, 4))
    pygame.image.save(surface, os.path.join(slots_dir, "武器_icon.png"))
    
    # 盾牌槽位
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.polygon(surface, (150, 150, 150, 100), [
        (8, 2),
        (14, 4), (14, 12),
        (8, 14),
        (2, 12), (2, 4)
    ])
    pygame.image.save(surface, os.path.join(slots_dir, "盾牌_icon.png"))

if __name__ == "__main__":
    generate_weapon_icons()
    generate_armor_icons()
    generate_slot_icons()
    print("所有装备图标生成完成！") 