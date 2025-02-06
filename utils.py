import os
import pygame
import glob

def get_font(size):
    """获取指定大小的字体"""
    try:
        return pygame.font.Font(os.path.join("assets", "fonts", "1.ttf"), size)
    except Exception as e:
        print(f"加载字体失败: {e}")
        # 如果加载失败，使用系统字体
        return pygame.font.SysFont("microsoftyaheui", size)

def get_documents_path():
    """获取当前用户的文档文件夹路径"""
    if os.name == 'nt':  # Windows
        import ctypes.wintypes
        CSIDL_PERSONAL = 5  # My Documents
        SHGFP_TYPE_CURRENT = 0  # Get current, not default value
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
        return buf.value
    else:  # Linux/Mac
        return os.path.expanduser('~/Documents')

def ensure_game_directories():
    """确保游戏所需的目录存在"""
    docs_path = get_documents_path()
    base_path = os.path.join(docs_path, 'My Games', 'TrFk')
    player_path = os.path.join(base_path, 'Players')
    world_path = os.path.join(base_path, 'Worlds')
    
    # 创建所需的目录
    os.makedirs(player_path, exist_ok=True)
    os.makedirs(world_path, exist_ok=True)
    
    return player_path, world_path 