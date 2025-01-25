import numpy as np
from scipy.io import wavfile

def generate_click_sound():
    # 设置音频参数
    sample_rate = 44100  # 采样率
    duration = 0.1      # 持续时间（秒）
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 生成点击音效（使用正弦波和指数衰减）
    frequency = 1000    # 基础频率
    decay = 50         # 衰减速率
    
    # 创建基础波形
    wave = np.sin(2 * np.pi * frequency * t)
    
    # 添加衰减
    envelope = np.exp(-decay * t)
    wave = wave * envelope
    
    # 标准化并转换为16位整数
    wave = wave * 32767
    wave = wave.astype(np.int16)
    
    # 保存为WAV文件
    wavfile.write('assets/sounds/ui/click.wav', sample_rate, wave)

if __name__ == "__main__":
    generate_click_sound() 