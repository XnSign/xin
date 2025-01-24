import wave
import struct
import math
import os

def generate_click_sound(filename, duration=0.1, frequency=1000.0, volume=0.5):
    """生成点击音效"""
    # 音频参数
    sample_rate = 44100  # 采样率
    num_samples = int(duration * sample_rate)
    
    # 创建音频数据
    audio_data = []
    for i in range(num_samples):
        t = float(i) / sample_rate  # 当前时间点
        # 使用正弦波并添加指数衰减
        decay = math.exp(-30.0 * t)  # 快速衰减
        value = volume * math.sin(2.0 * math.pi * frequency * t) * decay
        # 将浮点数转换为16位整数
        packed_value = struct.pack('h', int(32767.0 * value))
        audio_data.append(packed_value)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 写入WAV文件
    with wave.open(filename, 'w') as wav_file:
        # 设置参数
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 2字节采样
        wav_file.setframerate(sample_rate)
        # 写入音频数据
        wav_file.writeframes(b''.join(audio_data))

if __name__ == '__main__':
    # 生成点击音效
    generate_click_sound("assets/sounds/click.wav") 