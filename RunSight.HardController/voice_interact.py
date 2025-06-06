import numpy as np
import sounddevice as sd
import webrtcvad
from scipy.io.wavfile import write
import collections, sys, time, uuid
import threading

# 常量配置
SAMPLE_RATE = 16000              # 支持的采样率：8000, 16000, 32000, 48000
FRAME_DURATION_MS = 30           # 帧长（ms），只能是 10, 20, 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 样本数
BYTES_PER_FRAME = FRAME_SIZE * 2  # 16 位 PCM，每个样本 2 字节

vad = webrtcvad.Vad(3)  # 攻击性模式 0~3，值越大越严格

# 全局变量
input_paused = False
pause_lock = threading.Lock()

def speech_captured(filename): ...

def write_file(filename, recording):
    print(f"写入文件：{filename}")
    # 将字节数据合并
    wav_data = b"".join(recording)
    # 转换为 numpy 数组
    audio_array = np.frombuffer(wav_data, dtype=np.int16)
    # 写入 WAV 文件
    write(filename, SAMPLE_RATE, audio_array)
    return filename

def pause_input():
    """暂停音频输入"""
    global input_paused
    with pause_lock:
        input_paused = True
    print("[音频] 输入已暂停")

def resume_input():
    """恢复音频输入"""
    global input_paused
    with pause_lock:
        input_paused = False
    print("[音频] 输入已恢复")

def work():
    recording = []
    silent_count = 0
    threshold_frames=8  # 增加判断人声的帧数阈值
    silence_frames=20   # 增加判断静默的帧数阈值
    buffer = collections.deque(maxlen=threshold_frames)
    in_speech = False
    def callback(indata, frames, time_info, status):
        nonlocal in_speech, silent_count
        
        # 检查是否暂停处理
        with pause_lock:
            if input_paused:
                return
        
        # 将 float32 转为 int16 PCM，并打包成字节
        audio_int16 = (indata.flatten() * 32767).astype(np.int16)  # 单通道
        audio_bytes = audio_int16.tobytes()

        # 跳过长度不符的帧
        if len(audio_bytes) != BYTES_PER_FRAME:
            return

        try:
            is_speech = vad.is_speech(audio_bytes, SAMPLE_RATE)
        except webrtcvad.Error:
            # 非法帧，忽略
            return  
        buffer.append(is_speech)

        if not in_speech and sum(buffer) > (threshold_frames // 2):
            in_speech = True
            print("检测到人声，开始录音…")
            recording.clear()

        if in_speech:
            recording.append(audio_bytes)
            if not is_speech:
                silent_count += 1
            else:
                silent_count = 0
            if silent_count > silence_frames or len(recording) > 1000:
                print("检测到静默，结束录音。")
                in_speech = False
                if len(recording) <= 50:
                    print("录音太短，忽略")
                    return
                
                # 暂停音频处理
                pause_input()
                
                # 处理音频
                tmp_file = "/tmp/" + str(uuid.uuid4())
                write_file(tmp_file, recording)
                
                # 使用线程处理回调，避免阻塞
                def process_callback():
                    try:
                        speech_captured(tmp_file)
                    finally:
                        # 无论是否出错，都恢复音频
                        resume_input()
                
                threading.Thread(target=process_callback).start()
                
    # 启动流
    with sd.InputStream(channels=1,
                        samplerate=SAMPLE_RATE,
                        blocksize=FRAME_SIZE,
                        dtype='float32',
                        callback=callback) as stream:
        while True:
            time.sleep(0.1)  # 降低 CPU 使用率
