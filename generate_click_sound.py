import wave
import struct
import math

def generate_click_sound(filename, duration=0.1, frequency=1000.0, volume=0.5):
    # 音频参数
    sample_rate = 44100  # 采样率
    num_samples = int(duration * sample_rate)
    
    # 生成音频数据
    audio_data = []
    decay = 10.0  # 衰减因子
    
    for i in range(num_samples):
        t = float(i) / sample_rate
        # 使用正弦波生成基本音调，并添加指数衰减
        decay_factor = math.exp(-decay * t)
        sample = volume * math.sin(2.0 * math.pi * frequency * t) * decay_factor
        # 将浮点数转换为16位整数
        audio_data.append(int(sample * 32767))
    
    # 创建WAV文件
    with wave.open(filename, 'w') as wav_file:
        # 设置参数
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 2字节采样
        wav_file.setframerate(sample_rate)
        
        # 写入音频数据
        for sample in audio_data:
            wav_file.writeframes(struct.pack('h', sample))

if __name__ == "__main__":
    generate_click_sound("assets/sounds/click.wav") 