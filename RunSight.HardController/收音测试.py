import subprocess

def record_audio(duration=5, filename="output.wav"):
    cmd = [
        "arecord",
        "-D", "hw:1,0",
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "2",  # 明确指定声道数
        "-d", str(duration),
        filename
    ]
    
    result = subprocess.run(cmd, 
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          text=True)
    
    if result.returncode == 0:
        print(f"录音成功保存至 {filename}")
    else:
        print(f"录音失败，错误信息：\n{result.stderr}")

# 测试录制
record_audio(5, "fixed_recording.wav")