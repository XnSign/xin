import os
import json
import datetime

class SaveManager:
    def __init__(self, save_dir="saves"):
        self.save_dir = save_dir
        # 确保存档目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
    def save_game(self, game_data, slot_name=None):
        # 如果没有指定存档名，使用当前时间
        if slot_name is None:
            slot_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # 准备存档数据
        save_data = {
            "player": {
                "x": game_data["player"].rect.x,
                "y": game_data["player"].rect.y
            },
            "inventory": {
                "slots": [
                    {"item": slot.item} if slot.item else {"item": None}
                    for slot in game_data["inventory"].slots
                ],
                "selected_slot": game_data["inventory"].selected_slot
            },
            "camera": {
                "x": game_data["camera_x"],
                "y": game_data["camera_y"]
            },
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存到文件
        file_path = os.path.join(self.save_dir, f"{slot_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
            
        return slot_name
    
    def load_game(self, slot_name, game_data):
        file_path = os.path.join(self.save_dir, f"{slot_name}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
                
            # 恢复玩家位置
            game_data["player"].rect.x = save_data["player"]["x"]
            game_data["player"].rect.y = save_data["player"]["y"]
            game_data["player"].true_x = float(save_data["player"]["x"])
            game_data["player"].true_y = float(save_data["player"]["y"])
            
            # 恢复背包
            for i, slot_data in enumerate(save_data["inventory"]["slots"]):
                game_data["inventory"].slots[i].item = slot_data["item"]
            game_data["inventory"].selected_slot = save_data["inventory"]["selected_slot"]
            
            # 恢复摄像机位置
            game_data["camera_x"] = save_data["camera"]["x"]
            game_data["camera_y"] = save_data["camera"]["y"]
            
            return True
        except Exception as e:
            print(f"加载存档失败: {e}")
            return False
            
    def get_save_slots(self):
        """获取所有存档"""
        save_slots = []
        for file_name in os.listdir(self.save_dir):
            if file_name.endswith(".json"):
                slot_name = file_name[:-5]  # 移除.json后缀
                try:
                    with open(os.path.join(self.save_dir, file_name), "r", encoding="utf-8") as f:
                        save_data = json.load(f)
                        save_slots.append({
                            "name": slot_name,
                            "timestamp": save_data["timestamp"]
                        })
                except:
                    continue
        return sorted(save_slots, key=lambda x: x["name"], reverse=True)
    
    def delete_save(self, slot_name):
        """删除指定存档"""
        file_path = os.path.join(self.save_dir, f"{slot_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False 