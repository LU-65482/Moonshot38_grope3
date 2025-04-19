import numpy as np
import sounddevice as sd
import webrtcvad
from scipy.io.wavfile import write
import collections, sys, time, uuid

# 常量配置
SAMPLE_RATE = 16000              # 支持的采样率：8000, 16000, 32000, 48000
FRAME_DURATION_MS = 30           # 帧长（ms），只能是 10, 20, 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 样本数
BYTES_PER_FRAME = FRAME_SIZE * 2  # 16 位 PCM，每个样本 2 字节

vad = webrtcvad.Vad(2)  # 攻击性模式 0~3

def speech_captured(filename): ...

def write_file(filename, recording):
    wav_data = b"".join(recording)
    write(filename, SAMPLE_RATE, 
          # 将 bytes 转回 numpy 数组（示意）
          memoryview(wav_data).cast('h'))  
    return filename

def work():
    recording = []
    silent_count = 0
    threshold_frames=5
    silence_frames=10
    buffer = collections.deque(maxlen=threshold_frames)
    in_speech = False
    def callback(indata, frames, time_info, status):
        nonlocal in_speech, silent_count
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

        if in_speech :
            recording.append(audio_bytes)
            if not is_speech:
                silent_count += 1
            else:
                silent_count = 0
            if silent_count > silence_frames:
                print("检测到静默，结束录音。")
                in_speech = False
                tmp_file = "/tmp/" + str(uuid.uuid4())
                write_file(tmp_file, recording)
                speech_captured(tmp_file)
    # 启动流
    with sd.InputStream(channels=1,
                        samplerate=SAMPLE_RATE,
                        blocksize=FRAME_SIZE,
                        dtype='float32',
                        callback=callback):
        ...