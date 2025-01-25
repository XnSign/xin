import numpy as np
from scipy.io import wavfile

def generate_hover_sound():
    # 设置音频参数
    sample_rate = 44100  # 采样率
    duration = 0.08     # 持续时间（秒）
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 生成悬停音效（使用更高的频率和更柔和的衰减）
    frequency = 2000    # 更高的基础频率
    decay = 40         # 较柔和的衰减速率
    
    # 创建基础波形
    wave = np.sin(2 * np.pi * frequency * t)
    
    # 添加柔和的衰减
    envelope = np.exp(-decay * t)
    wave = wave * envelope
    
    # 添加一点点混响效果
    reverb = np.roll(wave * 0.3, int(0.01 * sample_rate))
    wave = wave + reverb
    
    # 标准化并转换为16位整数
    wave = wave / np.max(np.abs(wave))  # 确保不会溢出
    wave = wave * 32767 * 0.7  # 稍微降低音量
    wave = wave.astype(np.int16)
    
    # 保存为WAV文件
    wavfile.write('assets/sounds/ui/hover.wav', sample_rate, wave)

if __name__ == "__main__":
    generate_hover_sound() 